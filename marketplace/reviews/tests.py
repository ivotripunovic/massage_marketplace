from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from users.models import User
from providers.models import Provider
from reviews.models import Review, ReviewCategory, ReviewCategoryRating, ReviewReply
from reviews.forms import ReviewForm, ReviewReplyForm


class ReviewCategoryModelTests(TestCase):
    """Tests for ReviewCategory model."""

    def test_category_str(self):
        cat = ReviewCategory.objects.create(name="Professionalism")
        self.assertEqual(str(cat), "Professionalism")

    def test_category_ordering(self):
        ReviewCategory.objects.create(name="B Cat", display_order=2)
        ReviewCategory.objects.create(name="A Cat", display_order=1)
        cats = list(ReviewCategory.objects.values_list("name", flat=True))
        self.assertEqual(cats, ["A Cat", "B Cat"])


class ReviewModelTests(TestCase):
    """Tests for Review model."""

    def setUp(self):
        self.provider_user = User.objects.create_user(
            email="provider@example.com", password="testpass123", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890"
        )
        self.client_user = User.objects.create_user(
            email="client@example.com", password="testpass123", user_type="client"
        )

    def test_review_str(self):
        review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Great!"
        )
        self.assertIn("client@example.com", str(review))
        self.assertIn("provider@example.com", str(review))

    def test_review_unique_constraint(self):
        from django.core.exceptions import ValidationError

        Review.objects.create(
            provider=self.provider, client=self.client_user, comment="First"
        )
        with self.assertRaises(ValidationError):
            Review.objects.create(
                provider=self.provider, client=self.client_user, comment="Second"
            )

    def test_review_comment_max_length(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            Review.objects.create(
                provider=self.provider, client=self.client_user, comment="x" * 251
            )

    def test_review_average_rating(self):
        review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Test"
        )
        cat1 = ReviewCategory.objects.create(name="Cat1")
        cat2 = ReviewCategory.objects.create(name="Cat2")
        ReviewCategoryRating.objects.create(review=review, category=cat1, rating=5)
        ReviewCategoryRating.objects.create(review=review, category=cat2, rating=3)
        self.assertEqual(review.average_rating(), 4.0)

    def test_review_average_rating_no_ratings(self):
        review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Test"
        )
        self.assertEqual(review.average_rating(), 0)


class ReviewCategoryRatingTests(TestCase):
    """Tests for ReviewCategoryRating model."""

    def setUp(self):
        self.provider_user = User.objects.create_user(
            email="provider@example.com", password="testpass123", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890"
        )
        self.client_user = User.objects.create_user(
            email="client@example.com", password="testpass123", user_type="client"
        )
        self.review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Test"
        )
        self.category = ReviewCategory.objects.create(name="Quality")

    def test_category_rating_str(self):
        cr = ReviewCategoryRating.objects.create(
            review=self.review, category=self.category, rating=5
        )
        self.assertIn("Quality", str(cr))
        self.assertIn("5", str(cr))

    def test_unique_together(self):
        from django.db import IntegrityError

        ReviewCategoryRating.objects.create(
            review=self.review, category=self.category, rating=5
        )
        with self.assertRaises(IntegrityError):
            ReviewCategoryRating.objects.create(
                review=self.review, category=self.category, rating=3
            )


class ReviewReplyModelTests(TestCase):
    """Tests for ReviewReply model."""

    def setUp(self):
        self.provider_user = User.objects.create_user(
            email="provider@example.com", password="testpass123", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890"
        )
        self.client_user = User.objects.create_user(
            email="client@example.com", password="testpass123", user_type="client"
        )
        self.review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Test"
        )

    def test_reply_str(self):
        reply = ReviewReply.objects.create(review=self.review, comment="Thanks!")
        self.assertIn("Reply to", str(reply))

    def test_one_reply_per_review(self):
        from django.db import IntegrityError

        ReviewReply.objects.create(review=self.review, comment="Thanks!")
        with self.assertRaises(IntegrityError):
            ReviewReply.objects.create(review=self.review, comment="Second reply")


