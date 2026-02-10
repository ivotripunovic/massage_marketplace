"""
Management command to monitor crypto payments.

Checks pending crypto payments against blockchain APIs to verify transactions.
Designed to be run as a cron job (e.g., every hour):
    python manage.py monitor_crypto_payments

Blockchain APIs used:
    - Bitcoin: Blockchain.com API
    - Ethereum/USDC: Etherscan API
"""

import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from payments.models import SubscriptionPayment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Monitor pending crypto payments and verify against blockchain APIs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Check payments without updating status",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        pending_crypto = (
            SubscriptionPayment.objects.filter(
                status="pending",
                payment_method__startswith="crypto_",
                reference_id__isnull=False,
            )
            .exclude(reference_id="")
            .select_related("provider__user")
        )

        count = pending_crypto.count()
        self.stdout.write(f"Found {count} pending crypto payment(s) to check.")

        verified = 0
        for payment in pending_crypto:
            result = self.verify_payment(payment)

            if result["verified"]:
                if not dry_run:
                    payment.mark_completed()
                    self.send_confirmation_email(payment)
                    verified += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Payment #{payment.pk} ({payment.provider.user.email}): VERIFIED"
                        )
                    )
                else:
                    self.stdout.write(
                        f"  Payment #{payment.pk} ({payment.provider.user.email}): "
                        f"Would be verified (dry run)"
                    )
            else:
                self.stdout.write(
                    f"  Payment #{payment.pk} ({payment.provider.user.email}): "
                    f"Not yet confirmed - {result.get('reason', 'pending')}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {verified} payment(s) verified out of {count} checked."
            )
        )

    def verify_payment(self, payment):
        """
        Verify a crypto payment against blockchain APIs.

        Returns dict with 'verified' (bool) and optional 'reason' (str).

        In production, this would call:
        - Bitcoin: https://blockchain.info/rawtx/{tx_hash}
        - Ethereum: https://api.etherscan.io/api?module=transaction&action=gettxinfo&txhash={tx_hash}
        - USDC: Same as Ethereum (ERC-20 token)
        """
        tx_hash = payment.reference_id
        method = payment.payment_method

        if not tx_hash:
            return {"verified": False, "reason": "No transaction hash provided"}

        try:
            if method == "crypto_bitcoin":
                return self._check_bitcoin_transaction(tx_hash, payment.amount)
            elif method in ("crypto_ethereum", "crypto_usdc"):
                return self._check_ethereum_transaction(tx_hash, payment.amount)
            else:
                return {"verified": False, "reason": f"Unknown method: {method}"}
        except Exception as e:
            logger.error(f"Error verifying payment #{payment.pk}: {e}")
            return {"verified": False, "reason": str(e)}

    def _check_bitcoin_transaction(self, tx_hash, expected_amount):
        """
        Check Bitcoin transaction via Blockchain.com API.

        Production implementation would:
        1. GET https://blockchain.info/rawtx/{tx_hash}
        2. Check 'block_height' is not None (confirmed)
        3. Verify output amount matches expected
        """
        # Stub: In production, call blockchain.info API
        # For now, return not verified (manual admin approval required)
        return {
            "verified": False,
            "reason": "Blockchain API check not configured - use admin approval",
        }

    def _check_ethereum_transaction(self, tx_hash, expected_amount):
        """
        Check Ethereum/USDC transaction via Etherscan API.

        Production implementation would:
        1. GET https://api.etherscan.io/api?module=proxy&action=eth_getTransactionReceipt&txhash={tx_hash}
        2. Check 'status' == '0x1' (success)
        3. Verify 'to' address matches platform wallet
        4. Verify amount matches expected
        """
        # Stub: In production, call Etherscan API
        return {
            "verified": False,
            "reason": "Etherscan API check not configured - use admin approval",
        }

    def send_confirmation_email(self, payment):
        """Send payment confirmation email to provider."""
        try:
            send_mail(
                "Payment Confirmed - Massage Marketplace",
                f"Your {payment.get_payment_method_display()} payment of "
                f"${payment.amount} has been verified and confirmed.\n\n"
                f"Your subscription is active until "
                f"{payment.provider.subscription_renewal_date}.\n\n"
                f"Thank you for using Massage Marketplace!",
                "noreply@massagemarketplace.com",
                [payment.provider.user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(
                f"Failed to send confirmation email for payment #{payment.pk}: {e}"
            )
