from django import forms
from django.core.exceptions import ValidationError
from PIL import Image
import io
from providers.models import Provider, Service


class ProviderPhotoForm(forms.ModelForm):
    """Form for uploading provider profile photo."""
    
    class Meta:
        model = Provider
        fields = ('photo',)
        labels = {
            'photo': 'Profile Photo',
        }
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700',
                'accept': 'image/jpeg,image/png,image/gif',
                'id': 'photo-upload'
            }),
        }
    
    def clean_photo(self):
        """Validate photo file."""
        photo = self.cleaned_data.get('photo')
        
        if photo:
            # Check file size (< 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError('Image must be smaller than 5MB')
            
            # Check file format
            valid_formats = ['image/jpeg', 'image/png', 'image/gif']
            if photo.content_type not in valid_formats:
                raise ValidationError('Only JPEG, PNG, and GIF images are allowed')
            
            # Validate that it's a real image
            try:
                img = Image.open(photo)
                img.verify()
                # Reset file pointer after verification
                photo.seek(0)
            except Exception:
                raise ValidationError('The uploaded file is not a valid image')
        
        return photo
    
    def save(self, commit=True):
        """Save and process the image."""
        provider = super().save(commit=False)
        
        if provider.photo:
            # Resize image if needed
            self._resize_image(provider)
        
        if commit:
            provider.save()
        
        return provider
    
    def _resize_image(self, provider):
        """Resize image to maximum 800x800 pixels."""
        if not provider.photo:
            return
        
        # Read the image
        img = Image.open(provider.photo)
        
        # Check if resizing is needed
        if img.height > 800 or img.width > 800:
            # Create thumbnail
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save the resized image back to the field
            img_io = io.BytesIO()
            
            # Determine format from content type
            if provider.photo.content_type == 'image/png':
                img.save(img_io, format='PNG')
            elif provider.photo.content_type == 'image/gif':
                img.save(img_io, format='GIF')
            else:  # JPEG
                img.save(img_io, format='JPEG')
            
            img_io.seek(0)
            provider.photo.save(provider.photo.name, img_io, save=False)


class ServiceForm(forms.ModelForm):
    """Form for creating and updating services."""
    
    class Meta:
        model = Service
        fields = ('service_type', 'description', 'price', 'duration_minutes')
        labels = {
            'service_type': 'Service Type',
            'description': 'Service Description',
            'price': 'Price (USD)',
            'duration_minutes': 'Duration',
        }
        widgets = {
            'service_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
                'placeholder': 'Describe your service',
                'rows': 4
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
                'placeholder': '75.00',
                'min': '5.00',
                'step': '0.01',
                'type': 'number'
            }),
            'duration_minutes': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent',
            }),
        }


class SubscriptionSettingsForm(forms.Form):
    """Form for subscription payment method selection."""

    PAYMENT_METHOD_CHOICES = [
        ('crypto_bitcoin', 'Bitcoin'),
        ('crypto_ethereum', 'Ethereum'),
        ('crypto_usdc', 'USDC'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    payment_method = forms.ChoiceField(
        label='Payment Method',
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'radio-button'
        }),
        required=True
    )


class CryptoPaymentForm(forms.Form):
    """Form for submitting crypto transaction ID."""

    transaction_id = forms.CharField(
        label='Transaction ID / Hash',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono',
            'placeholder': 'e.g., 0x123abc456def...',
        }),
        help_text='Paste the transaction hash from your wallet after sending payment.'
    )


class BankTransferForm(forms.Form):
    """Form for confirming bank transfer details."""

    sender_name = forms.CharField(
        label='Account Holder Name',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Name on bank account',
        })
    )

    bank_name = forms.CharField(
        label='Bank Name',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., Chase Bank',
        })
    )

    reference_number = forms.CharField(
        label='Transfer Reference / Confirmation Number',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Bank transfer reference (if available)',
        }),
        help_text='Enter your bank transfer confirmation number if you have one. You can also provide this later.'
    )