class ReviewFormTests(TestCase):
    """Tests for the ReviewForm."""

    def setUp(self):
        self.cat1 = ReviewCategory.objects.create(name="Quality", display_order=1)
        self.cat2 = ReviewCategory.objects.create(name="Atmosphere", display_order=2)

    def test_form_has_category_fields(self):
        form = ReviewForm()
        self.assertIn(f"category_{self.cat1.pk}", form.fields)
        self.assertIn(f"category_{self.cat2.pk}", form.fields)

    def test_form_valid_with_one_category(self):
        form = ReviewForm(
            data={
                "comment": "Great service!",
                f"category_{self.cat1.pk}": 5,
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_valid_with_all_categories(self):
        form = ReviewForm(
            data={
                "comment": "Great service!",
                f"category_{self.cat1.pk}": 5,
                f"category_{self.cat2.pk}": 4,
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid_no_categories(self):
        form = ReviewForm(data={"comment": "Great service!"})
        self.assertFalse(form.is_valid())

    def test_form_comment_required(self):
        form = ReviewForm(data={f"category_{self.cat1.pk}": 5})
        self.assertFalse(form.is_valid())
        self.assertIn("comment", form.errors)

    def test_form_comment_max_length(self):
        form = ReviewForm(
            data={
                "comment": "x" * 251,
                f"category_{self.cat1.pk}": 5,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("comment", form.errors)

    def test_form_category_fields_list(self):
        form = ReviewForm()
        self.assertEqual(len(form.category_fields), 2)
        self.assertEqual(form.category_fields[0]["category"], self.cat1)


class ReviewReplyFormTests(TestCase):
    """Tests for the ReviewReplyForm."""

    def test_valid_reply(self):
        form = ReviewReplyForm(data={"comment": "Thank you!"})
        self.assertTrue(form.is_valid())

    def test_empty_reply_invalid(self):
        form = ReviewReplyForm(data={"comment": ""})
        self.assertFalse(form.is_valid())


class ReviewSubmissionTests(TestCase):
    """Tests for review submission."""

    def setUp(self):
        self.http_client = Client()
        self.provider_user = User.objects.create_user(
            email="provider@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.provider_user,
            phone="+1234567890",
            subscription_status="active",
        )
        self.client_user = User.objects.create_user(
            email="client@example.com",
            password="testpass123",
            user_type="client",
            is_email_verified=True,
        )
        self.cat = ReviewCategory.objects.create(name="Quality")

    def _submit_url(self):
        return reverse("review_submit", kwargs={"slug": self.provider.slug})

    def _detail_url(self):
        return reverse("provider_detail", kwargs={"slug": self.provider.slug})

    def test_unauthenticated_redirects_to_login(self):
        response = self.http_client.post(
            self._submit_url(),
            {"comment": "Great!", f"category_{self.cat.pk}": 5},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_submit_review_success(self):
        self.http_client.login(email="client@example.com", password="testpass123")
        response = self.http_client.post(
            self._submit_url(),
            {"comment": "Great massage!", f"category_{self.cat.pk}": 5},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.filter(provider=self.provider).count(), 1)
        review = Review.objects.get(provider=self.provider)
        self.assertEqual(review.client, self.client_user)
        self.assertEqual(review.comment, "Great massage!")
        self.assertEqual(review.category_ratings.count(), 1)
        self.assertEqual(review.category_ratings.first().rating, 5)

    def test_provider_cannot_review(self):
        self.http_client.login(email="provider@example.com", password="testpass123")
        response = self.http_client.post(
            self._submit_url(),
            {"comment": "Self review", f"category_{self.cat.pk}": 5},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 0)

    def test_duplicate_review_prevented(self):
        Review.objects.create(
            provider=self.provider, client=self.client_user, comment="First"
        )
        self.http_client.login(email="client@example.com", password="testpass123")
        response = self.http_client.post(
            self._submit_url(),
            {"comment": "Second", f"category_{self.cat.pk}": 5},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.filter(provider=self.provider).count(), 1)

    def test_invalid_form_redirects_with_error(self):
        self.http_client.login(email="client@example.com", password="testpass123")
        response = self.http_client.post(
            self._submit_url(),
            {"comment": ""},  # missing category and empty comment
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 0)

    def test_nonexistent_provider_returns_404(self):
        self.http_client.login(email="client@example.com", password="testpass123")
        response = self.http_client.post(
            reverse("review_submit", kwargs={"slug": "nonexistent-999"}),
            {"comment": "Test", f"category_{self.cat.pk}": 5},
        )
        self.assertEqual(response.status_code, 404)

    @patch("django.core.mail.send_mail")
    def test_submission_sends_email(self, mock_send_mail):
        self.http_client.login(email="client@example.com", password="testpass123")
        self.http_client.post(
            self._submit_url(),
            {"comment": "Great!", f"category_{self.cat.pk}": 5},
        )
        self.assertTrue(mock_send_mail.called)

    @patch("django.core.mail.send_mail", side_effect=Exception("fail"))
    def test_submission_works_if_email_fails(self, mock_send_mail):
        self.http_client.login(email="client@example.com", password="testpass123")
        response = self.http_client.post(
            self._submit_url(),
            {"comment": "Great!", f"category_{self.cat.pk}": 5},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 1)


class ReviewReplyViewTests(TestCase):
    """Tests for ReviewReplyView."""

    def setUp(self):
        self.http_client = Client()
        self.provider_user = User.objects.create_user(
            email="provider@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.provider_user,
            phone="+1234567890",
            subscription_status="active",
        )
        self.client_user = User.objects.create_user(
            email="client@example.com",
            password="testpass123",
            user_type="client",
        )
        self.review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Nice!"
        )

    def _reply_url(self):
        return reverse(
            "review_reply",
            kwargs={"slug": self.provider.slug, "pk": self.review.pk},
        )

    def test_provider_can_reply(self):
        self.http_client.login(email="provider@example.com", password="testpass123")
        response = self.http_client.post(self._reply_url(), {"comment": "Thank you!"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ReviewReply.objects.filter(review=self.review).exists())

    def test_other_user_cannot_reply(self):
        self.http_client.login(email="client@example.com", password="testpass123")
        response = self.http_client.post(self._reply_url(), {"comment": "Not allowed"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ReviewReply.objects.exists())

    def test_unauthenticated_redirects(self):
        response = self.http_client.post(self._reply_url(), {"comment": "Anon reply"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_cannot_reply_twice(self):
        ReviewReply.objects.create(review=self.review, comment="First reply")
        self.http_client.login(email="provider@example.com", password="testpass123")
        response = self.http_client.post(self._reply_url(), {"comment": "Second reply"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReviewReply.objects.filter(review=self.review).count(), 1)

    def test_get_not_allowed(self):
        self.http_client.login(email="provider@example.com", password="testpass123")
        response = self.http_client.get(self._reply_url())
        self.assertEqual(response.status_code, 405)


class ReviewDisplayTests(TestCase):
    """Tests for review display on provider detail page."""

    def setUp(self):
        self.http_client = Client()
        self.provider_user = User.objects.create_user(
            email="provider@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.provider_user,
            phone="+1234567890",
            subscription_status="active",
        )
        self.client_user = User.objects.create_user(
            email="client@example.com",
            password="testpass123",
            user_type="client",
            first_name="Jane",
        )

    def _detail_url(self):
        return reverse("provider_detail", kwargs={"slug": self.provider.slug})

    def test_shows_review_with_category_ratings(self):
        cat = ReviewCategory.objects.create(name="Professionalism")
        review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Excellent!"
        )
        ReviewCategoryRating.objects.create(review=review, category=cat, rating=5)
        response = self.http_client.get(self._detail_url())
        self.assertContains(response, "Excellent!")
        self.assertContains(response, "Professionalism")
        self.assertContains(response, "Jane")

    def test_shows_client_fallback_name(self):
        self.client_user.first_name = ""
        self.client_user.save()
        Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Good"
        )
        response = self.http_client.get(self._detail_url())
        self.assertContains(response, "Client")

    def test_shows_provider_reply(self):
        review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Nice"
        )
        ReviewReply.objects.create(review=review, comment="Thanks for the review!")
        response = self.http_client.get(self._detail_url())
        self.assertContains(response, "Thanks for the review!")
        self.assertContains(response, "Provider Reply")

    def test_no_reviews_message(self):
        response = self.http_client.get(self._detail_url())
        self.assertContains(response, "No reviews yet")

    def test_unauthenticated_sees_login_prompt(self):
        response = self.http_client.get(self._detail_url())
        self.assertContains(response, "Log in")

    def test_provider_sees_clients_only_message(self):
        self.http_client.login(email="provider@example.com", password="testpass123")
        response = self.http_client.get(self._detail_url())
        self.assertContains(response, "Only clients can leave reviews")

    def test_client_who_reviewed_sees_already_reviewed(self):
        Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Done"
        )
        self.http_client.login(email="client@example.com", password="testpass123")
        response = self.http_client.get(self._detail_url())
        self.assertContains(response, "already reviewed")

    def test_client_sees_review_form(self):
        self.http_client.login(email="client@example.com", password="testpass123")
        response = self.http_client.get(self._detail_url())
        self.assertContains(response, "Write a Review")
        self.assertContains(response, "Submit Review")

    def test_reviews_ordered_newest_first(self):
        from datetime import timedelta
        from django.utils import timezone

        client2 = User.objects.create_user(
            email="client2@example.com", password="testpass123", user_type="client"
        )
        older = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Older review"
        )
        Review.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=5)
        )
        Review.objects.create(
            provider=self.provider, client=client2, comment="Newer review"
        )
        response = self.http_client.get(self._detail_url())
        content = response.content.decode()
        self.assertLess(content.find("Newer review"), content.find("Older review"))

    def test_provider_sees_reply_form(self):
        """Provider should see reply form for unreplied reviews."""
        review = Review.objects.create(
            provider=self.provider, client=self.client_user, comment="Review"
        )
        self.http_client.login(email="provider@example.com", password="testpass123")
        response = self.http_client.get(self._detail_url())
        reply_url = reverse(
            "review_reply",
            kwargs={"slug": self.provider.slug, "pk": review.pk},
        )
        self.assertContains(response, reply_url)
