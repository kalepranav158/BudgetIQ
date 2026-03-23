from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_date: date
    description: str
    reference_number: str | None
    debit_amount: Decimal
    credit_amount: Decimal
    amount: Decimal
    balance: Decimal | None
    direction: str
    category: str
    predicted_category: str | None
    prediction_source: str
    counterparty: str | None
    transaction_channel: str
    source_file: str | None
    created_at: datetime


class TransactionListResponse(BaseModel):
    total: int
    items: list[TransactionRead]


class CategorySummaryItem(BaseModel):
    category: str
    transaction_count: int
    total_debit: Decimal
    total_credit: Decimal
    net_amount: Decimal


class MonthlyAnalyticsItem(BaseModel):
    month: str
    transaction_count: int
    total_debit: Decimal
    total_credit: Decimal
    net_amount: Decimal
    top_spend_category: str | None


class ImportResponse(BaseModel):
    imported_count: int
    duplicate_count: int
    total_parsed: int
    categories: list[str]
