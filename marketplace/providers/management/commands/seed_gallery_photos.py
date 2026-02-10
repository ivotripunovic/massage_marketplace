"""Management command to seed gallery photos for demo providers.

Downloads stock photos from picsum.photos and assigns them as gallery
images for all existing providers.

Usage:
    python manage.py seed_gallery_photos
    python manage.py seed_gallery_photos --flush    # Clear existing gallery images first
    python manage.py seed_gallery_photos --count 3  # 3 images per provider
"""

import random
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from providers.models import Provider, ProviderGalleryImage


CAPTIONS = [
    "Our relaxing treatment room",
    "Massage therapy session",
    "Tranquil studio environment",
    "Professional workspace",
    "Calming atmosphere",
    "Wellness center",
    "Aromatherapy station",
    "Hot stone therapy setup",
    "Client relaxation area",
    "Treatment preparation",
]


class Command(BaseCommand):
    help = "Seed gallery photos for existing providers from picsum.photos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Remove existing gallery images before seeding",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of gallery images per provider (default: 5)",
        )

    def handle(self, *args, **options):
        flush = options["flush"]
        count = options["count"]

        if flush:
            deleted, _ = ProviderGalleryImage.objects.all().delete()
            self.stdout.write(f"Removed {deleted} existing gallery images.")

        providers = Provider.objects.all()
        if not providers.exists():
            self.stdout.write(
                self.style.WARNING("No providers found. Run seed_beta_data first.")
            )
            return

        total_created = 0
        for provider in providers:
            if not flush and provider.gallery_images.exists():
                self.stdout.write(
                    f"  Skipping {provider.user.email} (already has gallery images)"
                )
                continue

            captions = random.sample(CAPTIONS, min(count, len(CAPTIONS)))

            for i in range(count):
                caption = captions[i % len(captions)]
                try:
                    url = "https://picsum.photos/800/600"
                    response = urllib.request.urlopen(url)
                    image_data = response.read()
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Failed to download image for {provider.user.email}: {e}"
                        )
                    )
                    continue

                filename = f"gallery_{provider.pk}_{i}.jpg"
                gallery_image = ProviderGalleryImage(
                    provider=provider,
                    caption=caption,
                )
                gallery_image.image.save(filename, ContentFile(image_data), save=True)
                total_created += 1

            self.stdout.write(
                f"  Added {count} gallery images for {provider.user.email}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Gallery seeding complete: {total_created} images created."
            )
        )
