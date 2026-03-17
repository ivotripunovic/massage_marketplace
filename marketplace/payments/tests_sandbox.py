"""
Sandbox integration tests for NOWPayments.

These tests make real HTTP calls to the NOWPayments SANDBOX API and cover
the full payment flow end-to-end — without requiring a public webhook URL
or ngrok.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sandbox uses DIFFERENT credentials than production.

1. Register at: https://account-sandbox.nowpayments.io
2. Generate a sandbox API key and IPN secret there.
3. In your .env set:

    NOW_PAYMENTS_API_KEY=<your-SANDBOX-api-key>
    NOW_PAYMENTS_IPN=<your-SANDBOX-ipn-secret>
    NOWPAYMENTS_SANDBOX=true

Note: Production keys from account.nowpayments.io return 403 on the
sandbox API — they are different accounts.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RUN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    python marketplace/manage.py test payments.tests_sandbox \\
        --settings=marketplace.test_settings -v 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEP: ngrok (real end-to-end)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The tests above simulate the IPN locally using our own signing.
To test with a REAL IPN callback delivered by NOWPayments:

1. Install ngrok:  https://ngrok.com/download
2. Run dev server: python marketplace/manage.py runserver
3. Expose it:      ngrok http 8000
4. Copy the HTTPS URL (e.g. https://abc123.ngrok.io)
5. In NOWPayments sandbox dashboard:
       Store Settings → IPN Callback URL:
       https://abc123.ngrok.io/payments/webhook/nowpayments/
6. Go to http://localhost:8000, log in as a provider and subscribe.
   The IPN will arrive automatically and activate the subscription.
"""

import hashlib
import hmac
import json
import os
import time
import unittest

import requests as http_requests
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from payments.models import SubscriptionPayment
from providers.models import Provider
from users.models import User

# ---------------------------------------------------------------------------
# Skip guard
# ---------------------------------------------------------------------------
_API_KEY = os.getenv("NOW_PAYMENTS_API_KEY", "")
_IPN_SECRET = os.getenv("NOW_PAYMENTS_IPN", "")
_SANDBOX_MODE = os.getenv("NOWPAYMENTS_SANDBOX", "false").lower() in ("true", "1", "yes")

_SANDBOX_READY = _SANDBOX_MODE and bool(_API_KEY) and bool(_IPN_SECRET)

requires_sandbox = unittest.skipUnless(
    _SANDBOX_READY,
    (
        "Sandbox tests require: NOWPAYMENTS_SANDBOX=true, NOW_PAYMENTS_API_KEY and "
        "NOW_PAYMENTS_IPN — all set to SANDBOX credentials from "
        "https://account-sandbox.nowpayments.io (not the same as production keys)"
    ),
)

SANDBOX_BASE = "https://api-sandbox.nowpayments.io/v1"


def _api_headers():
    return {
        "x-api-key": _API_KEY,
        "Content-Type": "application/json",
    }


def _sign_payload(payload_bytes: bytes) -> str:
    """Sign payload exactly as NOWPayments does — HMAC-SHA512, sorted keys."""
    secret = _IPN_SECRET.strip()
    data = json.loads(payload_bytes)
    sorted_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        secret.encode(),
        sorted_json.encode(),
        hashlib.sha512,
    ).hexdigest()


# ---------------------------------------------------------------------------
# 1. IPN signature verification (no API calls, no sandbox required)
# ---------------------------------------------------------------------------

