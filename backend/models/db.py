from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.connection.session import Base


class TransactionRecord(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(Text)
    reference_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), index=True)
    balance: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    direction: Mapped[str] = mapped_column(String(10), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    predicted_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prediction_source: Mapped[str] = mapped_column(String(20), default="rule")
    counterparty: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    transaction_channel: Mapped[str] = mapped_column(String(30), default="upi")
    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_transactions_date_category", "transaction_date", "category"),
    )


class CategoryMapping(Base):
    __tablename__ = "category_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    counterparty: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
