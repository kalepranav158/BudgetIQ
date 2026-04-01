from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CategoryLiteral = Literal[
    "cash_withdrawal",
    "extra",
    "lunch",
    "other",
    "recharge",
    "tea",
    "credit",
]

SubtypeLiteral = Literal[
    "expense",
    "transfer_out",
    "transfer_in",
    "atm_withdrawal",
    "salary",
    "refund",
]


class CategoryMappingIn(BaseModel):
    keyword: str = Field(min_length=1, max_length=100)
    category: CategoryLiteral


class TransactionOut(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    date: str
    description: str
    amount: Decimal
    type: Literal["debit", "credit"]
    subtype: SubtypeLiteral = "expense"
    balance: Decimal = Decimal("0.00")
    category: CategoryLiteral = "other"
    category_source: Literal["account_rule", "regex", "keyword", "ml"] = "keyword"
    confidence: float = 0.0


class DailySummaryOut(BaseModel):
    date: str
    cash_withdrawal: Decimal = Decimal("0.00")
    extra: Decimal = Decimal("0.00")
    lunch: Decimal = Decimal("0.00")
    other: Decimal = Decimal("0.00")
    recharge: Decimal = Decimal("0.00")
    tea: Decimal = Decimal("0.00")
    credit: Decimal = Decimal("0.00")
    total_debit: Decimal = Decimal("0.00")
    total_credit: Decimal = Decimal("0.00")


class ParsePdfResponse(BaseModel):
    transactions: list[TransactionOut]
    summaries: list[DailySummaryOut]
