"""
Locust load test for Massage Marketplace.

Usage:
    # Install locust
    pip install locust

    # Seed test data first
    python marketplace/manage.py seed_beta_data

    # Run against local gunicorn (recommended over runserver)
    gunicorn marketplace.wsgi -w 4 --chdir marketplace &
    locust -f locustfile.py --host=http://localhost:8000

    # Then open http://localhost:8089 to configure users and start
"""

import re

from locust import HttpUser, between, task

# Pre-seeded test credentials (created by seed_beta_data)
CLIENT_EMAIL = "reviewer1@seed.local"
CLIENT_PASSWORD = "BetaTest123!"


def extract_csrf(response):
    """Extract CSRF token from a Django-rendered HTML page."""
    match = re.search(
        r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text
    )
    if match:
        return match.group(1)
    # Fallback: cookie
    return response.cookies.get("csrftoken", "")


class AnonymousBrowsingUser(HttpUser):
    """
    Simulates an unauthenticated visitor browsing the site.
    This is the most common user type — browsing providers, viewing profiles.
    """

    weight = 6  # 60% of traffic
    wait_time = between(2, 8)

    def on_start(self):
        # Collect some provider slugs for detail page visits
        self.provider_slugs = []
        self._discover_providers()

    def _discover_providers(self):
        """Scrape provider slugs from the homepage."""
        with self.client.get("/", catch_response=True) as resp:
            if resp.status_code == 200:
                slugs = re.findall(r'/providers/([\w-]+)/', resp.text)
                self.provider_slugs = list(set(slugs))[:20]
                resp.success()
            else:
                resp.failure(f"Homepage returned {resp.status_code}")

    @task(5)
    def browse_homepage(self):
        """Visit the main provider directory."""
        self.client.get("/")

    @task(3)
    def browse_with_pagination(self):
        """Browse page 2+ of provider listings."""
        self.client.get("/providers/?page=2")

    @task(4)
    def view_provider_detail(self):
        """View a specific provider's detail page."""
        if not self.provider_slugs:
            self._discover_providers()
            return
        import random

        slug = random.choice(self.provider_slugs)
        self.client.get(f"/providers/{slug}/", name="/providers/[slug]/")

    @task(2)
    def browse_with_keyword(self):
        """Search providers by keyword."""
        import random

        keywords = ["massage", "therapy", "relax", "deep tissue", "spa"]
        kw = random.choice(keywords)
        self.client.get(f"/providers/?keyword={kw}", name="/providers/?keyword=[kw]")

    @task(1)
    def view_legal_pages(self):
        """Occasionally visit legal/static pages."""
        import random

        page = random.choice(["/terms/", "/privacy/", "/payment-policy/"])
        self.client.get(page, name="/[legal-page]/")

    @task(1)
    def api_countries(self):
        """Hit the countries search API."""
        self.client.get("/api/countries/search/?all=1", name="/api/countries/search/")

    @task(1)
    def api_cities(self):
        """Hit the cities search API for a country."""
        self.client.get(
            "/api/cities/search/?country=1&all=1", name="/api/cities/search/"
        )


class AuthenticatedClientUser(HttpUser):
    """
    Simulates a logged-in client who browses, views profiles,
    updates their profile, and checks their reviews.
    """

    weight = 3  # 30% of traffic
    wait_time = between(3, 10)

    def on_start(self):
        self.provider_slugs = []
        self._login()
        self._discover_providers()

    def _login(self):
        """Log in as a seeded client user."""
        resp = self.client.get("/auth/login/")
        csrf = extract_csrf(resp)
        self.client.post(
            "/auth/login/",
            data={
                "email": CLIENT_EMAIL,
                "password": CLIENT_PASSWORD,
                "csrfmiddlewaretoken": csrf,
            },
            name="/auth/login/ [POST]",
        )

    def _discover_providers(self):
        resp = self.client.get("/")
        if resp.status_code == 200:
            slugs = re.findall(r'/providers/([\w-]+)/', resp.text)
            self.provider_slugs = list(set(slugs))[:20]

    @task(4)
    def browse_homepage(self):
        self.client.get("/")

    @task(4)
    def view_provider_detail(self):
        if not self.provider_slugs:
            self._discover_providers()
            return
        import random

        slug = random.choice(self.provider_slugs)
        self.client.get(f"/providers/{slug}/", name="/providers/[slug]/")

    @task(2)
    def view_my_profile(self):
        """Visit client profile page."""
        self.client.get("/client/profile/")

    @task(1)
    def update_profile(self):
        """Submit the client profile form."""
        resp = self.client.get("/client/profile/")
        csrf = extract_csrf(resp)
        self.client.post(
            "/client/profile/",
            data={
                "first_name": "LoadTest",
                "last_name": "User",
                "csrfmiddlewaretoken": csrf,
            },
            name="/client/profile/ [POST]",
        )

    @task(2)
    def view_my_reviews(self):
        """Check the client's review history."""
        self.client.get("/client/reviews/")


class ProviderDashboardUser(HttpUser):
    """
    Simulates a provider checking their dashboard.
    Requires a seeded provider account — update credentials below.
    """

    weight = 1  # 10% of traffic
    wait_time = between(5, 15)

    # Seeded provider account (created by seed_beta_data)
    PROVIDER_EMAIL = "provider0001@seed.example.com"
    PROVIDER_PASSWORD = "BetaTest123!"

    def on_start(self):
        self._login()

    def _login(self):
        resp = self.client.get("/auth/login/")
        csrf = extract_csrf(resp)
        self.client.post(
            "/auth/login/",
            data={
                "email": self.PROVIDER_EMAIL,
                "password": self.PROVIDER_PASSWORD,
                "csrfmiddlewaretoken": csrf,
            },
            name="/auth/login/ [POST]",
        )

    @task(3)
    def view_dashboard(self):
        self.client.get("/provider/dashboard/")

    @task(2)
    def view_profile(self):
        self.client.get("/provider/profile/")

    @task(1)
    def view_subscription(self):
        self.client.get("/provider/subscription/")
