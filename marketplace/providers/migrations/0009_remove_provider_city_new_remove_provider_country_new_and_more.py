# Custom migration: remove deprecated CharField location fields, rename ForeignKey fields

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('providers', '0008_providerattributedefinition_providerattributevalue'),
    ]

    operations = [
        # Step 1: Remove the old CharField fields
        migrations.RemoveField(
            model_name='provider',
            name='country',
        ),
        migrations.RemoveField(
            model_name='provider',
            name='city',
        ),
        # Step 2: Rename ForeignKey fields from *_new to the original names
        migrations.RenameField(
            model_name='provider',
            old_name='country_new',
            new_name='country',
        ),
        migrations.RenameField(
            model_name='provider',
            old_name='city_new',
            new_name='city',
        ),
        # Step 3: Update field definitions to match the model
        migrations.AlterField(
            model_name='provider',
            name='country',
            field=models.ForeignKey(
                blank=True,
                help_text='Country where services are provided',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='providers',
                to='providers.country',
            ),
        ),
        migrations.AlterField(
            model_name='provider',
            name='city',
            field=models.ForeignKey(
                blank=True,
                help_text='City where services are provided',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='providers',
                to='providers.city',
            ),
        ),
    ]
