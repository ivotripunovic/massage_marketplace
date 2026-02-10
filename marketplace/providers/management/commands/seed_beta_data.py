"""Management command to seed beta test data for the marketplace.

Usage:
    python manage.py seed_beta_data
    python manage.py seed_beta_data --flush   # Clear existing seed data first
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from providers.models import Provider, Service, Country, City
from reviews.models import Review
from users.models import User


PROVIDERS_DATA = [
    {
        'email': 'sarah.johnson@example.com',
        'first_name': 'Sarah',
        'last_name': 'Johnson',
        'bio': 'Licensed Massage Therapist with 10 years of experience specialising in Swedish and deep tissue massage. I focus on relieving chronic pain and improving mobility.',
        'phone': '+44-20-7946-0101',
        'country_name': 'United Kingdom',
        'city_name': 'London',
        'services': [
            ('swedish', 'Relaxing full-body Swedish massage to improve circulation and reduce stress.', 80, 60),
            ('deep_tissue', 'Targeted deep tissue work for chronic pain relief and muscle recovery.', 100, 60),
            ('hot_stone', 'Warm stone therapy combined with deep pressure for total relaxation.', 120, 90),
        ],
    },
    {
        'email': 'michael.chen@example.com',
        'first_name': 'Michael',
        'last_name': 'Chen',
        'bio': 'Certified Thai massage practitioner trained in Chiang Mai, Thailand. I combine traditional Thai techniques with modern wellness approaches.',
        'phone': '+81-3-1234-5678',
        'country_name': 'Japan',
        'city_name': 'Tokyo',
        'services': [
            ('thai', 'Traditional Thai massage with gentle stretching and pressure point work.', 90, 60),
            ('reflexology', 'Therapeutic foot reflexology to restore balance and energy flow.', 55, 30),
            ('swedish', 'Gentle Swedish massage with Thai-inspired stretching elements.', 75, 60),
        ],
    },
    {
        'email': 'emma.wilson@example.com',
        'first_name': 'Emma',
        'last_name': 'Wilson',
        'bio': 'Holistic massage therapist offering aromatherapy and hot stone treatments. My goal is to create a healing environment for mind and body.',
        'phone': '+33-1-2345-6789',
        'country_name': 'France',
        'city_name': 'Paris',
        'services': [
            ('aromatherapy', 'Customised aromatherapy massage using premium essential oils.', 95, 60),
            ('hot_stone', 'Hot stone massage combining heat therapy with deep pressure techniques.', 110, 60),
            ('swedish', 'Gentle Swedish massage for stress relief and relaxation.', 70, 60),
        ],
    },
    {
        'email': 'david.martinez@example.com',
        'first_name': 'David',
        'last_name': 'Martinez',
        'bio': 'Sports massage specialist working with athletes and active individuals. I help optimise performance and speed up recovery.',
        'phone': '+55-11-9876-5432',
        'country_name': 'Brazil',
        'city_name': 'São Paulo',
        'services': [
            ('deep_tissue', 'Sports-focused deep tissue massage for athletes.', 85, 60),
            ('swedish', 'Recovery-focused Swedish massage for post-workout relaxation.', 70, 60),
        ],
    },
    {
        'email': 'lisa.patel@example.com',
        'first_name': 'Lisa',
        'last_name': 'Patel',
        'bio': 'Experienced reflexologist and aromatherapist. I believe in the power of touch to heal and restore. Serving clients in the Melbourne area for over 5 years.',
        'phone': '+61-3-9876-5432',
        'country_name': 'Australia',
        'city_name': 'Melbourne',
        'services': [
            ('reflexology', 'Full reflexology session focusing on feet and hands.', 60, 30),
            ('aromatherapy', 'Relaxing aromatherapy massage with essential oil blends.', 85, 60),
            ('hot_stone', 'Warm stone aromatherapy experience with hot towels.', 120, 90),
        ],
    },
]

REVIEWS_DATA = [
    # (provider_index, rating, client_name, comment)
    (0, 5, 'Alice B.', 'Sarah is amazing! My back pain is completely gone after just two sessions.'),
    (0, 4, 'Bob T.', 'Very professional and knowledgeable. The deep tissue massage was exactly what I needed.'),
    (0, 5, 'Carol M.', 'Best massage therapist I have ever visited. Highly recommend!'),
    (1, 5, 'Dan W.', 'Incredible Thai massage. Michael is very skilled and attentive.'),
    (1, 4, 'Eve S.', 'Great experience. The reflexology session was very relaxing.'),
    (2, 5, 'Frank J.', 'The aromatherapy massage was heavenly. Emma creates such a peaceful atmosphere.'),
    (2, 5, 'Grace L.', 'Hot stone massage was the best I have had. Will definitely return.'),
    (2, 4, 'Henry K.', 'Very professional. The essential oils she uses are top quality.'),
    (3, 4, 'Iris N.', 'David really knows sports massage. Helped my running injury tremendously.'),
    (3, 5, 'Jack P.', 'Perfect for post-workout recovery. Highly recommended for athletes.'),
    (4, 5, 'Karen R.', 'Lisa has magic hands. The reflexology session left me feeling so relaxed.'),
    (4, 4, 'Larry V.', 'Great aromatherapy experience. The essential oil blend was wonderful.'),
]


class Command(BaseCommand):
    help = 'Seed the database with beta test data (providers, services, reviews)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Remove existing seed data before creating new data',
        )

    def _ensure_fixtures_loaded(self):
        """Load location fixtures if Country table is empty."""
        if Country.objects.exists():
            return
        self.stdout.write('Loading location fixtures...')
        call_command('loaddata', '001_continents', verbosity=0)
        call_command('loaddata', '002_countries', verbosity=0)
        call_command('loaddata', '003_cities_europe', verbosity=0)
        call_command('loaddata', '004_cities_asia', verbosity=0)
        call_command('loaddata', '005_cities_africa', verbosity=0)
        call_command('loaddata', '006_cities_south_america', verbosity=0)
        call_command('loaddata', '007_cities_oceania', verbosity=0)
        self.stdout.write(self.style.SUCCESS('Location fixtures loaded.'))

    def _lookup_location(self, country_name, city_name):
        """Look up Country and City by name. Returns (country, city) or (None, None)."""
        try:
            country = Country.objects.get(name=country_name)
        except Country.DoesNotExist:
            self.stderr.write(self.style.WARNING(f'  Country not found: {country_name}'))
            return None, None

        city = None
        if city_name:
            try:
                city = City.objects.get(name=city_name, country=country)
            except City.DoesNotExist:
                self.stderr.write(self.style.WARNING(f'  City not found: {city_name} in {country_name}'))

        return country, city

    def handle(self, *args, **options):
        seed_emails = [p['email'] for p in PROVIDERS_DATA]

        if options['flush']:
            self.stdout.write('Removing existing seed data...')
            User.objects.filter(email__in=seed_emails).delete()
            self.stdout.write(self.style.SUCCESS('Seed data removed.'))

        self._ensure_fixtures_loaded()

        providers = []
        for data in PROVIDERS_DATA:
            if User.objects.filter(email=data['email']).exists():
                self.stdout.write(f"  Skipping {data['email']} (already exists)")
                provider = User.objects.get(email=data['email']).provider_profile
                providers.append(provider)
                continue

            country, city = self._lookup_location(
                data.get('country_name', ''),
                data.get('city_name', ''),
            )

            user = User.objects.create_user(
                email=data['email'],
                password='BetaTest123!',
                user_type='provider',
                is_email_verified=True,
                first_name=data['first_name'],
                last_name=data['last_name'],
            )

            provider = Provider.objects.create(
                user=user,
                bio=data['bio'],
                phone=data['phone'],
                country=country,
                city=city,
                subscription_status='active',
                subscription_payment_method='bank_transfer',
                subscription_renewal_date=timezone.now().date() + timedelta(days=30),
            )

            for stype, desc, price, duration in data['services']:
                Service.objects.create(
                    provider=provider,
                    service_type=stype,
                    description=desc,
                    price=Decimal(str(price)),
                    duration_minutes=duration,
                    is_active=True,
                )

            self.stdout.write(f"  Created provider: {data['first_name']} {data['last_name']} ({data['email']})")
            providers.append(provider)

        # Create reviews
        for provider_idx, rating, client_name, comment in REVIEWS_DATA:
            provider = providers[provider_idx]
            if Review.objects.filter(provider=provider, client_name=client_name).exists():
                continue
            Review.objects.create(
                provider=provider,
                rating=rating,
                client_name=client_name,
                comment=comment,
            )

        # Create admin user
        admin_email = 'admin@massagemarketplace.com'
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                password='AdminBeta123!',
                user_type='admin',
            )
            self.stdout.write(f"  Created admin: {admin_email}")

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Beta data seeded: {len(PROVIDERS_DATA)} providers, '
            f'{sum(len(p["services"]) for p in PROVIDERS_DATA)} services, '
            f'{len(REVIEWS_DATA)} reviews'
        ))
        # Seed gallery photos for providers
        self.stdout.write('')
        self.stdout.write('Seeding gallery photos...')
        call_command('seed_gallery_photos')

        self.stdout.write('')
        self.stdout.write('  Beta login credentials:')
        self.stdout.write(f'    Provider: {PROVIDERS_DATA[0]["email"]} / BetaTest123!')
        self.stdout.write(f'    Admin:    {admin_email} / AdminBeta123!')
