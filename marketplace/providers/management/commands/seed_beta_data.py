"""Management command to seed beta test data for the marketplace.

Usage:
    python manage.py seed_beta_data              # 100 providers (default)
    python manage.py seed_beta_data --count 1000  # 1000 providers
    python manage.py seed_beta_data --flush       # Clear existing seed data first
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from providers.models import (
    Provider, Service, Country, City,
    ProviderAttributeDefinition, ProviderAttributeValue,
)
from reviews.models import Review
from users.models import User

# ── Name pools ────────────────────────────────────────────────────────────────

FIRST_NAMES_F = [
    'Sarah', 'Emma', 'Lisa', 'Anna', 'Maria', 'Elena', 'Sofia', 'Yuki',
    'Mei', 'Priya', 'Fatima', 'Amara', 'Leila', 'Nina', 'Anya', 'Clara',
    'Hana', 'Lucia', 'Ingrid', 'Olivia', 'Chloe', 'Aisha', 'Rosa', 'Freya',
    'Lena', 'Mila', 'Zara', 'Nadia', 'Julia', 'Camille', 'Bianca', 'Petra',
    'Sakura', 'Ines', 'Suri', 'Vera', 'Kaia', 'Dina', 'Ewa', 'Thea',
]

FIRST_NAMES_M = [
    'Michael', 'David', 'James', 'Marco', 'Kenji', 'Raj', 'Omar', 'Luca',
    'Erik', 'Andre', 'Carlos', 'Tomas', 'Pavel', 'Youssef', 'Leo', 'Felix',
    'Hugo', 'Mateo', 'Kai', 'Stefan', 'Ravi', 'Chen', 'Ivan', 'Andrei',
    'Jan', 'Noah', 'Oscar', 'Samir', 'Diego', 'Viktor', 'Lars', 'Abel',
    'Tariq', 'Bruno', 'Sven', 'Milo', 'Nico', 'Ari', 'Daan', 'Finn',
]

LAST_NAMES = [
    'Johnson', 'Chen', 'Wilson', 'Martinez', 'Patel', 'Müller', 'Rossi',
    'Tanaka', 'Santos', 'Kim', 'Ali', 'Petrov', 'Johansson', 'Da Silva',
    'Nguyen', 'Garcia', 'Schmidt', 'Moretti', 'Larsson', 'Oliveira',
    'Nakamura', 'Hansen', 'Kowalski', 'Dubois', 'Fischer', 'Berg',
    'Fernandez', 'Bianchi', 'Yamamoto', 'Novak', 'Reyes', 'Ivanov',
    'Costa', 'Eriksen', 'Laurent', 'Weber', 'Popov', 'Szabo', 'Pereira',
    'Jansen', 'Andersen', 'Volkov', 'Sato', 'Park', 'Ahmad', 'Torres',
    'Kato', 'Lindberg', 'Mancini', 'Roy',
]

# ── Bio templates ─────────────────────────────────────────────────────────────

BIO_TEMPLATES = [
    'Licensed Massage Therapist with {years} years of experience specialising in {specialty}. I focus on {focus}.',
    'Certified {specialty} practitioner with a passion for holistic wellness. {years} years helping clients achieve balance and relaxation.',
    'Experienced therapist offering {specialty} treatments. With {years} years in the field, I bring expertise and care to every session.',
    'Dedicated massage professional specialising in {specialty}. My {years} years of practice are focused on {focus}.',
    'Trained in {specialty} with {years} years of hands-on experience. I create a calm, healing space for every client.',
    'Holistic wellness practitioner with {years} years of expertise in {specialty}. My approach centres on {focus}.',
    'Professional massage therapist with {years} years in the industry. I specialise in {specialty} and am passionate about {focus}.',
    'Skilled bodywork therapist offering {specialty} treatments for {years} years. My goal is {focus}.',
]

SPECIALTIES = [
    'Swedish and deep tissue massage',
    'Thai massage and stretching techniques',
    'aromatherapy and essential oil treatments',
    'hot stone and thermal therapies',
    'sports massage and recovery',
    'reflexology and pressure point therapy',
    'deep tissue and myofascial release',
    'relaxation and stress-relief massage',
]

FOCUSES = [
    'relieving chronic pain and improving mobility',
    'helping clients manage stress and find relaxation',
    'restoring balance through therapeutic touch',
    'optimising athletic performance and recovery',
    'promoting overall wellness and vitality',
    'creating a healing environment for mind and body',
    'personalised treatment plans for every client',
    'combining traditional and modern techniques',
]

# ── Service descriptions ──────────────────────────────────────────────────────

SERVICE_DESCRIPTIONS = {
    'swedish': [
        'Relaxing full-body Swedish massage to improve circulation and reduce stress.',
        'Gentle Swedish massage for deep relaxation and tension relief.',
        'Classic Swedish technique with long, flowing strokes for total calm.',
        'Swedish massage combining gentle pressure with soothing movements.',
    ],
    'deep_tissue': [
        'Targeted deep tissue work for chronic pain relief and muscle recovery.',
        'Intensive deep tissue massage focusing on problem areas.',
        'Sports-focused deep tissue massage for athletes and active individuals.',
        'Deep pressure therapy to release tension and restore movement.',
    ],
    'thai': [
        'Traditional Thai massage with gentle stretching and pressure point work.',
        'Authentic Thai bodywork combining yoga-like stretches with acupressure.',
        'Thai massage to improve flexibility and energy flow.',
        'Ancient Thai techniques for full-body rejuvenation.',
    ],
    'reflexology': [
        'Therapeutic foot reflexology to restore balance and energy flow.',
        'Full reflexology session focusing on feet and hands.',
        'Precision reflexology targeting key pressure points for whole-body wellness.',
        'Relaxing reflexology to ease tension and promote natural healing.',
    ],
    'hot_stone': [
        'Warm stone therapy combined with deep pressure for total relaxation.',
        'Hot stone massage combining heat therapy with soothing techniques.',
        'Heated basalt stones placed on key points for deep muscle relief.',
        'Luxurious hot stone treatment for stress release and warmth.',
    ],
    'aromatherapy': [
        'Customised aromatherapy massage using premium essential oils.',
        'Relaxing aromatherapy massage with carefully blended essential oils.',
        'Aromatic essential oil massage tailored to your needs.',
        'Soothing aromatherapy experience with therapeutic-grade oils.',
    ],
}

SERVICE_TYPES = list(SERVICE_DESCRIPTIONS.keys())

# ── Review templates ──────────────────────────────────────────────────────────

REVIEW_COMMENTS_5 = [
    'Absolutely amazing experience! Best massage I have ever had.',
    'Incredibly skilled therapist. I felt completely renewed afterwards.',
    'Five stars without hesitation. Will definitely be returning.',
    'Outstanding technique and a wonderfully relaxing atmosphere.',
    'Fantastic session. My chronic pain has improved dramatically.',
    'Truly exceptional. Professional, attentive, and extremely skilled.',
    'The best therapist I have found. Highly recommend to everyone.',
    'Life-changing experience. I have been coming back every month.',
    'Perfect in every way. The treatment exceeded all expectations.',
    'Cannot say enough good things. An absolute gem of a therapist.',
]

REVIEW_COMMENTS_4 = [
    'Very professional and knowledgeable. Great experience overall.',
    'Really enjoyable session. Would happily recommend.',
    'Skilled therapist with a great technique. Minor scheduling hiccup but otherwise perfect.',
    'Excellent massage. The pressure was just right.',
    'Very relaxing treatment. Good communication throughout.',
    'Thoroughly enjoyed it. Will be booking again soon.',
    'Great technique and friendly manner. Solid experience.',
    'Left feeling much better. Quality service all around.',
]

REVIEW_COMMENTS_3 = [
    'Decent massage but nothing extraordinary. Competent therapist.',
    'Good session overall, though the room was a bit cold.',
    'Average experience. The technique was fine but lacked personalisation.',
    'Okay massage. Expected a bit more for the price.',
]

REVIEWER_FIRST_NAMES = [
    'Alice', 'Bob', 'Carol', 'Dan', 'Eve', 'Frank', 'Grace', 'Henry',
    'Iris', 'Jack', 'Karen', 'Larry', 'Mona', 'Nick', 'Olga', 'Pete',
    'Quinn', 'Ruth', 'Sam', 'Tina', 'Uma', 'Vince', 'Wendy', 'Xander',
    'Yara', 'Zach', 'Amy', 'Ben', 'Cleo', 'Drew', 'Elle', 'Gus',
]

# ── Seed email domain ─────────────────────────────────────────────────────────

SEED_EMAIL_DOMAIN = 'seed.example.com'


class Command(BaseCommand):
    help = 'Seed the database with beta test data (providers, services, reviews)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of providers to create (default: 100)',
        )
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

    def _build_cities_list(self):
        """Return list of (city, country) tuples from database."""
        return list(
            City.objects.select_related('country')
            .filter(country__is_active=True)
            .values_list('id', 'country_id')
        )

    def _generate_provider_data(self, index, rng, city_country_pairs):
        """Generate deterministic provider data for a given index."""
        is_female = rng.random() < 0.5
        first_name = rng.choice(FIRST_NAMES_F if is_female else FIRST_NAMES_M)
        last_name = rng.choice(LAST_NAMES)
        email = f'provider{index:04d}@{SEED_EMAIL_DOMAIN}'

        years = rng.randint(2, 20)
        bio = rng.choice(BIO_TEMPLATES).format(
            years=years,
            specialty=rng.choice(SPECIALTIES),
            focus=rng.choice(FOCUSES),
        )

        city_id, country_id = rng.choice(city_country_pairs)
        phone_digits = ''.join(str(rng.randint(0, 9)) for _ in range(10))
        phone = f'+{phone_digits[:2]}-{phone_digits[2:5]}-{phone_digits[5:]}'

        # 1-4 services, unique types
        num_services = rng.randint(1, 4)
        service_types = rng.sample(SERVICE_TYPES, min(num_services, len(SERVICE_TYPES)))
        services = []
        for stype in service_types:
            desc = rng.choice(SERVICE_DESCRIPTIONS[stype])
            base_price = rng.randint(30, 150)
            price = round(base_price / 5) * 5  # round to nearest 5
            price = max(price, 5)
            duration = rng.choice([30, 60, 60, 60, 90])  # weighted toward 60
            services.append((stype, desc, price, duration))

        return {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'bio': bio,
            'phone': phone,
            'country_id': country_id,
            'city_id': city_id,
            'services': services,
        }

    def _generate_attributes(self, rng, providers):
        """Generate attribute values for providers. Returns count created."""
        definitions = list(ProviderAttributeDefinition.objects.filter(is_active=True))
        if not definitions:
            return 0

        # Value generators keyed by attribute name
        generators = {
            'Height': lambda: str(rng.randint(155, 195)),       # cm
            'Weight': lambda: str(rng.randint(50, 95)),         # kg
            'Established at': lambda: str(rng.randint(2005, 2024)),
            'Working with eldery': lambda: rng.choice(['true', 'false']),
        }

        count = 0
        for provider in providers:
            # Each provider fills 3-4 attributes (or all if fewer exist)
            num_attrs = min(rng.randint(3, 4), len(definitions))
            chosen = rng.sample(definitions, num_attrs)
            for defn in chosen:
                if ProviderAttributeValue.objects.filter(
                    provider=provider, definition=defn
                ).exists():
                    continue

                gen = generators.get(defn.name)
                if gen:
                    value = gen()
                else:
                    # Fallback for unknown attributes
                    if defn.data_type == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
                        value = rng.choice(['true', 'false'])
                    elif defn.data_type == ProviderAttributeDefinition.DATA_TYPE_INTEGER:
                        value = str(rng.randint(1, 100))
                    else:
                        value = 'N/A'

                ProviderAttributeValue.objects.create(
                    provider=provider,
                    definition=defn,
                    value_text=value,
                )
                count += 1
        return count

    def _generate_reviews(self, rng, providers):
        """Generate reviews for providers. Returns count of reviews created."""
        count = 0
        for provider in providers:
            num_reviews = rng.choices([0, 1, 2, 3, 4, 5], weights=[10, 15, 25, 25, 15, 10])[0]
            for _ in range(num_reviews):
                rating = rng.choices([3, 4, 5], weights=[10, 30, 60])[0]
                if rating == 5:
                    comment = rng.choice(REVIEW_COMMENTS_5)
                elif rating == 4:
                    comment = rng.choice(REVIEW_COMMENTS_4)
                else:
                    comment = rng.choice(REVIEW_COMMENTS_3)

                reviewer = f'{rng.choice(REVIEWER_FIRST_NAMES)} {rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}.'

                Review.objects.create(
                    provider=provider,
                    rating=rating,
                    client_name=reviewer,
                    comment=comment,
                )
                count += 1
        return count

    def handle(self, *args, **options):
        count = options['count']
        rng = random.Random(42)  # deterministic seed for reproducibility

        if options['flush']:
            self.stdout.write('Removing existing seed data...')
            User.objects.filter(email__endswith=f'@{SEED_EMAIL_DOMAIN}').delete()
            User.objects.filter(email='admin@massagemarketplace.com').delete()
            self.stdout.write(self.style.SUCCESS('Seed data removed.'))

        self._ensure_fixtures_loaded()

        city_country_pairs = self._build_cities_list()
        if not city_country_pairs:
            self.stderr.write(self.style.ERROR('No cities found in database. Cannot seed providers.'))
            return

        self.stdout.write(f'Generating {count} providers...')

        providers = []
        created_count = 0
        service_count = 0

        for i in range(1, count + 1):
            data = self._generate_provider_data(i, rng, city_country_pairs)

            if User.objects.filter(email=data['email']).exists():
                provider = User.objects.get(email=data['email']).provider_profile
                providers.append(provider)
                continue

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
                country_id=data['country_id'],
                city_id=data['city_id'],
                subscription_status='active',
                subscription_payment_method=rng.choice(['bank_transfer', 'crypto']),
                subscription_renewal_date=timezone.now().date() + timedelta(days=rng.randint(1, 30)),
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
                service_count += 1

            providers.append(provider)
            created_count += 1

            if created_count % 50 == 0:
                self.stdout.write(f'  ... {created_count} providers created')

        self.stdout.write(f'  Created {created_count} providers with {service_count} services')

        # Generate reviews
        self.stdout.write('Generating reviews...')
        review_count = self._generate_reviews(rng, providers)
        self.stdout.write(f'  Created {review_count} reviews')

        # Generate provider attributes
        self.stdout.write('Generating provider attributes...')
        attr_count = self._generate_attributes(rng, providers)
        self.stdout.write(f'  Created {attr_count} attribute values')

        # Create admin user
        admin_email = 'admin@massagemarketplace.com'
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                password='AdminBeta123!',
                user_type='admin',
            )
            self.stdout.write(f'  Created admin: {admin_email}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Beta data seeded: {created_count} providers, '
            f'{service_count} services, {review_count} reviews, '
            f'{attr_count} attribute values'
        ))

        self.stdout.write('')
        self.stdout.write('  Beta login credentials:')
        self.stdout.write(f'    Provider: provider0001@{SEED_EMAIL_DOMAIN} / BetaTest123!')
        self.stdout.write(f'    Admin:    {admin_email} / AdminBeta123!')
