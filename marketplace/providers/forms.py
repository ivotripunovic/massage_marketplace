from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from PIL import Image
import io
from providers.models import Provider, ProviderGalleryImage


class ProviderPhotoForm(forms.ModelForm):
    """Form for uploading provider profile photo."""

    class Meta:
        model = Provider
        fields = ("photo",)
        labels = {
            "photo": "Profile Photo",
        }
        widgets = {
            "photo": forms.FileInput(
                attrs={
                    "class": "block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700",
                    "accept": "image/jpeg,image/png,image/gif",
                    "id": "photo-upload",
                }
            ),
        }

    def clean_photo(self):
        """Validate photo file."""
        photo = self.cleaned_data.get("photo")

        if not photo or not isinstance(photo, UploadedFile):
            return photo

        # Check file size (< 5MB)
        if photo.size > 5 * 1024 * 1024:
            raise ValidationError("Image must be smaller than 5MB")

        # Check file format
        valid_formats = ["image/jpeg", "image/png", "image/gif"]
        if photo.content_type not in valid_formats:
            raise ValidationError("Only JPEG, PNG, and GIF images are allowed")

        # Validate that it's a real image
        try:
            img = Image.open(photo)
            img.verify()
            # Reset file pointer after verification
            photo.seek(0)
        except Exception:
            raise ValidationError("The uploaded file is not a valid image")

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

            # Determine format from content_type or filename
            content_type = getattr(provider.photo, "content_type", "")
            filename_lower = provider.photo.name.lower()
            if content_type == "image/png" or filename_lower.endswith(".png"):
                save_format = "PNG"
            elif content_type == "image/gif" or filename_lower.endswith(".gif"):
                save_format = "GIF"
            else:
                save_format = "JPEG"

            img.save(img_io, format=save_format)
            img_io.seek(0)
            provider.photo.save(provider.photo.name, img_io, save=False)


class SubscriptionSettingsForm(forms.Form):
    """Form for subscription payment method selection."""

    PAYMENT_METHOD_CHOICES = [
        ("crypto_bitcoin", "Bitcoin"),
        ("crypto_ethereum", "Ethereum"),
        ("crypto_usdc", "USDC"),
    ]

    payment_method = forms.ChoiceField(
        label="Payment Method",
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "radio-button"}),
        required=True,
    )


class CryptoPaymentForm(forms.Form):
    """Form for submitting crypto transaction ID."""

    transaction_id = forms.CharField(
        label="Transaction ID / Hash",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "input-dark w-full font-mono",
                "placeholder": "e.g., 0x123abc456def...",
            }
        ),
        help_text="Paste the transaction hash from your wallet after sending payment.",
    )



class GalleryImageForm(forms.ModelForm):
    """Form for uploading gallery images."""

    class Meta:
        model = ProviderGalleryImage
        fields = ("image", "caption")
        labels = {
            "image": "Photo",
            "caption": "Caption (optional)",
        }
        widgets = {
            "image": forms.FileInput(
                attrs={
                    "class": "block w-full text-sm text-text-primary file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gold file:text-dark cursor-pointer",
                    "accept": "image/jpeg,image/png,image/gif",
                }
            ),
            "caption": forms.TextInput(
                attrs={
                    "class": "input-dark w-full",
                    "placeholder": "Describe this photo",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.provider = kwargs.pop("provider", None)
        super().__init__(*args, **kwargs)

    def clean_image(self):
        """Validate image file."""
        image = self.cleaned_data.get("image")

        if image:
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image must be smaller than 5MB")

            valid_formats = ["image/jpeg", "image/png", "image/gif"]
            if image.content_type not in valid_formats:
                raise ValidationError("Only JPEG, PNG, and GIF images are allowed")

            try:
                img = Image.open(image)
                img.verify()
                image.seek(0)
            except Exception:
                raise ValidationError("The uploaded file is not a valid image")

        return image

    def clean(self):
        """Enforce per-provider image limit."""
        cleaned_data = super().clean()
        if self.provider:
            current_count = ProviderGalleryImage.objects.filter(
                provider=self.provider
            ).count()
            if current_count >= ProviderGalleryImage.MAX_IMAGES_PER_PROVIDER:
                raise ValidationError(
                    f"You can upload a maximum of {ProviderGalleryImage.MAX_IMAGES_PER_PROVIDER} gallery images."
                )
        return cleaned_data
