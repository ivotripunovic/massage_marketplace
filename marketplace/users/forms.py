from django import forms
from django.core.exceptions import ValidationError
from users.models import User


class SignupForm(forms.Form):
    """Form for user signup."""
    
    email = forms.EmailField(
        label='Email Address',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )
    
    password = forms.CharField(
        label='Password',
        required=True,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'At least 8 characters'
        })
    )
    
    password_confirm = forms.CharField(
        label='Confirm Password',
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat your password'
        })
    )
    
    user_type = forms.ChoiceField(
        label='Account Type',
        required=True,
        initial='provider',
        choices=[('provider', 'I am a Service Provider')],
        widget=forms.RadioSelect()
    )
    
    def clean_email(self):
        """Validate email is unique."""
        email = self.cleaned_data.get('email', '').lower()
        
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        
        return email
    
    def clean(self):
        """Validate password confirmation."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def clean_password(self):
        """Validate password length."""
        password = self.cleaned_data.get('password', '')
        
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        
        return password