class IPNSignatureTests(TestCase):
    """
    Test our verify_ipn_signature() using real HMAC computation.
    These tests use the IPN secret from .env and do not require sandbox mode —
    they test our own code's signing/verification logic only.
    """

    def _make_payload(self, payment_id="pay-123", status="finished") -> bytes:
        return json.dumps(
            {
                "payment_id": payment_id,
                "payment_status": status,
                "pay_address": "1BTC",
                "price_amount": 29.99,
                "price_currency": "usd",
                "pay_amount": 0.00085,
                "actually_paid": 0.00085,
                "pay_currency": "btc",
                "order_id": "order-1",
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

    def test_valid_signature_accepted(self):
        """Payload signed with our IPN secret passes verification."""
        import payments.nowpayments as nowpayments

        payload = self._make_payload()
        sig = _sign_payload(payload)
        self.assertTrue(nowpayments.verify_ipn_signature(payload, sig))

    def test_wrong_signature_rejected(self):
        """A payload signed with a different secret fails verification."""
        import payments.nowpayments as nowpayments

        payload = self._make_payload()
        self.assertFalse(nowpayments.verify_ipn_signature(payload, "badsignature"))

    def test_tampered_payload_rejected(self):
        """Modifying the payload after signing invalidates the signature."""
        import payments.nowpayments as nowpayments

        payload = self._make_payload()
        sig = _sign_payload(payload)
        tampered = payload.replace(b'"finished"', b'"waiting"')
        self.assertFalse(nowpayments.verify_ipn_signature(tampered, sig))

    def test_key_order_doesnt_matter(self):
        """Verification succeeds regardless of JSON key order in the incoming payload."""
        import payments.nowpayments as nowpayments

        data = {
            "order_id": "order-1",
            "pay_currency": "btc",
            "payment_id": "pay-123",
            "payment_status": "finished",
            "price_amount": 29.99,
            "price_currency": "usd",
            "pay_amount": 0.00085,
            "actually_paid": 0.00085,
            "pay_address": "1BTC",
        }
        # Sign the sorted version
        sorted_payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        sig = _sign_payload(sorted_payload)
        # Verify against the unsorted version — our code sorts internally
        unsorted_payload = json.dumps(data, separators=(",", ":")).encode()
        self.assertTrue(nowpayments.verify_ipn_signature(unsorted_payload, sig))

    def test_empty_secret_rejects_all(self):
        """Missing IPN secret causes all IPN requests to be rejected."""
        import payments.nowpayments as nowpayments

        payload = self._make_payload()
        sig = _sign_payload(payload)
        with override_settings(NOWPAYMENTS_IPN_SECRET=""):
            self.assertFalse(nowpayments.verify_ipn_signature(payload, sig))


# ---------------------------------------------------------------------------
# 2. Sandbox API tests (require real sandbox credentials)
# ---------------------------------------------------------------------------

@requires_sandbox
class SandboxAPITests(TestCase):
    """
    Tests that call the real NOWPayments sandbox REST API.

    All payments are created at class setup to avoid rate limits from
    making multiple API calls during individual test methods.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create one sandbox payment per currency — reused across tests.
        # A small delay prevents 429 errors from the sandbox API.
        cls.btc_payment = cls._api_create("btc", "sandbox-btc")
        time.sleep(1)
        cls.eth_payment = cls._api_create("eth", "sandbox-eth")
        time.sleep(1)
        cls.usdc_payment = cls._api_create("usdcerc20", "sandbox-usdc")

    @staticmethod
    def _api_create(pay_currency, order_id):
        resp = http_requests.post(
            f"{SANDBOX_BASE}/payment",
            headers=_api_headers(),
            json={
                "price_amount": 29.99,
                "price_currency": "usd",
                "pay_currency": pay_currency,
                "order_id": order_id,
                "case": "success",
            },
            timeout=15,
        )
        return resp

    def test_api_status(self):
        """Sandbox API is reachable and returns OK."""
        resp = http_requests.get(f"{SANDBOX_BASE}/status", timeout=10)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get("message"), "OK")

    def test_create_bitcoin_payment(self):
        """BTC payment creation returns 201 with required fields."""
        self.assertEqual(self.btc_payment.status_code, 201, self.btc_payment.text)
        data = self.btc_payment.json()
        self.assertIn("payment_id", data)
        self.assertIn("pay_address", data)
        self.assertIn("pay_amount", data)
        self.assertEqual(data["pay_currency"], "btc")
        self.assertIsNotNone(data["pay_address"])
        self.assertGreater(float(data["pay_amount"]), 0)

    def test_create_ethereum_payment(self):
        """ETH payment creation returns 201."""
        self.assertEqual(self.eth_payment.status_code, 201, self.eth_payment.text)
        data = self.eth_payment.json()
        self.assertIn("payment_id", data)
        self.assertEqual(data["pay_currency"], "eth")

    def test_create_usdc_payment(self):
        """USDC payment creation returns 201."""
        self.assertEqual(self.usdc_payment.status_code, 201, self.usdc_payment.text)
        data = self.usdc_payment.json()
        self.assertIn("payment_id", data)

    def test_get_payment_status(self):
        """Payment status can be retrieved by ID."""
        self.assertEqual(self.btc_payment.status_code, 201, self.btc_payment.text)
        payment_id = self.btc_payment.json()["payment_id"]

        resp = http_requests.get(
            f"{SANDBOX_BASE}/payment/{payment_id}",
            headers=_api_headers(),
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(str(data["payment_id"]), str(payment_id))
        self.assertIn("payment_status", data)

    def test_nowpayments_client_wrapper(self):
        """Our create_payment() wrapper returns the expected fields."""
        import payments.nowpayments as nowpayments

        time.sleep(1)  # avoid rate limit after setUpClass calls
        result = nowpayments.create_payment(
            amount_usd=29.99,
            pay_currency="btc",
            order_id="client-wrapper-test",
            ipn_callback_url="https://placeholder.example.com/webhook/",
        )
        self.assertIn("payment_id", result)
        self.assertIn("pay_address", result)
        self.assertIn("pay_amount", result)
        self.assertEqual(result["pay_currency"], "btc")


# ---------------------------------------------------------------------------
# 3. End-to-end local flow: sandbox API + simulated IPN → subscription active
# ---------------------------------------------------------------------------

@requires_sandbox
class SandboxEndToEndTests(TestCase):
    """
    Full end-to-end flow without ngrok:

      1. Create a real payment via the sandbox API (class-level setup).
      2. Build an IPN payload with the real payment_id and status=finished.
      3. Sign it with our IPN secret (same algorithm NOWPayments uses).
      4. POST to our local webhook view.
      5. Assert subscription activated and payment completed.

    Payments are created once in setUpClass and reused — this avoids
    hitting the sandbox API rate limit (429) across many test methods.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import payments.nowpayments as nowpayments

        # Create two payments for the different scenarios
        cls.btc_api_result = nowpayments.create_payment(
            amount_usd=29.99,
            pay_currency="btc",
            order_id="e2e-btc",
            ipn_callback_url="https://placeholder.example.com/webhook/",
        )
        time.sleep(1)
        cls.eth_api_result = nowpayments.create_payment(
            amount_usd=29.99,
            pay_currency="eth",
            order_id="e2e-eth",
            ipn_callback_url="https://placeholder.example.com/webhook/",
        )

    def setUp(self):
        self.django_client = Client()
        self.user = User.objects.create_user(
            email="sandbox@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", subscription_status="inactive"
        )
        self.webhook_url = reverse("nowpayments_webhook")

    def _simulate_ipn(self, payment_id, payment_status="finished", extra=None):
        """Build, sign and POST a fake IPN for the given payment_id."""
        data = {
            "payment_id": str(payment_id),
            "payment_status": payment_status,
            "pay_address": "1SimulatedAddress",
            "price_amount": 29.99,
            "price_currency": "usd",
            "pay_amount": 0.00085,
            "actually_paid": 0.00085,
            "pay_currency": "btc",
            "order_id": "e2e-btc",
            "outcome_transaction_hash": "0xfake_tx_for_testing",
        }
        if extra:
            data.update(extra)
        payload = json.dumps(data).encode()
        sig = _sign_payload(payload)
        return self.django_client.post(
            self.webhook_url,
            data=payload,
            content_type="application/json",
            HTTP_X_NOWPAYMENTS_SIG=sig,
        )

    def _create_db_record(self, api_result, payment_method):
        return SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method=payment_method,
            status="pending",
            nowpayments_payment_id=str(api_result["payment_id"]),
            pay_address=api_result.get("pay_address"),
            pay_amount=api_result.get("pay_amount"),
            pay_currency=api_result.get("pay_currency"),
        )

    # ---- happy path --------------------------------------------------------

    def test_btc_finished_activates_subscription(self):
        """BTC finished IPN → payment completed, subscription active."""
        payment = self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        response = self._simulate_ipn(self.btc_api_result["payment_id"], "finished")

        self.assertEqual(response.status_code, 200, response.content)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "completed")
        self.assertIsNotNone(payment.completed_at)
        self.assertEqual(payment.reference_id, "0xfake_tx_for_testing")

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "active")
        self.assertEqual(self.provider.subscription_payment_method, "crypto_bitcoin")
        self.assertIsNotNone(self.provider.subscription_renewal_date)

    def test_eth_finished_activates_subscription(self):
        """ETH finished IPN → payment completed, subscription active."""
        payment = self._create_db_record(self.eth_api_result, "crypto_ethereum")
        response = self._simulate_ipn(
            self.eth_api_result["payment_id"],
            "finished",
            extra={"pay_currency": "eth"},
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "completed")

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "active")
        self.assertEqual(self.provider.subscription_payment_method, "crypto_ethereum")

    # ---- failure scenarios -------------------------------------------------

    def test_failed_ipn_marks_payment_failed(self):
        """Failed IPN → payment failed, subscription stays inactive."""
        payment = self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        response = self._simulate_ipn(self.btc_api_result["payment_id"], "failed")

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "failed")

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "inactive")

    def test_expired_ipn_marks_payment_failed(self):
        """Expired IPN → payment failed."""
        payment = self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        response = self._simulate_ipn(self.btc_api_result["payment_id"], "expired")

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "failed")

    def test_refunded_ipn_marks_payment_failed(self):
        """Refunded IPN → payment failed."""
        payment = self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        response = self._simulate_ipn(self.btc_api_result["payment_id"], "refunded")

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "failed")

    # ---- intermediate statuses ---------------------------------------------

    def test_intermediate_statuses_leave_payment_pending(self):
        """Intermediate IPNs (confirming, sending, etc.) do not complete payment."""
        payment = self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        for status in ("waiting", "confirming", "confirmed", "sending", "partially_paid"):
            response = self._simulate_ipn(self.btc_api_result["payment_id"], status)
            self.assertEqual(response.status_code, 200)

        payment.refresh_from_db()
        self.assertEqual(payment.status, "pending")
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "inactive")

    # ---- edge cases --------------------------------------------------------

    def test_idempotency_double_finished_ipn(self):
        """Duplicate finished IPN does not double-activate or create duplicate records."""
        payment = self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        self._simulate_ipn(self.btc_api_result["payment_id"], "finished")
        self._simulate_ipn(self.btc_api_result["payment_id"], "finished")  # duplicate

        self.assertEqual(
            SubscriptionPayment.objects.filter(provider=self.provider).count(), 1
        )
        payment.refresh_from_db()
        self.assertEqual(payment.status, "completed")

    def test_invalid_signature_returns_400(self):
        """Webhook with wrong signature returns 400 without processing."""
        payment = self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        payload = json.dumps({
            "payment_id": str(self.btc_api_result["payment_id"]),
            "payment_status": "finished",
        }).encode()

        response = self.django_client.post(
            self.webhook_url,
            data=payload,
            content_type="application/json",
            HTTP_X_NOWPAYMENTS_SIG="invalidsig",
        )
        self.assertEqual(response.status_code, 400)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "pending")  # unchanged

    def test_unknown_payment_id_returns_200(self):
        """Webhook for an unknown payment_id returns 200 (idempotent, not an error)."""
        payload = json.dumps({
            "payment_id": "completely-unknown-id",
            "payment_status": "finished",
        }).encode()
        sig = _sign_payload(payload)
        response = self.django_client.post(
            self.webhook_url,
            data=payload,
            content_type="application/json",
            HTTP_X_NOWPAYMENTS_SIG=sig,
        )
        self.assertEqual(response.status_code, 200)

    # ---- provider UI flow --------------------------------------------------

    def test_provider_crypto_page_creates_real_sandbox_payment(self):
        """Provider hitting the crypto payment page creates a real sandbox payment record."""
        time.sleep(1)  # avoid rate limit
        self.django_client.login(email=self.user.email, password="testpass123")
        session = self.django_client.session
        session["pending_payment_method"] = "crypto_bitcoin"
        session.save()

        response = self.django_client.get(reverse("subscription_crypto_payment"))
        self.assertEqual(response.status_code, 200)

        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertIsNotNone(payment.nowpayments_payment_id)
        self.assertIsNotNone(payment.pay_address)
        self.assertGreater(float(payment.pay_amount), 0)

        # Pay address should appear in the rendered page
        self.assertContains(response, payment.pay_address)

    def test_provider_post_redirects_to_confirm_without_activating(self):
        """Clicking 'I've sent payment' redirects to confirm but does NOT activate."""
        payment = self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        session = self.django_client.session
        session["pending_payment_method"] = "crypto_bitcoin"
        session["nowpayments_payment_id"] = str(self.btc_api_result["payment_id"])
        session.save()

        self.django_client.login(email=self.user.email, password="testpass123")
        response = self.django_client.post(
            reverse("subscription_crypto_payment"), follow=True
        )

        self.assertIn(
            reverse("subscription_confirm"), response.request["PATH_INFO"]
        )
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "inactive")

    def test_confirm_page_shows_pending_banner_for_nowpayments(self):
        """Confirm page shows the amber 'awaiting confirmation' banner for NOWPayments payments."""
        self._create_db_record(self.btc_api_result, "crypto_bitcoin")
        self.django_client.login(email=self.user.email, password="testpass123")
        response = self.django_client.get(reverse("subscription_confirm"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["payment_pending"])
        self.assertContains(response, "Awaiting Payment Confirmation")
