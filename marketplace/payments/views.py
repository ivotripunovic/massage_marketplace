import json
import logging

from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q, Sum, Avg
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from payments.models import SubscriptionPayment
from providers.models import Provider

logger = logging.getLogger(__name__)


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to require admin user type."""

    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and is an admin."""
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.user_type != "admin":
            return HttpResponseForbidden(
                "You do not have permission to access this page."
            )

        return super().dispatch(request, *args, **kwargs)


class AdminPaymentListView(AdminRequiredMixin, ListView):
    """View for listing all subscription payments (admin only)."""

    model = SubscriptionPayment
    template_name = "admin/payment_list.html"
    context_object_name = "payments"
    paginate_by = 50

    def get_queryset(self):
        """Get all payments with related provider info."""
        queryset = SubscriptionPayment.objects.select_related(
            "provider__user"
        ).order_by("-created_at")

        # Filter by status
        status = self.request.GET.get("status", "").strip()
        if status and status in ["pending", "completed", "failed"]:
            queryset = queryset.filter(status=status)

        # Filter by payment method
        method = self.request.GET.get("method", "").strip()
        if method:
            queryset = queryset.filter(payment_method=method)

        # Search by provider email or reference ID
        search = self.request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(provider__user__email__icontains=search)
                | Q(reference_id__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        """Add filter values and payment methods to context."""
        context = super().get_context_data(**kwargs)

        context["status"] = self.request.GET.get("status", "")
        context["method"] = self.request.GET.get("method", "")
        context["search"] = self.request.GET.get("search", "")

        context["status_choices"] = ["pending", "completed", "failed"]
        context["method_choices"] = [
            ("crypto_bitcoin", "Bitcoin"),
            ("crypto_ethereum", "Ethereum"),
            ("crypto_usdc", "USDC"),
        ]

        return context


class AdminPaymentDetailView(AdminRequiredMixin, DetailView):
    """View for viewing payment details (admin only)."""

    model = SubscriptionPayment
    template_name = "admin/payment_detail.html"
    context_object_name = "payment"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        """Get payment with related provider info."""
        return SubscriptionPayment.objects.select_related("provider__user")


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin dashboard with key platform metrics."""

    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from reviews.models import Review
        from users.models import User

        # Provider metrics
        providers = Provider.objects.all()
        context["total_providers"] = providers.count()
        context["active_providers"] = providers.filter(
            subscription_status="active"
        ).count()
        context["inactive_providers"] = providers.filter(
            subscription_status="inactive"
        ).count()
        context["suspended_providers"] = providers.filter(
            subscription_status="suspended"
        ).count()

        # Review metrics
        context["total_reviews"] = Review.objects.count()

        # Payment metrics
        payments = SubscriptionPayment.objects.all()
        context["pending_payments"] = payments.filter(status="pending").count()
        context["total_revenue"] = (
            payments.filter(status="completed").aggregate(total=Sum("amount"))["total"]
            or 0
        )

        # This month's revenue
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context["monthly_revenue"] = (
            payments.filter(
                status="completed", completed_at__gte=month_start
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        # Total users
        context["total_users"] = User.objects.count()

        return context


class AdminProviderDetailView(AdminRequiredMixin, DetailView):
    """Admin view for managing a single provider."""

    model = Provider
    template_name = "admin/provider_detail.html"
    context_object_name = "provider"

    def get_queryset(self):
        return Provider.objects.select_related("user").prefetch_related(
            "reviews__client",
            "reviews__reply",
            "reviews__category_ratings__category",
            "subscription_payments",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider = self.object
        context["reviews"] = (
            provider.reviews.select_related("client", "reply")
            .prefetch_related("category_ratings__category")
            .order_by("-created_at")[:10]
        )
        context["payments"] = provider.subscription_payments.all().order_by(
            "-created_at"
        )[:10]
        context["avg_rating"] = provider.average_rating()
        context["total_reviews"] = provider.reviews.count()
        return context


class AdminProviderSuspendView(AdminRequiredMixin, View):
    """Suspend or activate a provider account."""

    def post(self, request, pk):
        provider = get_object_or_404(Provider, pk=pk)
        action = request.POST.get("action")

        if action == "suspend":
            provider.subscription_status = "suspended"
            provider.save(update_fields=["subscription_status"])
            messages.success(
                request, f"Provider {provider.user.email} has been suspended."
            )
        elif action == "activate":
            provider.subscription_status = "active"
            provider.save(update_fields=["subscription_status"])
            messages.success(
                request, f"Provider {provider.user.email} has been activated."
            )
        elif action == "deactivate":
            provider.deactivate_subscription()
            messages.success(
                request, f"Provider {provider.user.email} has been deactivated."
            )

        return redirect("admin_provider_detail", pk=pk)


class AdminPaymentApproveView(AdminRequiredMixin, View):
    """Approve or reject a subscription payment."""

    def post(self, request, pk):
        payment = get_object_or_404(SubscriptionPayment, pk=pk)
        action = request.POST.get("action")

        if action == "approve":
            payment.mark_completed()
            messages.success(
                request,
                f"Payment #{payment.pk} for {payment.provider.user.email} marked as completed.",
            )
            # Send confirmation email
            self._send_payment_confirmation(payment)
        elif action == "reject":
            payment.mark_failed()
            notes = request.POST.get("notes", "")
            if notes:
                payment.notes = notes
                payment.save(update_fields=["notes"])
            messages.success(
                request,
                f"Payment #{payment.pk} for {payment.provider.user.email} marked as failed.",
            )

        return redirect("admin_payment_detail", pk=pk)

    def _send_payment_confirmation(self, payment):
        from django.core.mail import send_mail

        try:
            send_mail(
                "Payment Confirmed - Massage Marketplace",
                f"Your payment of ${payment.amount} has been verified and confirmed. "
                f"Your subscription is active until {payment.provider.subscription_renewal_date}.",
                "noreply@massagemarketplace.com",
                [payment.provider.user.email],
                fail_silently=True,
            )
        except Exception:
            pass


@method_decorator(csrf_exempt, name="dispatch")
class NowPaymentsWebhookView(View):
    """Receive and process IPN callbacks from NOWPayments."""

    TERMINAL_SUCCESS = "finished"
    TERMINAL_FAILURE = {"failed", "expired", "refunded"}

    def post(self, request):
        from payments.nowpayments import verify_ipn_signature

        payload_bytes = request.body
        received_sig = request.headers.get("x-nowpayments-sig", "")

        if not verify_ipn_signature(payload_bytes, received_sig):
            logger.warning("NOWPayments IPN: invalid signature")
            return HttpResponse(status=400)

        try:
            data = json.loads(payload_bytes)
        except json.JSONDecodeError:
            logger.warning("NOWPayments IPN: invalid JSON body")
            return HttpResponse(status=400)

        nowpayments_id = str(data.get("payment_id", ""))
        status = data.get("payment_status", "")

        if not nowpayments_id:
            return HttpResponse(status=400)

        try:
            payment = SubscriptionPayment.objects.select_related(
                "provider__user"
            ).get(nowpayments_payment_id=nowpayments_id)
        except SubscriptionPayment.DoesNotExist:
            logger.warning(
                "NOWPayments IPN: payment %s not found in DB", nowpayments_id
            )
            return HttpResponse(status=200)

        if payment.status == "completed":
            # Idempotent: already processed
            return HttpResponse(status=200)

        if status == self.TERMINAL_SUCCESS:
            payment.mark_completed()
            # Store the on-chain transaction hash if provided
            tx_hash = data.get("outcome_transaction_hash") or data.get(
                "payin_hash", ""
            )
            if tx_hash:
                payment.reference_id = tx_hash
                payment.save(update_fields=["reference_id"])
            payment.provider.activate_subscription(payment.payment_method)
            self._send_confirmation_email(payment)
            logger.info(
                "NOWPayments IPN: payment %s completed for %s",
                nowpayments_id,
                payment.provider.user.email,
            )
        elif status in self.TERMINAL_FAILURE:
            payment.mark_failed()
            logger.info(
                "NOWPayments IPN: payment %s %s for %s",
                nowpayments_id,
                status,
                payment.provider.user.email,
            )

        return HttpResponse(status=200)

    def _send_confirmation_email(self, payment):
        from django.core.mail import send_mail

        try:
            send_mail(
                "Payment Confirmed - Massage Marketplace",
                f"Your payment of ${payment.amount} has been verified and confirmed. "
                f"Your subscription is active until {payment.provider.subscription_renewal_date}.",
                "noreply@massagemarketplace.com",
                [payment.provider.user.email],
                fail_silently=True,
            )
        except Exception:
            pass


class AdminAnalyticsView(AdminRequiredMixin, TemplateView):
    """Admin analytics dashboard with charts and metrics."""

    template_name = "admin/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from reviews.models import Review
        from datetime import timedelta

        now = timezone.now()

        # Provider signups over last 6 months (by month)
        signup_data = []
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                month_end = now
            count = Provider.objects.filter(
                created_at__gte=month_start, created_at__lt=month_end
            ).count()
            signup_data.append(
                {
                    "month": month_start.strftime("%b %Y"),
                    "count": count,
                }
            )
        context["signup_data"] = signup_data

        # Revenue over last 6 months
        revenue_data = []
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                month_end = now
            total = (
                SubscriptionPayment.objects.filter(
                    status="completed",
                    completed_at__gte=month_start,
                    completed_at__lt=month_end,
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )
            revenue_data.append(
                {
                    "month": month_start.strftime("%b %Y"),
                    "total": float(total),
                }
            )
        context["revenue_data"] = revenue_data

        # Key metrics
        total_providers = Provider.objects.count()
        active_providers = Provider.objects.filter(subscription_status="active").count()
        context["conversion_rate"] = (
            round(active_providers / total_providers * 100, 1)
            if total_providers > 0
            else 0
        )

        total_revenue = (
            SubscriptionPayment.objects.filter(status="completed").aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
        context["avg_revenue_per_provider"] = (
            round(float(total_revenue) / active_providers, 2)
            if active_providers > 0
            else 0
        )

        context["active_providers"] = active_providers
        context["total_providers"] = total_providers
        context["total_reviews"] = Review.objects.count()
        from reviews.models import ReviewCategoryRating

        context["avg_rating"] = (
            ReviewCategoryRating.objects.aggregate(avg=Avg("rating"))["avg"] or 0
        )

        return context
