from django import forms
from reviews.models import Review


class ReviewForm(forms.ModelForm):
    """Form for submitting reviews."""

    class Meta:
        model = Review
        fields = ["rating", "comment", "client_name", "client_email"]
        labels = {
            "rating": "Rating",
            "comment": "Your Review",
            "client_name": "Your Name (Optional)",
            "client_email": "Your Email (Required for verification)",
        }
        widgets = {
            "rating": forms.RadioSelect(
                choices=Review.RATING_CHOICES, attrs={"class": "review-rating-input"}
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "Share your experience with this provider...",
                    "rows": 4,
                    "maxlength": 250,
                }
            ),
            "client_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "Your name (leave blank for anonymous)",
                }
            ),
            "client_email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "your@email.com",
                    "required": True,
                }
            ),
        }
        help_texts = {
            "client_email": "Your email is required to prevent duplicate reviews. It will not be displayed publicly.",
            "comment": "Maximum 250 characters",
        }

    def clean_rating(self):
        """Validate rating is between 1 and 5."""
        rating = self.cleaned_data.get("rating")
        if rating is None:
            raise forms.ValidationError("Please select a rating.")
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating

    def clean_comment(self):
        """Validate comment length."""
        comment = self.cleaned_data.get("comment")
        if not comment or len(comment.strip()) == 0:
            raise forms.ValidationError("Please write a review.")
        if len(comment) > 250:
            raise forms.ValidationError("Review must be 250 characters or less.")
        return comment.strip()

    def clean_client_email(self):
        """Validate email is provided."""
        email = self.cleaned_data.get("client_email")
        if not email:
            raise forms.ValidationError(
                "Email is required to prevent duplicate reviews."
            )
        return email.lower()
