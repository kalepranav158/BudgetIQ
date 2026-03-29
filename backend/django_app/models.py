from django.core.validators import MinValueValidator
from django.db import models


CATEGORY_CHOICES = [
    "cash_withdrawal",
    "extra",
    "lunch",
    "other",
    "recharge",
    "tea",
    "credit",
]

TYPE_CHOICES = [
    ("debit", "Debit"),
    ("credit", "Credit"),
]


class Transaction(models.Model):
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    type = models.CharField(max_length=6, choices=TYPE_CHOICES)
    category = models.CharField(max_length=32, default="other")
    source_file = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions"
        indexes = [models.Index(fields=["date"]), models.Index(fields=["category"]), models.Index(fields=["type"])]


class DailyExpenseSummary(models.Model):
    date = models.DateField(unique=True)
    cash_withdrawal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    extra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lunch = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recharge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tea = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "daily_expense_summary"
        indexes = [models.Index(fields=["date"])]


class CategoryMapping(models.Model):
    keyword = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "category_mapping"
        indexes = [models.Index(fields=["keyword"])]

    def save(self, *args, **kwargs):
        self.keyword = self.keyword.strip().upper()
        self.category = self.category.strip().lower()
        super().save(*args, **kwargs)
