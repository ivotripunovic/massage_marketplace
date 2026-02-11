"""Data migration: add new ProviderAttributeDefinition rows and clean up old ones."""

from django.db import migrations


NEW_DEFINITIONS = [
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

# Old definitions that are no longer needed
OLD_DEFINITIONS_TO_REMOVE = ["Established at", "Working with eldery"]


def create_definitions(apps, schema_editor):
    ProviderAttributeDefinition = apps.get_model(
        "providers", "ProviderAttributeDefinition"
    )
    for defn in NEW_DEFINITIONS:
        ProviderAttributeDefinition.objects.get_or_create(
            name=defn["name"],
            defaults={
                "data_type": defn["data_type"],
                "display_order": defn["display_order"],
                "show_on_card": defn["show_on_card"],
            },
        )
    # Remove old definitions (and their values via CASCADE)
    ProviderAttributeDefinition.objects.filter(
        name__in=OLD_DEFINITIONS_TO_REMOVE
    ).delete()


def reverse_definitions(apps, schema_editor):
    ProviderAttributeDefinition = apps.get_model(
        "providers", "ProviderAttributeDefinition"
    )
    ProviderAttributeDefinition.objects.filter(
        name__in=[d["name"] for d in NEW_DEFINITIONS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("providers", "0012_make_provider_slug_unique"),
    ]

    operations = [
        migrations.RunPython(create_definitions, reverse_definitions),
    ]
