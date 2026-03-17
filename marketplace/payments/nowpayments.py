"""NOWPayments API client and IPN signature verification."""

import hashlib
import hmac
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Maps our internal payment method codes to NOWPayments currency codes
CURRENCY_MAP = {
    "crypto_bitcoin": "btc",
    "crypto_ethereum": "eth",
    "crypto_usdc": "usdcerc20",
}


def _base_url():
    if getattr(settings, "NOWPAYMENTS_SANDBOX", False):
        return "https://api-sandbox.nowpayments.io/v1"
    return "https://api.nowpayments.io/v1"


def _headers():
    return {
        "x-api-key": settings.NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json",
    }


def get_pay_currency(payment_method):
    """Return the NOWPayments currency code for an internal payment method."""
    return CURRENCY_MAP.get(payment_method, "btc")


def create_payment(amount_usd, payment_method, order_id, ipn_callback_url):
    """
    Create a new payment via the NOWPayments API.

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
    pay_currency = get_pay_currency(payment_method)
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
