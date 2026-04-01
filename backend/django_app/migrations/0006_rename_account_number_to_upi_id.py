# Generated migration to rename account_number to upi_id

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_app', '0005_account_category_mapping'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accountcategorymapping',
            old_name='account_number',
            new_name='upi_id',
        ),
    ]
