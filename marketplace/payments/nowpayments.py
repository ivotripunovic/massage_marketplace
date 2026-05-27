"""NOWPayments API client and IPN signature verification."""

import hashlib
import hmac
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Accepted payment currencies.
# Each entry defines: code (NOWPayments currency code), name (display),
# network (badge label), uri_scheme (wallet deep-link prefix for QR codes).
# To add a new coin: append an entry here — no other code needs to change.
SUPPORTED_CURRENCIES = [
    {
        "code": "usdtmatic",
        "name": "Tether USD (Polygon)",
        "network": "polygon",
        "uri_scheme": "ethereum",
        # EIP-681: USDT contract on Polygon PoS, 6 decimal places
        "erc20_contract": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "chain_id": 137,
        "token_decimals": 6,
    },
    {
        "code": "usdtbsc",
        "name": "Tether USD (BSC)",
        "network": "bsc",
        "uri_scheme": "ethereum",
        # EIP-681: BSC-pegged USDT contract, 18 decimal places
        "erc20_contract": "0x55d398326f99059fF775485246999027B3197955",
        "chain_id": 56,
        "token_decimals": 18,
    },
]

SUPPORTED_CURRENCY_CODES = {c["code"] for c in SUPPORTED_CURRENCIES}

# Used when the API is unavailable or the API key is not configured
FALLBACK_CURRENCIES = SUPPORTED_CURRENCIES


def _base_url():
    if getattr(settings, "NOWPAYMENTS_SANDBOX", False):
        return "https://api-sandbox.nowpayments.io/v1"
    return "https://api.nowpayments.io/v1"


def _headers():
    return {
        "x-api-key": settings.NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json",
    }


def get_currencies():
    """
    Return a list of available deposit currencies from NOWPayments.

    Result is cached for 1 hour. Falls back to FALLBACK_CURRENCIES if the API
    key is not configured or the request fails.

    Each entry is a dict: {"code": str, "name": str, "network": str}.
    """
    if not getattr(settings, "NOWPAYMENTS_API_KEY", ""):
        return FALLBACK_CURRENCIES

    from django.core.cache import cache

    CACHE_KEY = "nowpayments_currencies_v1"
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            f"{_base_url()}/full-currencies",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        currencies = []
        for c in data.get("currencies", []):
            code = c["code"].lower()
            if code not in SUPPORTED_CURRENCY_CODES:
                continue
            if not c.get("enable") or not c.get("isDepositEnabled", True):
                continue
            currencies.append({
                "code": code,
                "name": c.get("name", c["code"].upper()),
                "network": (c.get("network") or c["code"]).lower(),
            })
        if currencies:
            cache.set(CACHE_KEY, currencies, timeout=3600)
            return currencies
    except Exception:
        logger.warning("Could not fetch NOWPayments currencies, using fallback list")

    return FALLBACK_CURRENCIES


def create_payment(amount_usd, pay_currency, order_id, ipn_callback_url):
    """
    Create a new payment via the NOWPayments API.

    pay_currency is a NOWPayments currency code (e.g. "btc", "eth", "usdcerc20").

    Returns the full response dict on success:
        {
            "payment_id": "...",
            "pay_address": "...",
            "pay_amount": 0.00085,
            "pay_currency": "btc",
            "payment_status": "waiting",
            ...
        }

    Raises requests.HTTPError on API errors.
    """
    payload = {
        "price_amount": float(amount_usd),
        "price_currency": "usd",
        "pay_currency": pay_currency,
        "order_id": str(order_id),
        "order_description": f"Massage Marketplace subscription #{order_id}",
        "ipn_callback_url": ipn_callback_url,
    }
    if getattr(settings, "NOWPAYMENTS_SANDBOX", False):
        payload["case"] = "success"

    resp = requests.post(
        f"{_base_url()}/payment",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def verify_ipn_signature(payload_bytes, received_sig):
    """
    Verify an IPN webhook signature from NOWPayments.

    NOWPayments signs IPN payloads with HMAC-SHA512 over the JSON body
    serialised with keys sorted alphabetically.

    Returns True if the signature is valid, False otherwise.
    """
    secret = getattr(settings, "NOWPAYMENTS_IPN_SECRET", "")
    if not secret:
        logger.warning("NOWPAYMENTS_IPN_SECRET is not configured — rejecting IPN")
        return False

    try:
        data = json.loads(payload_bytes)
        sorted_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
        calculated = hmac.new(
            secret.strip().encode(),
            sorted_json.encode(),
            hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(calculated, received_sig)
    except Exception:
        logger.exception("Error verifying IPN signature")
        return False
