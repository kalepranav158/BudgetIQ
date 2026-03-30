from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0003_transaction_subtype_monthly_subtype_summary"),
    ]

    operations = [
        migrations.CreateModel(
            name="RegexCategoryMapping",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("pattern", models.CharField(max_length=255, unique=True)),
                ("category", models.CharField(max_length=32)),
                ("priority", models.IntegerField(default=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "regex_category_mapping",
            },
        ),
        migrations.AddIndex(
            model_name="regexcategorymapping",
            index=models.Index(fields=["priority"], name="regex_categ_priority_ca5335_idx"),
        ),
        migrations.AddIndex(
            model_name="regexcategorymapping",
            index=models.Index(fields=["category"], name="regex_categ_categor_8f096c_idx"),
        ),
    ]
