from django.views.generic import FormView, TemplateView, View
from django.urls import reverse_lazy
from django.contrib import messages, auth
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from django import forms
from users.forms import (
    SignupForm,
    LoginForm,
    PasswordResetForm,
    PasswordResetConfirmForm,
)
from users.models import User
from users.utils import (
    send_verification_email,
    verify_email_token,
    send_password_reset_email,
    verify_password_reset_token,
)


class SignupView(FormView):
    """Provider signup view."""

    form_class = SignupForm
    template_name = "users/signup.html"
    success_url = reverse_lazy("check_email")

    def form_valid(self, form):
        """Create user and send verification email."""
        # Create user
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user_type = form.cleaned_data.get("user_type", "provider")

        user = User.objects.create_user(
            email=email, password=password, user_type=user_type, is_email_verified=False
        )

        # Send verification email
        try:
            send_verification_email(user, self.request)
        except Exception as e:
            # Log error but don't fail signup
            print(f"Error sending verification email: {e}")

        messages.success(
            self.request, "Account created! Check your email for verification link."
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")

        return super().form_invalid(form)


class CheckEmailView(TemplateView):
    """Page to check email for verification link."""

    template_name = "users/check_email.html"


class VerifyEmailView(View):
    """Verify email token and activate user account."""

    def get(self, request, token):
        """Verify email token."""
        try:
            verify_email_token(token)
            messages.success(
                request, "Email verified successfully! You can now log in."
            )
            return HttpResponseRedirect(reverse_lazy("login"))
        except Exception as e:
            # Token is invalid or expired
            context = {
                "error": "Token expired or invalid",
                "error_message": str(e),
            }
            return render(request, "users/verify_email_error.html", context, status=400)


class ResendVerificationView(FormView):
    """Resend email verification link."""

    template_name = "users/resend_verification.html"
    success_url = reverse_lazy("check_email")

    class ResendForm(forms.Form):
        email = forms.EmailField(
            widget=forms.EmailInput(
                attrs={"class": "input-dark w-full", "placeholder": "your@email.com"}
            )
        )

    form_class = ResendForm

    def form_valid(self, form):
        email = form.cleaned_data["email"].lower()
        try:
            user = User.objects.get(email__iexact=email, is_email_verified=False)
            send_verification_email(user, self.request)
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        messages.success(
            self.request,
            "If an unverified account exists with that email, a new verification link has been sent.",
        )
        return super().form_valid(form)


class LoginView(FormView):
    """User login view."""

    form_class = LoginForm
    template_name = "users/login.html"

    def get_success_url(self):
        """Return redirect URL based on 'next' param or user type."""
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return next_url
        if hasattr(self.request.user, "user_type") and self.request.user.user_type == "provider":
            return reverse_lazy("provider_dashboard")
        return reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        """Redirect logged-in users to appropriate page."""
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Authenticate and login user."""
        email = form.cleaned_data["email"].lower()
        password = form.cleaned_data["password"]

        user = auth.authenticate(email=email, password=password)
        if user is not None:
            auth.login(self.request, user)
            messages.success(self.request, f"Welcome back, {user.email}!")

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(self.request, str(error))
                else:
                    messages.error(self.request, f"{field}: {error}")

        return super().form_invalid(form)


class LogoutView(View):
    """User logout view."""

    def post(self, request):
        """Logout user and redirect."""
        auth.logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("login")

    def get(self, request):
        """Handle GET request - redirect to login."""
        auth.logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("login")


class PasswordResetView(FormView):
    """Password reset request view."""

    form_class = PasswordResetForm
    template_name = "users/password_reset.html"
    success_url = reverse_lazy("password_reset_sent")

    def form_valid(self, form):
        """Send password reset email."""
        email = form.cleaned_data["email"].lower()

        try:
            user = User.objects.get(email__iexact=email)
            send_password_reset_email(user, self.request)
            messages.success(
                self.request,
                "If an account exists with this email, you will receive a password reset link.",
            )
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            messages.success(
                self.request,
                "If an account exists with this email, you will receive a password reset link.",
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")

        return super().form_invalid(form)


class PasswordResetSentView(TemplateView):
    """Page shown after password reset email is sent."""

    template_name = "users/password_reset_sent.html"


class PasswordResetConfirmView(FormView):
    """Password reset confirmation view."""

    form_class = PasswordResetConfirmForm
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("login")

    def dispatch(self, request, token, *args, **kwargs):
        """Check if token is valid before displaying form."""
        self.user = verify_password_reset_token(token)
        if self.user is None:
            messages.error(request, "Password reset link is invalid or expired.")
            return redirect("password_reset")
        return super().dispatch(request, token, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add token to context."""
        context = super().get_context_data(**kwargs)
        context["token"] = self.kwargs["token"]
        return context

    def form_valid(self, form):
        """Set new password."""
        password = form.cleaned_data["password"]

        # Update password
        self.user.set_password(password)
        self.user.email_verification_token = None  # Clear reset token
        self.user.save()

        messages.success(
            self.request,
            "Password reset successfully! You can now log in with your new password.",
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                if field == "__all__":
                    messages.error(self.request, str(error))
                else:
                    messages.error(self.request, f"{field}: {error}")

        return super().form_invalid(form)
