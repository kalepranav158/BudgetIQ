from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.schemas.transaction import (
    CategorySummaryItem,
    ImportResponse,
    MonthlyAnalyticsItem,
    TransactionListResponse,
    TransactionRead,
)
from backend.services.analytics import AnalyticsService
from backend.services.transaction_service import TransactionIngestionService
from database.connection.session import get_db

router = APIRouter(tags=["transactions"])


@router.post("/transactions/import", response_model=ImportResponse)
async def import_transactions(
    pdf_file: Annotated[UploadFile, File(...)],
    password: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> ImportResponse:
    if not pdf_file.filename or not pdf_file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF bank statements are supported.")

    service = TransactionIngestionService(db)
    try:
        pdf_file.file.seek(0)
        summary = service.import_statement(
            pdf_source=pdf_file.file,
            source_name=pdf_file.filename,
            password=password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ImportResponse(**summary)


@router.get("/transactions", response_model=TransactionListResponse)
def get_transactions(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    service = AnalyticsService(db)
    items = service.list_transactions(
        start_date=start_date,
        end_date=end_date,
        category=category,
        limit=limit,
    )
    return TransactionListResponse(
        total=len(items),
        items=[TransactionRead.model_validate(item) for item in items],
    )


@router.get("/analytics/category-summary", response_model=list[CategorySummaryItem])
def get_category_summary(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CategorySummaryItem]:
    service = AnalyticsService(db)
    return service.category_summary(start_date=start_date, end_date=end_date)


@router.get("/analytics/monthly", response_model=list[MonthlyAnalyticsItem])
def get_monthly_analytics(
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
) -> list[MonthlyAnalyticsItem]:
    service = AnalyticsService(db)
    return service.monthly_analytics(year=year)
