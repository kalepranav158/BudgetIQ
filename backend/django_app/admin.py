from django.contrib import admin

from backend.django_app.models import (
    AccountCategoryMapping,
    CategoryMapping,
    DailyExpenseSummary,
    RegexCategoryMapping,
    Transaction,
)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "description", "amount", "type", "category", "source_file", "created_at")
    search_fields = ("description", "category", "source_file")
    list_filter = ("type", "category", "date")


@admin.register(DailyExpenseSummary)
class DailyExpenseSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "date",
        "cash_withdrawal",
        "extra",
        "lunch",
        "other",
        "recharge",
        "tea",
        "credit",
        "total_debit",
        "total_credit",
    )
    list_filter = ("date",)


@admin.register(CategoryMapping)
class CategoryMappingAdmin(admin.ModelAdmin):
    list_display = ("id", "keyword", "category", "created_at")
    search_fields = ("keyword", "category")


@admin.register(RegexCategoryMapping)
class RegexCategoryMappingAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "pattern", "category", "priority", "created_at")
    search_fields = ("name", "pattern", "category")
    list_filter = ("category",)


@admin.register(AccountCategoryMapping)
class AccountCategoryMappingAdmin(admin.ModelAdmin):
    list_display = ("id", "upi_id", "name", "category", "priority", "created_at")
    search_fields = ("upi_id", "name", "category")
    list_filter = ("category",)
