from django.views.generic import FormView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from users.forms import SignupForm
from users.models import User
from users.utils import send_verification_email


class SignupView(FormView):
    """Provider signup view."""
    
    form_class = SignupForm
    template_name = 'users/signup.html'
    success_url = reverse_lazy('check_email')
    
    def form_valid(self, form):
        """Create user and send verification email."""
        # Create user
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user_type = form.cleaned_data.get('user_type', 'provider')
        
        user = User.objects.create_user(
            email=email,
            password=password,
            user_type=user_type,
            is_email_verified=False
        )
        
        # Send verification email
        try:
            send_verification_email(user, self.request)
        except Exception as e:
            # Log error but don't fail signup
            print(f"Error sending verification email: {e}")
        
        messages.success(
            self.request,
            'Account created! Check your email for verification link.'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle form errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        
        return super().form_invalid(form)


class CheckEmailView(TemplateView):
    """Page to check email for verification link."""
    
    template_name = 'users/check_email.html'
