"""
URL configuration for marketplace project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from users.views import (
    SignupView,
    CheckEmailView,
    VerifyEmailView,
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetSentView,
    PasswordResetConfirmView,
    ResendVerificationView,
)
from providers.views import (
    ProviderDashboardView,
    ProviderProfileUpdateView,
    AdminProviderListView,
    ProviderSubscriptionView,
    SubscriptionConfirmView,
    CryptoPaymentView,
    CryptoPaymentStatusView,
    GalleryImageCreateView,
    GalleryImageDeleteView,
)
from payments.views import (
    AdminPaymentListView,
    AdminPaymentDetailView,
    AdminDashboardView,
    AdminProviderDetailView,
    AdminProviderSuspendView,
    AdminPaymentApproveView,
    AdminAnalyticsView,
    NowPaymentsWebhookView,
)
from clients.views import (
    ProviderDirectoryView,
    ProviderDetailView,
    ClientProfileView,
    ClientReviewsView,
    country_search_api,
    city_search_api,
)
from reviews.views import ReviewSubmitView, ReviewReplyView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Public URLs
    path("", ProviderDirectoryView.as_view(), name="home"),
    path("providers/", ProviderDirectoryView.as_view(), name="providers"),
    path(
        "providers/<slug:slug>/", ProviderDetailView.as_view(), name="provider_detail"
    ),
    path(
        "providers/<slug:slug>/review/",
        ReviewSubmitView.as_view(),
        name="review_submit",
    ),
    path(
        "providers/<slug:slug>/review/<int:pk>/reply/",
        ReviewReplyView.as_view(),
        name="review_reply",
    ),
    # Authentication URLs
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/check-email/", CheckEmailView.as_view(), name="check_email"),
    path(
        "auth/resend-email/",
        ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    path(
        "auth/verify-email/<str:token>/", VerifyEmailView.as_view(), name="verify_email"
    ),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "auth/password-reset-sent/",
        PasswordResetSentView.as_view(),
        name="password_reset_sent",
    ),
    path(
        "auth/password-reset-confirm/<str:token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # Client URLs
    path("client/profile/", ClientProfileView.as_view(), name="client_profile"),
    path("client/reviews/", ClientReviewsView.as_view(), name="client_reviews"),
    # Provider URLs
    path(
        "provider/dashboard/",
        ProviderDashboardView.as_view(),
        name="provider_dashboard",
    ),
    path(
        "provider/profile/",
        ProviderProfileUpdateView.as_view(),
        name="provider_profile",
    ),
    path(
        "provider/subscription/",
        ProviderSubscriptionView.as_view(),
        name="subscription",
    ),
    path(
        "provider/subscription/crypto/",
        CryptoPaymentView.as_view(),
        name="subscription_crypto_payment",
    ),
    path(
        "provider/subscription/confirm/",
        SubscriptionConfirmView.as_view(),
        name="subscription_confirm",
    ),
    path(
        "provider/subscription/status/<str:nowpayments_payment_id>/",
        CryptoPaymentStatusView.as_view(),
        name="crypto_payment_status",
    ),
    path(
        "provider/gallery/upload/",
        GalleryImageCreateView.as_view(),
        name="gallery_upload",
    ),
    path(
        "provider/gallery/<int:pk>/delete/",
        GalleryImageDeleteView.as_view(),
        name="gallery_delete",
    ),
    # Admin URLs
    path("internal/admin/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path(
        "internal/admin/providers/",
        AdminProviderListView.as_view(),
        name="admin_providers",
    ),
    path(
        "internal/admin/providers/<int:pk>/",
        AdminProviderDetailView.as_view(),
        name="admin_provider_detail",
    ),
    path(
        "internal/admin/providers/<int:pk>/status/",
        AdminProviderSuspendView.as_view(),
        name="admin_provider_status",
    ),
    path(
        "internal/admin/payments/",
        AdminPaymentListView.as_view(),
        name="admin_payments",
    ),
    path(
        "internal/admin/payments/<int:pk>/",
        AdminPaymentDetailView.as_view(),
        name="admin_payment_detail",
    ),
    path(
        "internal/admin/payments/<int:pk>/action/",
        AdminPaymentApproveView.as_view(),
        name="admin_payment_action",
    ),
    path(
        "internal/admin/analytics/",
        AdminAnalyticsView.as_view(),
        name="admin_analytics",
    ),
    # Legal pages
    path(
        "terms/", TemplateView.as_view(template_name="legal/terms.html"), name="terms"
    ),
    path(
        "privacy/",
        TemplateView.as_view(template_name="legal/privacy.html"),
        name="privacy",
    ),
    path(
        "payment-policy/",
        TemplateView.as_view(template_name="legal/payment_policy.html"),
        name="payment_policy",
    ),
    # API endpoints for location autocomplete
    path("api/countries/search/", country_search_api, name="api_country_search"),
    path("api/cities/search/", city_search_api, name="api_city_search"),
    # NOWPayments IPN webhook
    path(
        "payments/webhook/nowpayments/",
        NowPaymentsWebhookView.as_view(),
        name="nowpayments_webhook",
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
