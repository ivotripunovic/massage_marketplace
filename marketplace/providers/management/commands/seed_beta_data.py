"""Management command to seed beta test data for the marketplace.

Usage:
    python manage.py seed_beta_data              # 100 providers (default)
    python manage.py seed_beta_data --count 1000  # 1000 providers
    python manage.py seed_beta_data --flush       # Clear existing seed data first
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from providers.models import (
    Provider,
    Country,
    City,
    ProviderAttributeDefinition,
    ProviderAttributeValue,
    ProviderPricing,
    PreferenceGroup,
    PreferenceSubgroup,
    PreferenceSubgroupOption,
    ProviderPreference,
    ProviderPreferenceCustomOption,
    ProviderCustomPreference,
)
from reviews.models import Review, ReviewCategory, ReviewCategoryRating
from users.models import User

# ── Name pools ────────────────────────────────────────────────────────────────

FIRST_NAMES_F = [
    "Sarah",
    "Emma",
    "Lisa",
    "Anna",
    "Maria",
    "Elena",
    "Sofia",
    "Yuki",
    "Mei",
    "Priya",
    "Fatima",
    "Amara",
    "Leila",
    "Nina",
    "Anya",
    "Clara",
    "Hana",
    "Lucia",
    "Ingrid",
    "Olivia",
    "Chloe",
    "Aisha",
    "Rosa",
    "Freya",
    "Lena",
    "Mila",
    "Zara",
    "Nadia",
    "Julia",
    "Camille",
    "Bianca",
    "Petra",
    "Sakura",
    "Ines",
    "Suri",
    "Vera",
    "Kaia",
    "Dina",
    "Ewa",
    "Thea",
]

FIRST_NAMES_M = [
    "Michael",
    "David",
    "James",
    "Marco",
    "Kenji",
    "Raj",
    "Omar",
    "Luca",
    "Erik",
    "Andre",
    "Carlos",
    "Tomas",
    "Pavel",
    "Youssef",
    "Leo",
    "Felix",
    "Hugo",
    "Mateo",
    "Kai",
    "Stefan",
    "Ravi",
    "Chen",
    "Ivan",
    "Andrei",
    "Jan",
    "Noah",
    "Oscar",
    "Samir",
    "Diego",
    "Viktor",
    "Lars",
    "Abel",
    "Tariq",
    "Bruno",
    "Sven",
    "Milo",
    "Nico",
    "Ari",
    "Daan",
    "Finn",
]

LAST_NAMES = [
    "Johnson",
    "Chen",
    "Wilson",
    "Martinez",
    "Patel",
    "Müller",
    "Rossi",
    "Tanaka",
    "Santos",
    "Kim",
    "Ali",
    "Petrov",
    "Johansson",
    "Da Silva",
    "Nguyen",
    "Garcia",
    "Schmidt",
    "Moretti",
    "Larsson",
    "Oliveira",
    "Nakamura",
    "Hansen",
    "Kowalski",
    "Dubois",
    "Fischer",
    "Berg",
    "Fernandez",
    "Bianchi",
    "Yamamoto",
    "Novak",
    "Reyes",
    "Ivanov",
    "Costa",
    "Eriksen",
    "Laurent",
    "Weber",
    "Popov",
    "Szabo",
    "Pereira",
    "Jansen",
    "Andersen",
    "Volkov",
    "Sato",
    "Park",
    "Ahmad",
    "Torres",
    "Kato",
    "Lindberg",
    "Mancini",
    "Roy",
]

# ── Bio templates ─────────────────────────────────────────────────────────────

BIO_TEMPLATES = [
    "Licensed Massage Therapist with {years} years of experience specialising in {specialty}. I focus on {focus}.",
    "Certified {specialty} practitioner with a passion for holistic wellness. {years} years helping clients achieve balance and relaxation.",
    "Experienced therapist offering {specialty} treatments. With {years} years in the field, I bring expertise and care to every session.",
    "Dedicated massage professional specialising in {specialty}. My {years} years of practice are focused on {focus}.",
    "Trained in {specialty} with {years} years of hands-on experience. I create a calm, healing space for every client.",
    "Holistic wellness practitioner with {years} years of expertise in {specialty}. My approach centres on {focus}.",
    "Professional massage therapist with {years} years in the industry. I specialise in {specialty} and am passionate about {focus}.",
    "Skilled bodywork therapist offering {specialty} treatments for {years} years. My goal is {focus}.",
]

SPECIALTIES = [
    "Swedish and deep tissue massage",
    "Thai massage and stretching techniques",
    "aromatherapy and essential oil treatments",
    "hot stone and thermal therapies",
    "sports massage and recovery",
    "reflexology and pressure point therapy",
    "deep tissue and myofascial release",
    "relaxation and stress-relief massage",
]

FOCUSES = [
    "relieving chronic pain and improving mobility",
    "helping clients manage stress and find relaxation",
    "restoring balance through therapeutic touch",
    "optimising athletic performance and recovery",
    "promoting overall wellness and vitality",
    "creating a healing environment for mind and body",
    "personalised treatment plans for every client",
    "combining traditional and modern techniques",
]

# ── Review templates ──────────────────────────────────────────────────────────

REVIEW_COMMENTS_5 = [
    "Absolutely amazing experience! Best massage I have ever had.",
    "Incredibly skilled therapist. I felt completely renewed afterwards.",
    "Five stars without hesitation. Will definitely be returning.",
    "Outstanding technique and a wonderfully relaxing atmosphere.",
    "Fantastic session. My chronic pain has improved dramatically.",
    "Truly exceptional. Professional, attentive, and extremely skilled.",
    "The best therapist I have found. Highly recommend to everyone.",
    "Life-changing experience. I have been coming back every month.",
    "Perfect in every way. The treatment exceeded all expectations.",
    "Cannot say enough good things. An absolute gem of a therapist.",
]

REVIEW_COMMENTS_4 = [
    "Very professional and knowledgeable. Great experience overall.",
    "Really enjoyable session. Would happily recommend.",
    "Skilled therapist with a great technique. Minor scheduling hiccup but otherwise perfect.",
    "Excellent massage. The pressure was just right.",
    "Very relaxing treatment. Good communication throughout.",
    "Thoroughly enjoyed it. Will be booking again soon.",
    "Great technique and friendly manner. Solid experience.",
    "Left feeling much better. Quality service all around.",
]

REVIEW_COMMENTS_3 = [
    "Decent massage but nothing extraordinary. Competent therapist.",
    "Good session overall, though the room was a bit cold.",
    "Average experience. The technique was fine but lacked personalisation.",
    "Okay massage. Expected a bit more for the price.",
]

REVIEWER_FIRST_NAMES = [
    "Alice",
    "Bob",
    "Carol",
    "Dan",
    "Eve",
    "Frank",
    "Grace",
    "Henry",
    "Iris",
    "Jack",
    "Karen",
    "Larry",
    "Mona",
    "Nick",
    "Olga",
    "Pete",
    "Quinn",
    "Ruth",
    "Sam",
    "Tina",
    "Uma",
    "Vince",
    "Wendy",
    "Xander",
    "Yara",
    "Zach",
    "Amy",
    "Ben",
    "Cleo",
    "Drew",
    "Elle",
    "Gus",
]

# ── Review categories ────────────────────────────────────────────────────────

SEED_REVIEW_CATEGORIES = [
    {"name": "Professionalism", "display_order": 1},
    {"name": "Skill & Technique", "display_order": 2},
    {"name": "Communication", "display_order": 3},
    {"name": "Cleanliness & Hygiene", "display_order": 4},
    {"name": "Value for Money", "display_order": 5},
]

# ── Seed email domain ─────────────────────────────────────────────────────────

SEED_EMAIL_DOMAIN = "seed.example.com"

# ── Provider attribute definitions to seed ────────────────────────────────────

SEED_ATTRIBUTE_DEFINITIONS = [
    {"name": "Height", "data_type": "int", "display_order": 1, "show_on_card": True},
    {"name": "Weight", "data_type": "int", "display_order": 2, "show_on_card": True},
    {
        "name": "District",
        "data_type": "string",
        "display_order": 3,
        "show_on_card": False,
    },
    {"name": "Age", "data_type": "int", "display_order": 4, "show_on_card": True},
    {"name": "Breasts", "data_type": "int", "display_order": 5, "show_on_card": True},
    {
        "name": "Size of clothing",
        "data_type": "int",
        "display_order": 6,
        "show_on_card": False,
    },
    {
        "name": "Size of shoes",
        "data_type": "int",
        "display_order": 7,
        "show_on_card": False,
    },
    {
        "name": "Intimate haircut",
        "data_type": "string",
        "display_order": 8,
        "show_on_card": False,
    },
    {
        "name": "Body Art",
        "data_type": "string",
        "display_order": 9,
        "show_on_card": False,
    },
    {
        "name": "Not younger",
        "data_type": "int",
        "display_order": 10,
        "show_on_card": False,
    },
    {
        "name": "Not older",
        "data_type": "int",
        "display_order": 11,
        "show_on_card": False,
    },
]

# ── Preference group definitions to seed ──────────────────────────────────────

SEED_PREFERENCE_GROUPS = [
    {
        "name": "Massage",
        "display_order": 1,
        "subgroups": [
            {"name": "Classical", "options": []},
            {"name": "Erotic", "options": ["+10$ for 30min more"]},
            {"name": "Relaxing", "options": []},
            {"name": "Thai", "options": []},
            {"name": "Tantric", "options": ["+20$ surcharge"]},
            {"name": "Nuru", "options": ["+15$ gel included"]},
        ],
    },
    {
        "name": "Extra Services",
        "display_order": 2,
        "subgroups": [
            {"name": "Sauna", "options": ["Available on request"]},
            {"name": "Jacuzzi", "options": ["Available on request"]},
            {"name": "Shower together", "options": []},
            {"name": "Couples", "options": ["+50% for second person"]},
        ],
    },
    {
        "name": "Body Type",
        "display_order": 3,
        "subgroups": [
            {"name": "Slim", "options": []},
            {"name": "Athletic", "options": []},
            {"name": "Curvy", "options": []},
            {"name": "Plus size", "options": []},
        ],
    },
    {
        "name": "Meeting Place",
        "display_order": 4,
        "subgroups": [
            {"name": "My apartment", "options": []},
            {"name": "Your place", "options": ["+20$ travel fee"]},
            {"name": "Hotel", "options": ["+10$ travel fee"]},
            {"name": "Office", "options": []},
        ],
    },
    {
        "name": "Languages",
        "display_order": 5,
        "subgroups": [
            {"name": "English", "options": []},
            {"name": "German", "options": []},
            {"name": "French", "options": []},
            {"name": "Spanish", "options": []},
            {"name": "Russian", "options": []},
        ],
    },
]

# ── Bulk-create batch size ────────────────────────────────────────────────────

BATCH_SIZE = 500


class Command(BaseCommand):
    help = "Seed the database with beta test data (providers, reviews, pricing)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of providers to create (default: 100)",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Remove existing seed data before creating new data",
        )

    def _ensure_fixtures_loaded(self):
        """Load location fixtures if Country table is empty."""
        if Country.objects.exists():
            return
        self.stdout.write("Loading location fixtures...")
        call_command("loaddata", "001_continents", verbosity=0)
        call_command("loaddata", "002_countries", verbosity=0)
        call_command("loaddata", "003_cities_europe", verbosity=0)
        call_command("loaddata", "004_cities_asia", verbosity=0)
        call_command("loaddata", "005_cities_africa", verbosity=0)
        call_command("loaddata", "006_cities_south_america", verbosity=0)
        call_command("loaddata", "007_cities_oceania", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Location fixtures loaded."))

    def _build_cities_list(self):
        """Return list of (city, country) tuples from database."""
        return list(
            City.objects.select_related("country")
            .filter(country__is_active=True)
            .values_list("id", "country_id")
        )

    def _generate_provider_data(self, index, rng, city_country_pairs):
        """Generate deterministic provider data for a given index."""
        is_female = rng.random() < 0.5
        first_name = rng.choice(FIRST_NAMES_F if is_female else FIRST_NAMES_M)
        last_name = rng.choice(LAST_NAMES)
        email = f"provider{index:04d}@{SEED_EMAIL_DOMAIN}"

        years = rng.randint(2, 20)
        bio = rng.choice(BIO_TEMPLATES).format(
            years=years,
            specialty=rng.choice(SPECIALTIES),
            focus=rng.choice(FOCUSES),
        )

        city_id, country_id = rng.choice(city_country_pairs)
        phone_digits = "".join(str(rng.randint(0, 9)) for _ in range(10))
        phone = f"+{phone_digits[:2]}-{phone_digits[2:5]}-{phone_digits[5:]}"

        hour_start = rng.choice([8, 9, 10, 11])
        hour_end = rng.choice([17, 18, 19, 20])
        phone_hours = f"{hour_start}:00 – {hour_end}:00"

        return {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "bio": bio,
            "phone": phone,
            "phone_hours": phone_hours,
            "country_id": country_id,
            "city_id": city_id,
            "payment_method": rng.choice(["bank_transfer", "crypto"]),
            "renewal_days": rng.randint(1, 30),
        }

    def _ensure_review_categories(self):
        """Create review categories if they don't exist. Returns list of categories."""
        categories = []
        for cat_data in SEED_REVIEW_CATEGORIES:
            cat, _ = ReviewCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults={"display_order": cat_data["display_order"]},
            )
            categories.append(cat)
        return categories

    def _generate_reviews(self, rng, providers, hashed_password):
        """Generate reviews for providers using bulk_create. Returns count."""
        categories = self._ensure_review_categories()

        # Skip providers that already have seed reviews
        existing_reviewed = set(
            Review.objects.filter(
                client__email__endswith="@seed.local", provider__in=providers
            ).values_list("provider_id", flat=True)
        )

        # First pass: collect review data and build client User objects
        review_plan = []  # list of (provider, comment, base_rating, reviewer_first)
        client_idx = 0
        for provider in providers:
            if provider.pk in existing_reviewed:
                continue
            num_reviews = rng.choices(
                [0, 1, 2, 3, 4, 5], weights=[10, 15, 25, 25, 15, 10]
            )[0]
            for _ in range(num_reviews):
                base_rating = rng.choices([3, 4, 5], weights=[10, 30, 60])[0]
                if base_rating == 5:
                    comment = rng.choice(REVIEW_COMMENTS_5)
                elif base_rating == 4:
                    comment = rng.choice(REVIEW_COMMENTS_4)
                else:
                    comment = rng.choice(REVIEW_COMMENTS_3)

                client_idx += 1
                review_plan.append(
                    {
                        "provider": provider,
                        "comment": comment,
                        "base_rating": base_rating,
                        "client_email": f"reviewer{client_idx}@seed.local",
                        "client_first": rng.choice(REVIEWER_FIRST_NAMES),
                    }
                )

        if not review_plan:
            return 0

        # Bulk-create client users
        client_users = [
            User(
                email=User.objects.normalize_email(r["client_email"]),
                password=hashed_password,
                user_type="client",
                first_name=r["client_first"],
                is_email_verified=True,
            )
            for r in review_plan
        ]
        User.objects.bulk_create(client_users, batch_size=BATCH_SIZE)

        # Bulk-create reviews (bypass full_clean — data is controlled)
        review_objects = [
            Review(
                provider=r["provider"],
                client=client_user,
                comment=r["comment"],
            )
            for r, client_user in zip(review_plan, client_users)
        ]
        Review.objects.bulk_create(review_objects, batch_size=BATCH_SIZE)

        # Bulk-create category ratings
        rating_objects = []
        for r, review in zip(review_plan, review_objects):
            for cat in categories:
                cat_rating = max(1, min(5, r["base_rating"] + rng.randint(-1, 1)))
                rating_objects.append(
                    ReviewCategoryRating(review=review, category=cat, rating=cat_rating)
                )
        ReviewCategoryRating.objects.bulk_create(rating_objects, batch_size=BATCH_SIZE)

        return len(review_objects)

    def _ensure_attribute_definitions(self):
        """Create provider attribute definitions if they don't already exist."""
        created = 0
        for defn_data in SEED_ATTRIBUTE_DEFINITIONS:
            _, was_created = ProviderAttributeDefinition.objects.get_or_create(
                name=defn_data["name"],
                defaults={
                    "data_type": defn_data["data_type"],
                    "display_order": defn_data["display_order"],
                    "show_on_card": defn_data["show_on_card"],
                },
            )
            if was_created:
                created += 1
        return created

    def _generate_attributes(self, rng, providers):
        """Generate attribute values for providers via bulk_create. Returns count."""
        definitions = list(ProviderAttributeDefinition.objects.filter(is_active=True))
        if not definitions:
            return 0

        # Required attributes (show_on_card=True) must always be filled
        required_defs = [d for d in definitions if d.show_on_card]
        optional_defs = [d for d in definitions if not d.show_on_card]

        # Pre-fetch all existing attribute values for these providers in one query
        existing_pairs = set(
            ProviderAttributeValue.objects.filter(provider__in=providers).values_list(
                "provider_id", "definition_id"
            )
        )

        # Value generators keyed by attribute name
        districts = [
            "Central",
            "Downtown",
            "Westside",
            "Eastside",
            "Old Town",
            "Riverside",
            "Midtown",
            "Northside",
        ]
        generators = {
            "Height": lambda: str(rng.randint(155, 195)),  # cm
            "Weight": lambda: str(rng.randint(50, 95)),  # kg
            "District": lambda: rng.choice(districts) if rng.random() > 0.5 else "",
            "Age": lambda: str(rng.randint(20, 45)),
            "Breasts": lambda: str(rng.randint(1, 5)),
            "Size of clothing": lambda: str(rng.randint(18, 24) * 2),  # 36–48 even
            "Size of shoes": lambda: str(rng.randint(35, 42)),
            "Intimate haircut": lambda: rng.choice(
                ["Full depilation", "Trimmed", "Natural"]
            ),
            "Body Art": lambda: rng.choice(
                ["None", "Tattoos", "Piercing", "Tattoos, Piercing"]
            ),
            "Not younger": lambda: str(rng.choice([18, 21])),
            "Not older": lambda: str(rng.randint(55, 70)),
        }

        attr_objects = []
        for provider in providers:
            # Always include required attributes, plus a random sample of optional ones
            num_optional = min(rng.randint(0, 2), len(optional_defs))
            chosen = required_defs + rng.sample(optional_defs, num_optional)
            for defn in chosen:
                if (provider.pk, defn.pk) in existing_pairs:
                    continue

                gen = generators.get(defn.name)
                if gen:
                    value = gen()
                else:
                    if defn.data_type == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
                        value = rng.choice(["true", "false"])
                    elif (
                        defn.data_type == ProviderAttributeDefinition.DATA_TYPE_INTEGER
                    ):
                        value = str(rng.randint(1, 100))
                    else:
                        value = "N/A"

                attr_objects.append(
                    ProviderAttributeValue(
                        provider=provider,
                        definition=defn,
                        value_text=value,
                    )
                )

        ProviderAttributeValue.objects.bulk_create(attr_objects, batch_size=BATCH_SIZE)
        return len(attr_objects)

    def _generate_pricing(self, rng, providers):
        """Generate pricing grid data for providers via bulk_create. Returns count."""
        day_notes = [
            "",
            "Weekdays only",
            "Available Mon-Fri",
            "By appointment",
            "10:00-18:00",
            "Morning preferred",
        ]
        night_notes = [
            "",
            "After 20:00",
            "Weekend nights only",
            "By appointment",
            "20:00-02:00",
            "Call first",
        ]

        existing_provider_ids = set(
            ProviderPricing.objects.filter(provider__in=providers).values_list(
                "provider_id", flat=True
            )
        )

        pricing_objects = []
        for provider in providers:
            if provider.pk in existing_provider_ids:
                continue

            apartment_available = rng.random() > 0.2
            outside_available = rng.random() > 0.2

            def rand_price():
                return Decimal(str(round(rng.randint(30, 200) / 5) * 5))

            pricing_objects.append(
                ProviderPricing(
                    provider=provider,
                    apartment_available=apartment_available,
                    outside_available=outside_available,
                    apartment_day_1h=rand_price() if apartment_available else None,
                    apartment_day_2h=rand_price() if apartment_available else None,
                    apartment_night_1h=rand_price() if apartment_available else None,
                    apartment_night_whole=rand_price() if apartment_available else None,
                    outside_day_1h=rand_price() if outside_available else None,
                    outside_day_2h=rand_price() if outside_available else None,
                    outside_night_1h=rand_price() if outside_available else None,
                    outside_night_whole=rand_price() if outside_available else None,
                    day_note=rng.choice(day_notes),
                    night_note=rng.choice(night_notes),
                )
            )

        ProviderPricing.objects.bulk_create(pricing_objects, batch_size=BATCH_SIZE)
        return len(pricing_objects)

    def _ensure_preference_definitions(self):
        """Ensure preference groups, subgroups, and options exist. Returns count created."""
        created = 0
        for group_def in SEED_PREFERENCE_GROUPS:
            group, g_created = PreferenceGroup.objects.get_or_create(
                name=group_def["name"],
                defaults={
                    "display_order": group_def["display_order"],
                    "is_active": True,
                },
            )
            if g_created:
                created += 1
            for i, sg_def in enumerate(group_def["subgroups"]):
                subgroup, sg_created = PreferenceSubgroup.objects.get_or_create(
                    group=group,
                    name=sg_def["name"],
                    defaults={"display_order": i, "is_active": True},
                )
                if sg_created:
                    created += 1
                for j, opt_text in enumerate(sg_def.get("options", [])):
                    _, opt_created = PreferenceSubgroupOption.objects.get_or_create(
                        subgroup=subgroup,
                        text=opt_text,
                        defaults={"display_order": j},
                    )
                    if opt_created:
                        created += 1
        return created

    def _generate_preferences(self, rng, providers):
        """Generate preference toggles and custom options for providers. Returns count."""
        subgroups = list(PreferenceSubgroup.objects.filter(is_active=True))
        if not subgroups:
            return 0

        existing_pairs = set(
            ProviderPreference.objects.filter(provider__in=providers).values_list(
                "provider_id", "subgroup_id"
            )
        )

        custom_texts = [
            "By appointment only",
            "Ask for details",
            "Weekend special",
            "First-time discount",
            "Premium option",
        ]

        pref_objects = []
        custom_objects = []
        for provider in providers:
            for sg in subgroups:
                if (provider.pk, sg.pk) in existing_pairs:
                    continue
                is_checked = rng.random() > 0.35
                pref_objects.append(
                    ProviderPreference(
                        provider=provider,
                        subgroup=sg,
                        is_checked=is_checked,
                    )
                )
                if is_checked and rng.random() > 0.6:
                    custom_objects.append(
                        ProviderPreferenceCustomOption(
                            provider=provider,
                            subgroup=sg,
                            text=rng.choice(custom_texts),
                            display_order=0,
                        )
                    )

        ProviderPreference.objects.bulk_create(pref_objects, batch_size=BATCH_SIZE)
        ProviderPreferenceCustomOption.objects.bulk_create(
            custom_objects, batch_size=BATCH_SIZE
        )

        # Generate provider custom preferences ("Other" group)
        other_items = [
            "Candles & aromatherapy",
            "Background music",
            "Hot stones",
            "Warm towels",
            "Parking available",
            "Wi-Fi for clients",
            "Drinks included",
            "Wheelchair accessible",
        ]
        existing_custom = set(
            ProviderCustomPreference.objects.filter(provider__in=providers).values_list(
                "provider_id", flat=True
            )
        )
        custom_pref_objects = []
        for provider in providers:
            if provider.pk in existing_custom:
                continue
            if rng.random() > 0.5:
                num_items = rng.randint(1, 3)
                for i, item in enumerate(rng.sample(other_items, num_items)):
                    custom_pref_objects.append(
                        ProviderCustomPreference(
                            provider=provider,
                            name=item,
                            display_order=i,
                        )
                    )
        ProviderCustomPreference.objects.bulk_create(
            custom_pref_objects, batch_size=BATCH_SIZE
        )

        return len(pref_objects)

    def handle(self, *args, **options):
        count = options["count"]
        rng = random.Random(42)  # deterministic seed for reproducibility

        if options["flush"]:
            self.stdout.write("Removing existing seed data...")
            seed_users = User.objects.filter(email__endswith=f"@{SEED_EMAIL_DOMAIN}")
            # Cascade: User → Provider → Reviews, Attributes, Gallery, Pricing
            deleted = seed_users.delete()
            admin_deleted = User.objects.filter(
                email="admin@massagemarketplace.com"
            ).delete()
            total = deleted[0] + admin_deleted[0]
            self.stdout.write(self.style.SUCCESS(f"Seed data removed ({total} rows)."))

        self._ensure_fixtures_loaded()

        city_country_pairs = self._build_cities_list()
        if not city_country_pairs:
            self.stderr.write(
                self.style.ERROR("No cities found in database. Cannot seed providers.")
            )
            return

        self.stdout.write(f"Generating {count} providers...")

        # Pre-fetch all existing seed emails in one query
        existing_emails = set(
            User.objects.filter(email__endswith=f"@{SEED_EMAIL_DOMAIN}").values_list(
                "email", flat=True
            )
        )

        # Pre-generate all provider data
        all_data = []
        for i in range(1, count + 1):
            all_data.append(self._generate_provider_data(i, rng, city_country_pairs))

        today = timezone.now().date()

        # Hash the shared password once instead of per-user (PBKDF2 is slow)
        hashed_password = make_password("BetaTest123!")

        # Split data into new vs existing
        new_data = [d for d in all_data if d["email"] not in existing_emails]

        with transaction.atomic():
            # Collect existing providers
            if existing_emails:
                providers = list(
                    Provider.objects.select_related("user").filter(
                        user__email__in=existing_emails
                    )
                )
            else:
                providers = []

            if new_data:
                # 1) Bulk-create all User objects
                user_objects = [
                    User(
                        email=User.objects.normalize_email(d["email"]),
                        password=hashed_password,
                        user_type="provider",
                        is_email_verified=True,
                        first_name=d["first_name"],
                        last_name=d["last_name"],
                    )
                    for d in new_data
                ]
                User.objects.bulk_create(user_objects, batch_size=BATCH_SIZE)

                # 2) Bulk-create all Provider objects with temporary unique slugs
                provider_objects = [
                    Provider(
                        user=user,
                        slug=f"_tmp-{i}",
                        bio=data["bio"],
                        phone=data["phone"],
                        phone_hours=data["phone_hours"],
                        country_id=data["country_id"],
                        city_id=data["city_id"],
                        subscription_status="active",
                        subscription_payment_method=data["payment_method"],
                        subscription_renewal_date=today
                        + timedelta(days=data["renewal_days"]),
                    )
                    for i, (user, data) in enumerate(zip(user_objects, new_data))
                ]
                Provider.objects.bulk_create(provider_objects, batch_size=BATCH_SIZE)

                # 3) Compute final slugs from PKs and bulk-update
                for provider in provider_objects:
                    name = provider.get_name()
                    provider.slug = slugify(name) + "-" + str(provider.pk)
                Provider.objects.bulk_update(
                    provider_objects, ["slug"], batch_size=BATCH_SIZE
                )

                providers.extend(provider_objects)

        created_count = len(new_data)

        self.stdout.write(f"  Created {created_count} providers")

        # Generate reviews in bulk
        self.stdout.write("Generating reviews...")
        with transaction.atomic():
            review_count = self._generate_reviews(rng, providers, hashed_password)
        self.stdout.write(f"  Created {review_count} reviews")

        # Ensure attribute definitions exist
        defn_created = self._ensure_attribute_definitions()
        if defn_created:
            self.stdout.write(f"  Created {defn_created} attribute definitions")

        # Generate provider attributes in bulk
        self.stdout.write("Generating provider attributes...")
        with transaction.atomic():
            attr_count = self._generate_attributes(rng, providers)
        self.stdout.write(f"  Created {attr_count} attribute values")

        # Copy city lat/lng to provider map_latitude/map_longitude
        self.stdout.write("Setting provider map coordinates from city...")
        cities_by_id = {
            c.id: c
            for c in City.objects.filter(
                id__in=[p.city_id for p in providers if p.city_id]
            )
        }
        to_update = []
        for provider in providers:
            city = cities_by_id.get(provider.city_id)
            if city and city.latitude and city.longitude:
                provider.map_latitude = city.latitude
                provider.map_longitude = city.longitude
                to_update.append(provider)
        if to_update:
            Provider.objects.bulk_update(
                to_update, ["map_latitude", "map_longitude"], batch_size=BATCH_SIZE
            )
        self.stdout.write(f"  Set map coordinates for {len(to_update)} providers")

        # Generate pricing grids in bulk
        self.stdout.write("Generating pricing grids...")
        with transaction.atomic():
            pricing_count = self._generate_pricing(rng, providers)
        self.stdout.write(f"  Created {pricing_count} pricing grids")

        # Ensure preference definitions exist
        pref_defn_created = self._ensure_preference_definitions()
        if pref_defn_created:
            self.stdout.write(f"  Created {pref_defn_created} preference definitions")

        # Generate provider preferences in bulk
        self.stdout.write("Generating provider preferences...")
        with transaction.atomic():
            pref_count = self._generate_preferences(rng, providers)
        self.stdout.write(f"  Created {pref_count} provider preferences")

        # Create admin user
        admin_email = "admin@massagemarketplace.com"
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                password="AdminBeta123!",
                user_type="admin",
            )
            self.stdout.write(f"  Created admin: {admin_email}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Beta data seeded: {created_count} providers, "
                f"{review_count} reviews, "
                f"{attr_count} attribute values, {pricing_count} pricing grids"
            )
        )

        self.stdout.write("")
        self.stdout.write("  Beta login credentials:")
        self.stdout.write(
            f"    Provider: provider0001@{SEED_EMAIL_DOMAIN} / BetaTest123!"
        )
        self.stdout.write(f"    Admin:    {admin_email} / AdminBeta123!")
