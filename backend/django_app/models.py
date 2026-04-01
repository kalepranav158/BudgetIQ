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

SUBTYPE_CHOICES = [
    ("expense", "Expense"),
    ("transfer_out", "Transfer Out"),
    ("transfer_in", "Transfer In"),
    ("atm_withdrawal", "ATM Withdrawal"),
    ("salary", "Salary"),
    ("refund", "Refund"),
]


class Transaction(models.Model):
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    type = models.CharField(max_length=6, choices=TYPE_CHOICES)
    subtype = models.CharField(max_length=20, choices=SUBTYPE_CHOICES, default="expense")
    category = models.CharField(max_length=32, default="other")
    source_file = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions"
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["category"]),
            models.Index(fields=["type"]),
            models.Index(fields=["subtype"]),
        ]

class MonthlySummary(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()  # 1–12

    # optional aggregated totals (fast dashboard)
    total_debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "monthly_summary"
        unique_together = ("year", "month")


class MonthlySubtypeSummary(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12

    expense_debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_out = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_in = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    atm_withdrawal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refund = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "monthly_subtype_summary"
        unique_together = ("year", "month")

class DailyExpenseSummary(models.Model):
    date = models.DateField(unique=True)

    # 🔗 link to month
    month = models.ForeignKey(
        MonthlySummary,
        on_delete=models.CASCADE,
        related_name="daily_summaries"
    )

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


class RegexCategoryMapping(models.Model):
    name = models.CharField(max_length=100, unique=True)
    pattern = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=32)
    priority = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "regex_category_mapping"
        indexes = [models.Index(fields=["priority"]), models.Index(fields=["category"])]

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.pattern = self.pattern.strip()
        self.category = self.category.strip().lower()
        super().save(*args, **kwargs)


class AccountCategoryMapping(models.Model):
    upi_id = models.CharField(max_length=32, db_index=True)
    name = models.CharField(max_length=100, blank=True, default="")
    category = models.CharField(max_length=32)
    priority = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "account_category_mapping"
        indexes = [models.Index(fields=["upi_id"]), models.Index(fields=["priority"])]

    def save(self, *args, **kwargs):
        self.upi_id = self.upi_id.strip()
        self.name = self.name.strip().upper()
        self.category = self.category.strip().lower()
        super().save(*args, **kwargs)


