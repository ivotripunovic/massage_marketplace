from django.views.generic import CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from reviews.models import Review, ReviewCategoryRating
from reviews.forms import ReviewForm, ReviewReplyForm
from providers.models import Provider


class ReviewSubmitView(LoginRequiredMixin, CreateView):
    """View for submitting reviews — authenticated clients only."""

    model = Review
    form_class = ReviewForm

    def dispatch(self, request, *args, **kwargs):
        self.provider = get_object_or_404(
            Provider,
            slug=self.kwargs.get("slug"),
            subscription_status="active",
            user__is_email_verified=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.request.user.user_type != "client":
            messages.error(self.request, "Only clients can leave reviews.")
            return redirect(self.get_success_url())

        try:
            review = form.save(commit=False)
            review.provider = self.provider
            review.client = self.request.user
            review.save()

            # Save category ratings
            for cat_field in form.category_fields:
                rating_value = form.cleaned_data.get(cat_field["name"])
                if rating_value is not None:
                    ReviewCategoryRating.objects.create(
                        review=review,
                        category=cat_field["category"],
                        rating=rating_value,
                    )

            self._send_admin_notification(review)
            messages.success(
                self.request,
                "Thank you for your review! It has been submitted successfully.",
            )
            return redirect(self.get_success_url())

        except (IntegrityError, ValidationError):
            messages.error(
                self.request, "You have already submitted a review for this provider."
            )
            return redirect(self.get_success_url())

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("provider_detail", kwargs={"slug": self.provider.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["provider"] = self.provider
        return context

    def _send_admin_notification(self, review):
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings

        try:
            subject = f"New Review Submitted - {self.provider.get_name()}"
            html_message = render_to_string(
                "emails/review_notification.html",
                {
                    "provider": self.provider,
                    "review": review,
                    "provider_url": self.request.build_absolute_uri(
                        reverse("provider_detail", kwargs={"slug": self.provider.slug})
                    ),
                },
            )
            admin_emails = getattr(
                settings, "ADMIN_EMAILS", ["admin@massagemarketplace.com"]
            )
            send_mail(
                subject,
                f"New review submitted for {self.provider.get_name()}",
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                html_message=html_message,
                fail_silently=True,
            )
        except Exception:
            pass


class ReviewReplyView(LoginRequiredMixin, View):
    """Provider reply to a review — POST only."""

    http_method_names = ["post"]

    def post(self, request, slug, pk):
        provider = get_object_or_404(Provider, slug=slug)

        # Only the provider who owns this profile can reply
        if request.user != provider.user:
            messages.error(
                request, "You do not have permission to reply to this review."
            )
            return redirect(reverse("provider_detail", kwargs={"slug": slug}))

        review = get_object_or_404(Review, pk=pk, provider=provider)

        if hasattr(review, "reply"):
            messages.error(request, "You have already replied to this review.")
            return redirect(reverse("provider_detail", kwargs={"slug": slug}))

        form = ReviewReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.review = review
            reply.save()
            messages.success(request, "Your reply has been posted.")
        else:
            for error in form.errors.values():
                messages.error(request, error[0])

        return redirect(reverse("provider_detail", kwargs={"slug": slug}))
