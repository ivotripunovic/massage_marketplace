from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from users.models import User
from providers.models import Provider
from reviews.models import Review
from reviews.forms import ReviewForm


class ReviewFormTests(TestCase):
    """Tests for the ReviewForm."""

    def test_review_form_valid(self):
        """Test that form is valid with correct data."""
        form_data = {
            'rating': 5,
            'comment': 'Great service!',
            'client_name': 'John Doe',
            'client_email': 'john@example.com'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_review_form_rating_required(self):
        """Test that rating is required."""
        form_data = {
            'comment': 'Great service!',
            'client_email': 'john@example.com'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)

    def test_review_form_comment_required(self):
        """Test that comment is required."""
        form_data = {
            'rating': 5,
            'client_email': 'john@example.com'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)

    def test_review_form_email_required(self):
        """Test that email is required."""
        form_data = {
            'rating': 5,
            'comment': 'Great service!'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('client_email', form.errors)

    def test_review_form_comment_max_length(self):
        """Test that comment has max length of 250 characters."""
        form_data = {
            'rating': 5,
            'comment': 'x' * 251,
            'client_email': 'john@example.com'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)

    def test_review_form_client_name_optional(self):
        """Test that client name is optional."""
        form_data = {
            'rating': 5,
            'comment': 'Great service!',
            'client_email': 'john@example.com'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())


class ReviewSubmissionTests(TestCase):
    """Tests for review submission."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create provider
        self.user = User.objects.create_user(
            email='provider@example.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            subscription_status='active'
        )

    def test_submit_review_success(self):
        """Test successful review submission."""
        response = self.client.post(
            reverse('review_submit', kwargs={'slug': self.provider.user.email}),
            {
                'rating': 5,
                'comment': 'Great massage therapist!',
                'client_name': 'John Doe',
                'client_email': 'john@example.com'
            }
        )

        # Should redirect to provider detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('provider_detail', kwargs={'slug': self.provider.user.email})
        )

        # Review should be created
        self.assertEqual(Review.objects.filter(provider=self.provider).count(), 1)
        review = Review.objects.get(provider=self.provider)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Great massage therapist!')
        self.assertEqual(review.client_name, 'John Doe')
        self.assertEqual(review.client_email, 'john@example.com')

    def test_submit_review_anonymous(self):
        """Test anonymous review submission (no client name)."""
        response = self.client.post(
            reverse('review_submit', kwargs={'slug': self.provider.user.email}),
            {
                'rating': 4,
                'comment': 'Good service',
                'client_email': 'anonymous@example.com'
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertIsNone(review.client_name)
        self.assertEqual(review.client_email, 'anonymous@example.com')

    def test_submit_review_duplicate_prevention(self):
        """Test that duplicate reviews are prevented."""
        # First review
        Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='First review',
            client_email='john@example.com'
        )

        # Try to submit second review with same email
        response = self.client.post(
            reverse('review_submit', kwargs={'slug': self.provider.user.email}),
            {
                'rating': 4,
                'comment': 'Second review',
                'client_email': 'john@example.com'
            }
        )

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        # Still only one review
        self.assertEqual(Review.objects.filter(provider=self.provider).count(), 1)

    def test_submit_review_invalid_rating(self):
        """Test that invalid rating is rejected."""
        response = self.client.post(
            reverse('review_submit', kwargs={'slug': self.provider.user.email}),
            {
                'rating': 6,  # Invalid: must be 1-5
                'comment': 'Test',
                'client_email': 'test@example.com'
            }
        )

        # Should not create review
        self.assertEqual(Review.objects.count(), 0)

    def test_submit_review_missing_comment(self):
        """Test that missing comment is rejected."""
        response = self.client.post(
            reverse('review_submit', kwargs={'slug': self.provider.user.email}),
            {
                'rating': 5,
                'client_email': 'test@example.com'
            }
        )

        # Should not create review
        self.assertEqual(Review.objects.count(), 0)

    def test_submit_review_provider_not_found(self):
        """Test that submitting review for non-existent provider returns 404."""
        response = self.client.post(
            reverse('review_submit', kwargs={'slug': 'nonexistent@example.com'}),
            {
                'rating': 5,
                'comment': 'Test',
                'client_email': 'test@example.com'
            }
        )

        self.assertEqual(response.status_code, 404)

    @patch('django.core.mail.send_mail')
    def test_review_submission_sends_email(self, mock_send_mail):
        """Test that review submission sends email notification."""
        self.client.post(
            reverse('review_submit', kwargs={'slug': self.provider.user.email}),
            {
                'rating': 5,
                'comment': 'Great service!',
                'client_email': 'test@example.com'
            }
        )

        # Email should be sent
        self.assertTrue(mock_send_mail.called)
        args = mock_send_mail.call_args[0]
        self.assertIn('New Review Submitted', args[0])  # Subject

    @patch('django.core.mail.send_mail', side_effect=Exception('Email failed'))
    def test_review_submission_works_if_email_fails(self, mock_send_mail):
        """Test that review submission works even if email fails."""
        response = self.client.post(
            reverse('review_submit', kwargs={'slug': self.provider.user.email}),
            {
                'rating': 5,
                'comment': 'Great service!',
                'client_email': 'test@example.com'
            }
        )

        # Should still succeed
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 1)


class ReviewDisplayTests(TestCase):
    """Tests for review display on provider detail page."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create provider
        self.user = User.objects.create_user(
            email='provider@example.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            subscription_status='active'
        )

    def test_provider_detail_shows_reviews(self):
        """Test that provider detail page shows reviews."""
        # Create reviews
        Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='Excellent service!',
            client_name='John Doe'
        )
        Review.objects.create(
            provider=self.provider,
            rating=4,
            comment='Very good',
            client_name='Jane Smith'
        )

        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.provider.user.email})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Excellent service!')
        self.assertContains(response, 'Very good')
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Jane Smith')

    def test_provider_detail_shows_anonymous_review(self):
        """Test that anonymous reviews display correctly."""
        Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='Great!',
            client_email='anon@example.com'
        )

        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.provider.user.email})
        )

        self.assertContains(response, 'Great!')
        self.assertContains(response, 'Anonymous')

    def test_provider_detail_shows_no_reviews_message(self):
        """Test that page shows message when no reviews exist."""
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.provider.user.email})
        )

        self.assertContains(response, 'No reviews yet')

    def test_provider_detail_shows_review_form(self):
        """Test that review form is displayed on provider detail page."""
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.provider.user.email})
        )

        self.assertContains(response, 'Write a Review')
        self.assertContains(response, 'rating')
        self.assertContains(response, 'comment')
        self.assertContains(response, 'client_email')

    def test_reviews_ordered_by_newest_first(self):
        """Test that reviews are ordered by newest first."""
        from datetime import timedelta
        from django.utils import timezone

        # Create older review
        older_review = Review.objects.create(
            provider=self.provider,
            rating=4,
            comment='Older review'
        )
        older_review.created_at = timezone.now() - timedelta(days=5)
        older_review.save(update_fields=['created_at'])

        # Create newer review
        newer_review = Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='Newer review'
        )

        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.provider.user.email})
        )

        content = response.content.decode()
        newer_pos = content.find('Newer review')
        older_pos = content.find('Older review')

        # Newer should appear before older
        self.assertLess(newer_pos, older_pos)


class ReviewModelTests(TestCase):
    """Tests for Review model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='provider@example.com',
            password='testpass123',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )

    def test_review_string_representation(self):
        """Test review string representation."""
        review = Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='Great!'
        )

        str_repr = str(review)
        self.assertIn(self.provider.user.email, str_repr)
        self.assertIn('5 stars', str_repr)

    def test_review_validation_rating(self):
        """Test that invalid rating raises ValidationError."""
        from django.core.exceptions import ValidationError

        review = Review(
            provider=self.provider,
            rating=6,  # Invalid
            comment='Test'
        )

        with self.assertRaises(ValidationError):
            review.save()

    def test_review_validation_comment_length(self):
        """Test that long comment raises ValidationError."""
        from django.core.exceptions import ValidationError

        review = Review(
            provider=self.provider,
            rating=5,
            comment='x' * 251  # Too long
        )

        with self.assertRaises(ValidationError):
            review.save()
