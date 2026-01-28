from django.db import models
from django.core.exceptions import ValidationError
from providers.models import Provider


class Review(models.Model):
    """Review model for provider ratings."""
    
    RATING_CHOICES = (
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    )
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    client_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Leave blank for anonymous review'
    )
    
    client_email = models.EmailField(blank=True, null=True)
    
    rating = models.IntegerField(choices=RATING_CHOICES)
    
    comment = models.TextField(max_length=250)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews_review'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        # Unique constraint on provider and client_email to prevent duplicates
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'client_email'],
                name='unique_provider_client_review',
                condition=models.Q(client_email__isnull=False)
            )
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider.user.email} - {self.rating} stars - {self.created_at.date()}"
    
    def clean(self):
        """Validate review fields."""
        if self.rating not in dict(self.RATING_CHOICES).keys():
            raise ValidationError({'rating': 'Rating must be between 1 and 5'})
        
        if len(self.comment) > 250:
            raise ValidationError({'comment': 'Comment must be 250 characters or less'})
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)
