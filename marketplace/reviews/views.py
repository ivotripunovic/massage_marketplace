from django.views.generic import CreateView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from reviews.models import Review
from reviews.forms import ReviewForm
from providers.models import Provider


class ReviewSubmitView(CreateView):
    """View for submitting reviews."""

    model = Review
    form_class = ReviewForm

    def dispatch(self, request, *args, **kwargs):
        """Get provider and store in instance."""
        self.provider = get_object_or_404(
            Provider,
            slug=self.kwargs.get("slug"),
            subscription_status="active",
            user__is_email_verified=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Save review with provider."""
        try:
            # Set the provider
            form.instance.provider = self.provider

            # Save the review
            self.object = form.save()

            # Send email notification to admin
            self._send_admin_notification()

            messages.success(
                self.request,
                "Thank you for your review! It has been submitted successfully.",
            )
            return redirect(self.get_success_url())

        except (IntegrityError, ValidationError):
            # Duplicate review (same email already reviewed this provider)
            messages.error(
                self.request, "You have already submitted a review for this provider."
            )
            return redirect(self.get_success_url())

    def form_invalid(self, form):
        """Redirect back to provider detail with error messages."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect back to provider detail page."""
        return reverse("provider_detail", kwargs={"slug": self.provider.slug})

    def get_context_data(self, **kwargs):
        """Add provider to context."""
        context = super().get_context_data(**kwargs)
        context["provider"] = self.provider
        return context

    def _send_admin_notification(self):
        """Send email notification to admin about new review."""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings

        try:
            subject = f"New Review Submitted - {self.provider.get_name()}"

            html_message = render_to_string(
                "emails/review_notification.html",
                {
                    "provider": self.provider,
                    "review": self.object,
                    "provider_url": self.request.build_absolute_uri(
                        reverse("provider_detail", kwargs={"slug": self.provider.slug})
                    ),
                },
            )

            # Send to admins (get from settings or use default)
            admin_emails = getattr(
                settings, "ADMIN_EMAILS", ["admin@massagemarketplace.com"]
            )

            send_mail(
                subject,
                f"New review submitted for {self.provider.get_name()}",
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                html_message=html_message,
                fail_silently=True,  # Don't break submission if email fails
            )
        except Exception:
            # Silently fail if email cannot be sent
            pass
