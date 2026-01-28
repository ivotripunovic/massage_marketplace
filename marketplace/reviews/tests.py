from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from users.models import User
from providers.models import Provider
from .models import Review


class ReviewModelTests(TestCase):
    """Test Review model functionality."""
    
    def setUp(self):
        """Set up test provider and client for reviews."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
    
    def test_review_creation(self):
        """Test creating a review."""
        review = Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='Great service!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Great service!')
    
    def test_review_with_client_name(self):
        """Test review with client name."""
        review = Review.objects.create(
            provider=self.provider,
            client_name='John Doe',
            client_email='john@example.com',
            rating=4,
            comment='Very satisfied with the service'
        )
        self.assertEqual(review.client_name, 'John Doe')
        self.assertEqual(review.client_email, 'john@example.com')
    
    def test_anonymous_review(self):
        """Test anonymous review (no client name)."""
        review = Review.objects.create(
            provider=self.provider,
            client_name=None,
            rating=5,
            comment='Excellent massage'
        )
        self.assertIsNone(review.client_name)
    
    def test_review_rating_validation(self):
        """Test review rating validation."""
        with self.assertRaises(ValidationError):
            review = Review(
                provider=self.provider,
                rating=6,  # Invalid
                comment='Good'
            )
            review.full_clean()
    
    def test_valid_ratings(self):
        """Test all valid ratings."""
        for rating in [1, 2, 3, 4, 5]:
            review = Review.objects.create(
                provider=self.provider,
                client_email=f'client{rating}@test.com',
                rating=rating,
                comment='Test comment'
            )
            self.assertEqual(review.rating, rating)
    
    def test_review_comment_max_length(self):
        """Test comment max length validation."""
        long_comment = 'a' * 251
        with self.assertRaises(ValidationError):
            review = Review(
                provider=self.provider,
                rating=5,
                comment=long_comment
            )
            review.full_clean()
    
    def test_review_comment_valid_length(self):
        """Test comment at maximum valid length."""
        comment = 'a' * 250
        review = Review.objects.create(
            provider=self.provider,
            rating=5,
            comment=comment
        )
        self.assertEqual(len(review.comment), 250)
    
    def test_review_string_representation(self):
        """Test review __str__ method."""
        review = Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='Great!'
        )
        self.assertIn(self.user.email, str(review))
        self.assertIn('5', str(review))
    
    def test_unique_review_per_client_email(self):
        """Test that same client can't leave multiple reviews."""
        Review.objects.create(
            provider=self.provider,
            client_email='client@test.com',
            rating=5,
            comment='Great service'
        )
        
        # Try to create another review from same client
        with self.assertRaises((IntegrityError, ValidationError)):
            Review.objects.create(
                provider=self.provider,
                client_email='client@test.com',
                rating=3,
                comment='Changed my mind'
            )
    
    def test_multiple_reviews_different_clients(self):
        """Test multiple reviews from different clients."""
        review1 = Review.objects.create(
            provider=self.provider,
            client_email='client1@test.com',
            rating=5,
            comment='Excellent'
        )
        review2 = Review.objects.create(
            provider=self.provider,
            client_email='client2@test.com',
            rating=4,
            comment='Very good'
        )
        self.assertEqual(self.provider.reviews.count(), 2)
    
    def test_review_has_timestamp(self):
        """Test review has creation timestamp."""
        review = Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='Test'
        )
        self.assertIsNotNone(review.created_at)
