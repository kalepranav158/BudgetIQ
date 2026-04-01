from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0004_regex_category_mapping"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountCategoryMapping",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("account_number", models.CharField(db_index=True, max_length=32)),
                ("name", models.CharField(blank=True, default="", max_length=100)),
                ("category", models.CharField(max_length=32)),
                ("priority", models.IntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "account_category_mapping",
            },
        ),
        migrations.AddIndex(
            model_name="accountcategorymapping",
            index=models.Index(fields=["account_number"], name="account_cat_account_8b740e_idx"),
        ),
        migrations.AddIndex(
            model_name="accountcategorymapping",
            index=models.Index(fields=["priority"], name="account_cat_priorit_5feb3f_idx"),
        ),
    ]
