from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from providers.models import Provider


class ReviewCategory(models.Model):
    """Admin-defined rating category (e.g., 'Professionalism', 'Punctuality')."""

    name = models.CharField(max_length=150, unique=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "reviews_category"
        verbose_name = "Review Category"
        verbose_name_plural = "Review Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Review(models.Model):
    """Review model for provider ratings — authenticated clients only."""

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="reviews"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    comment = models.TextField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews_review"
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "client"],
                name="unique_provider_client_review",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client.email} → {self.provider.user.email} ({self.created_at.date()})"

    def average_rating(self):
        """Average of this review's category ratings."""
        from django.db.models import Avg

        avg = self.category_ratings.aggregate(Avg("rating"))["rating__avg"]
        return round(avg, 1) if avg else 0

    def clean(self):
        if self.comment and len(self.comment) > 250:
            raise ValidationError({"comment": "Comment must be 250 characters or less"})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ReviewCategoryRating(models.Model):
    """Per-category rating within a review."""

    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="category_ratings"
    )
    category = models.ForeignKey(
        ReviewCategory, on_delete=models.CASCADE, related_name="ratings"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        db_table = "reviews_category_rating"
        verbose_name = "Category Rating"
        verbose_name_plural = "Category Ratings"
        unique_together = ("review", "category")

    def __str__(self):
        return f"{self.category.name}: {self.rating}"


class ReviewReply(models.Model):
    """Provider's response to a review."""

    review = models.OneToOneField(
        Review, on_delete=models.CASCADE, related_name="reply"
    )
    comment = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews_reply"
        verbose_name = "Review Reply"
        verbose_name_plural = "Review Replies"

    def __str__(self):
        return f"Reply to {self.review}"
