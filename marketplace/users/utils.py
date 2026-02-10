import secrets
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_email_verification_token(user):
    """
    Generate a unique email verification token for a user.

    Args:
        user: User instance

    Returns:
        str: URL-safe token
    """
    # Generate a random token
    token = secrets.token_urlsafe(32)

    # Store token in user record
    user.email_verification_token = token
    user.save(update_fields=["email_verification_token"])

    return token


def verify_email_token(token):
    """
    Verify an email verification token and mark user as verified.

    Args:
        token: Email verification token

    Returns:
        User object if token is valid, None otherwise
    """
    try:
        # Find user by token
        user = User.objects.get(email_verification_token=token)
    except User.DoesNotExist:
        return None

    # Mark user as verified
    user.is_email_verified = True
    user.email_verification_token = None
    user.save()

    return user


def send_verification_email(user, request):
    """
    Send email verification email to user.

    Args:
        user: User instance
        request: Django request object

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Generate token
        token = generate_email_verification_token(user)

        # Build verification URL
        verification_url = (
            f"{request.build_absolute_uri('/auth/verify-email/')}{token}/"
        )

        # Prepare email content
        subject = "Verify Your Email - Massage Marketplace"

        text_message = f"""
Hi {user.email},

Please verify your email by clicking the link below:

{verification_url}

This link expires in 24 hours.

Best regards,
The Massage Marketplace Team
"""

        # Try to render HTML template, fallback to text only
        try:
            html_message = render_to_string(
                "emails/verify_email.html",
                {
                    "user": user,
                    "verification_url": verification_url,
                    "token": token,
                },
            )
        except Exception:
            html_message = None

        # Send email
        send_mail(
            subject,
            text_message,
            "noreply@massagemarketplace.com",
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error sending verification email: {e}")
        return False


def generate_password_reset_token(user):
    """
    Generate a unique password reset token for a user.

    Args:
        user: User instance

    Returns:
        str: URL-safe token
    """
    # Generate a random token
    token = secrets.token_urlsafe(32)

    # Store token in user record (reuse email_verification_token field for reset)
    user.email_verification_token = token
    user.save(update_fields=["email_verification_token"])

    return token


def verify_password_reset_token(token):
    """
    Verify a password reset token.

    Args:
        token: Password reset token

    Returns:
        User object if token is valid, None otherwise
    """
    try:
        # Find user by token
        user = User.objects.get(email_verification_token=token)
        return user
    except User.DoesNotExist:
        return None


def send_password_reset_email(user, request):
    """
    Send password reset email to user.

    Args:
        user: User instance
        request: Django request object

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Generate token
        token = generate_password_reset_token(user)

        # Build reset URL
        reset_url = (
            f"{request.build_absolute_uri('/auth/password-reset-confirm/')}{token}/"
        )

        # Prepare email content
        subject = "Reset Your Password - Massage Marketplace"

        text_message = f"""
Hi {user.email},

Click the link below to reset your password:

{reset_url}

This link expires in 24 hours.

If you didn't request a password reset, please ignore this email.

Best regards,
The Massage Marketplace Team
"""

        # Try to render HTML template, fallback to text only
        try:
            html_message = render_to_string(
                "emails/password_reset.html",
                {
                    "user": user,
                    "reset_url": reset_url,
                    "token": token,
                },
            )
        except Exception:
            html_message = None

        # Send email
        send_mail(
            subject,
            text_message,
            "noreply@massagemarketplace.com",
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error sending password reset email: {e}")
        return False
