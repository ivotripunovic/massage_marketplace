"""Signup email checks: reject disposable and undeliverable addresses."""

from disposable_email_domains import blocklist
from django.conf import settings
from django.core.exceptions import ValidationError
from email_validator import EmailNotValidError, validate_email

DNS_TIMEOUT_SECONDS = 5


def _is_disposable(domain):
    """Return True if domain or any parent domain is on the disposable blocklist."""
    parts = domain.split(".")
    return any(".".join(parts[i:]) in blocklist for i in range(len(parts) - 1))


def validate_signup_email(email):
    """
    Validate that an email address can plausibly receive mail.

    Rejects disposable domains (local blocklist) and, when
    settings.EMAIL_CHECK_DELIVERABILITY is on, domains without MX/A records.
    DNS timeouts are not treated as failures, so a resolver hiccup never blocks signup.

    Returns:
        The lowercased email.

    Raises:
        ValidationError: If the address is disposable or undeliverable.
    """
    email = email.strip().lower()
    domain = email.rpartition("@")[2]

    if _is_disposable(domain):
        raise ValidationError("Disposable email addresses are not allowed.")

    try:
        validate_email(
            email,
            check_deliverability=settings.EMAIL_CHECK_DELIVERABILITY,
            timeout=DNS_TIMEOUT_SECONDS,
        )
    except EmailNotValidError:
        raise ValidationError(
            "This email domain cannot receive mail. Please check the address."
        )

    return email
