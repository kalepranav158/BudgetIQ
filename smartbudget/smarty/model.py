from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class Raw_Transaction(models.Model):
    """Stores raw transaction data from bank statements"""
    date = models.DateField(max_length=50)
    details = models.TextField()
    debit = models.CharField(max_length=50, null=True, blank=True)
    credit = models.CharField(max_length=50, null=True, blank=True)
    balance = models.CharField(max_length=50, null=True, blank=True)
    source_pdf = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    upi_id = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['created_at']),
            models.Index(fields=['upi_id']),
            models.Index(fields=['category']),
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.details[:50]}"

class DailyTransactionSummary(models.Model):
    """Daily categorized transaction summary"""
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Expense Categories
    cash_withdrawal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    tea = models.DecimalField(
        max_digits=12,
        decimal_places=2,  # Fixed missing decimal_places
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    lunch = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    dinner = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    other_expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    
    # Totals
    total_debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    total_credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Daily Transaction Summaries"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'user']),
        ]
        unique_together = [['date', 'user']]  # Ensures one summary per user per day

    def __str__(self):
        return f"{self.user.username}'s summary for {self.date}"

class UPI_Category_Mapping(models.Model):
    """Stores UPI ID to category mappings"""
    CATEGORY_CHOICES = [
        ('cash_withdrawal', 'Cash Withdrawal'),
        ('tea', 'Tea/Snacks'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('other', 'Other Expenses')
    ]
    
    upi_id = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "UPI Category Mappings"
        unique_together = [['upi_id', 'user']]  # Each user can have unique mapping per UPI ID

   