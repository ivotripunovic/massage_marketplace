from django import forms
from reviews.models import Review, ReviewCategory, ReviewReply


class ReviewForm(forms.ModelForm):
    """Form for submitting reviews with per-category ratings."""

    class Meta:
        model = Review
        fields = ["comment"]
        labels = {
            "comment": "Your Review",
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "input-dark w-full resize-none",
                    "placeholder": "Share your experience with this provider...",
                    "rows": 4,
                    "maxlength": 250,
                }
            ),
        }
        help_texts = {
            "comment": "Maximum 250 characters",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories = list(
            ReviewCategory.objects.filter(is_active=True).order_by(
                "display_order", "name"
            )
        )
        self.category_fields = []
        for cat in self.categories:
            field_name = f"category_{cat.pk}"
            self.fields[field_name] = forms.IntegerField(
                label=cat.name,
                required=False,
                min_value=1,
                max_value=5,
                widget=forms.RadioSelect(
                    choices=[(i, str(i)) for i in range(1, 6)],
                ),
            )
            self.category_fields.append(
                {
                    "category": cat,
                    "name": field_name,
                    "bound_field": self[field_name],
                }
            )

    def clean(self):
        cleaned = super().clean()
        has_rating = any(
            cleaned.get(f"category_{cat.pk}") is not None for cat in self.categories
        )
        if not has_rating:
            raise forms.ValidationError("Please rate at least one category.")
        return cleaned

    def clean_comment(self):
        comment = self.cleaned_data.get("comment")
        if not comment or len(comment.strip()) == 0:
            raise forms.ValidationError("Please write a review.")
        if len(comment) > 250:
            raise forms.ValidationError("Review must be 250 characters or less.")
        return comment.strip()


class ReviewReplyForm(forms.ModelForm):
    """Form for provider replies to reviews."""

    class Meta:
        model = ReviewReply
        fields = ["comment"]
        labels = {
            "comment": "Your Reply",
        }
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "input-dark w-full resize-none",
                    "placeholder": "Write your reply...",
                    "rows": 3,
                    "maxlength": 500,
                }
            ),
        }
