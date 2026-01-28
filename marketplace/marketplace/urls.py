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
from django.conf import settings
from django.conf.urls.static import static
from users.views import (
    SignupView, CheckEmailView, VerifyEmailView, LoginView, LogoutView,
    PasswordResetView, PasswordResetSentView, PasswordResetConfirmView
)
from providers.views import (
    ProviderDashboardView, ProviderProfileUpdateView,
    CertificationCreateView, CertificationDeleteView,
    ServiceListView, ServiceCreateView, ServiceUpdateView, ServiceDeleteView,
    AdminProviderListView, ProviderSubscriptionView, SubscriptionConfirmView
)
from payments.views import AdminPaymentListView, AdminPaymentDetailView
from clients.views import ProviderDirectoryView, ProviderDetailView
from reviews.views import ReviewSubmitView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public URLs
    path('', ProviderDirectoryView.as_view(), name='home'),
    path('providers/', ProviderDirectoryView.as_view(), name='providers'),
    path('providers/<str:slug>/', ProviderDetailView.as_view(), name='provider_detail'),
    path('providers/<str:slug>/review/', ReviewSubmitView.as_view(), name='review_submit'),

    # Authentication URLs
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('auth/check-email/', CheckEmailView.as_view(), name='check_email'),
    path('auth/verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('auth/password-reset-sent/', PasswordResetSentView.as_view(), name='password_reset_sent'),
    path('auth/password-reset-confirm/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Provider URLs
    path('provider/dashboard/', ProviderDashboardView.as_view(), name='provider_dashboard'),
    path('provider/profile/', ProviderProfileUpdateView.as_view(), name='provider_profile'),
    path('provider/subscription/', ProviderSubscriptionView.as_view(), name='subscription'),
    path('provider/subscription/confirm/', SubscriptionConfirmView.as_view(), name='subscription_confirm'),
    path('provider/certifications/add/', CertificationCreateView.as_view(), name='add_certification'),
    path('provider/certifications/<int:pk>/delete/', CertificationDeleteView.as_view(), name='delete_certification'),
    path('provider/services/', ServiceListView.as_view(), name='services_list'),
    path('provider/services/create/', ServiceCreateView.as_view(), name='service_create'),
    path('provider/services/<int:pk>/edit/', ServiceUpdateView.as_view(), name='service_edit'),
    path('provider/services/<int:pk>/delete/', ServiceDeleteView.as_view(), name='service_delete'),
    
    # Admin URLs
    path('internal/admin/providers/', AdminProviderListView.as_view(), name='admin_providers'),
    path('internal/admin/payments/', AdminPaymentListView.as_view(), name='admin_payments'),
    path('internal/admin/payments/<int:pk>/', AdminPaymentDetailView.as_view(), name='admin_payment_detail'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
