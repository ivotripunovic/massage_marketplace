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
from users.views import (
    SignupView, CheckEmailView, VerifyEmailView, LoginView, LogoutView,
    PasswordResetView, PasswordResetSentView, PasswordResetConfirmView
)
from providers.views import ProviderDashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    
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
]
