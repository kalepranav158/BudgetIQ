import json
import logging
from collections import defaultdict
from decimal import Decimal
import os
import time
import django
from django.db.utils import OperationalError, ProgrammingError
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from backend.fastapi_service.parser.categorizer import (
    build_account_rules,
    build_keyword_map,
    build_regex_rules,
    categorize_transaction,
    infer_transaction_subtype,
)
from backend.fastapi_service.parser.pdf_parser import extract_transactions_from_pdf
from backend.shared.schemas import DailySummaryOut, ParsePdfResponse, TransactionOut
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from backend.django_app.models import AccountCategoryMapping, CategoryMapping, MonthlySummary, RegexCategoryMapping, Transaction
from backend.django_app.services.db_service import save_transactions, upsert_daily_summaries

app = FastAPI(title="BudgetIQ ", version="1.0.0")

_MAPPING_CACHE: dict[str, float | list[dict]] = {
    "expires_at": 0.0,
    "rows": [],
}

DEBIT_CATEGORIES = ["cash_withdrawal", "extra", "lunch", "other", "recharge", "tea"]


def _get_cached_mappings(ttl_seconds: int = 120) -> list[dict]:
    now = time.time()
    expires_at_raw = _MAPPING_CACHE.get("expires_at", 0.0)
    expires_at = float(expires_at_raw) if isinstance(expires_at_raw, (int, float)) else 0.0
    if now < expires_at:
        rows_raw = _MAPPING_CACHE.get("rows", [])
        if isinstance(rows_raw, list) and rows_raw:
            return list(rows_raw)

    keyword_rows = CategoryMapping.objects.all().values("keyword", "category")
    regex_rows = RegexCategoryMapping.objects.all().order_by("priority", "name").values(
        "name", "pattern", "category", "priority"
    )
    account_rows = AccountCategoryMapping.objects.all().order_by("priority", "upi_id").values(
        "upi_id", "name", "category", "priority"
    )

    rows: list[dict] = [
        {
            "kind": "keyword",
            "keyword": row["keyword"],
            "category": row["category"],
        }
        for row in keyword_rows
    ]
    rows.extend(
        {
            "kind": "regex",
            "name": row["name"],
            "pattern": row["pattern"],
            "category": row["category"],
            "priority": row["priority"],
        }
        for row in regex_rows
    )
    rows.extend(
        {
            "kind": "account",
            "upi_id": row["upi_id"],
            "name": row["name"],
            "category": row["category"],
            "priority": row["priority"],
        }
        for row in account_rows
    )

    _MAPPING_CACHE["rows"] = rows
    _MAPPING_CACHE["expires_at"] = now + ttl_seconds
    return rows


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "budgetiq-fastapi"}


@app.post("/parse-pdf")
def parse_pdf(
    file: UploadFile = File(...),
    
    mappings: str = Form(default="[]"),
    persist: bool = Form(default=True),
) -> JSONResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if mappings.strip():
        try:
            mapping_rows = json.loads(mappings)
            if not isinstance(mapping_rows, list):
                raise ValueError("mappings must be a JSON list")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid mappings payload") from exc
        if not mapping_rows:
            mapping_rows = _get_cached_mappings()
    else:
        mapping_rows = _get_cached_mappings()

    content = file.file.read()

    try:
        transactions = extract_transactions_from_pdf(content, password='1508@6239')
    except Exception as exc:
        logger.exception("PDF parsing failed")
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc

    keyword_map = build_keyword_map(mapping_rows)
    regex_rules = build_regex_rules(mapping_rows)
    account_rules = build_account_rules(mapping_rows)
    for tx in transactions:
        category, category_source, confidence, canonical_name = categorize_transaction(
            description=tx["description"],
            keyword_map=keyword_map,
            regex_rules=regex_rules,
            account_rules=account_rules,
        )
        tx["category"] = category
        tx["category_source"] = category_source
        tx["confidence"] = confidence
        tx["subtype"] = infer_transaction_subtype(tx["description"], tx["type"])
        if canonical_name:
            tx["canonical_name"] = canonical_name

    summaries = _build_daily_summaries(transactions)

    if persist and transactions:
        save_transactions(transactions=transactions, source_file=file.filename)
        upsert_daily_summaries(summaries=summaries)

    transaction_models = [TransactionOut.model_validate(tx) for tx in transactions]
    summary_models = [DailySummaryOut.model_validate(summary) for summary in summaries]

    payload = ParsePdfResponse(transactions=transaction_models, summaries=summary_models)
    return JSONResponse(content=payload.model_dump(mode="json"))


@app.get('/get_transactions')
def get_transactions():
    """Get all transactions from the database."""
    transactions = list(
        Transaction.objects.
        all().
        order_by('-date', '-id').
        values('id', 'date', 'description', 'amount', 'type', 'subtype', 'category')
        )
    return {"transactions": transactions}

@app.get('/get_all_daily_summaries')
def get_all_daily_summaries():
    daily_summaries = _build_daily_summaries(
        list(Transaction.objects.all().order_by('-date', '-id').values('date', 'description', 'amount', 'type', 'category'))
    )
    return daily_summaries


@app.get('/get_monthly_summaries')
def get_monthly_summaries(year: int | None = None, month: int | None = None):
    queryset = MonthlySummary.objects.all().order_by('year', 'month')
    if year is not None:
        queryset = queryset.filter(year=year)
    if month is not None:
        queryset = queryset.filter(month=month)

    summaries = list(queryset.values('year', 'month', 'total_debit', 'total_credit', 'created_at'))
    return {'monthly_summaries': summaries}


@app.get('/get_category_mappings')
def get_category_mappings():
    try:
        mappings = list(
            CategoryMapping.objects.all()
            .order_by('keyword')
            .values('id', 'keyword', 'category', 'created_at')
        )
    except (OperationalError, ProgrammingError):
        logger.warning("category_mapping table not available yet; returning empty mapping list")
        mappings = []
    return {'category_mappings': mappings}


@app.get('/get_regex_mappings')
def get_regex_mappings():
    try:
        mappings = list(
            RegexCategoryMapping.objects.all()
            .order_by('priority', 'name')
            .values('id', 'name', 'pattern', 'category', 'priority', 'created_at')
        )
    except (OperationalError, ProgrammingError):
        logger.warning("regex_category_mapping table not available yet; returning empty mapping list")
        mappings = []
    return {'regex_mappings': mappings}



@app.get('/get_account_mappings')
def get_account_mappings():
    try:
        mappings = list(
            AccountCategoryMapping.objects.all()
            .order_by('priority', 'upi_id')
            .values('id', 'upi_id', 'name', 'category', 'priority', 'created_at')
        )
    except (OperationalError, ProgrammingError):
        logger.warning("account_category_mapping table not available yet; returning empty mapping list")
        mappings = []
    return {'account_mappings': mappings}











#_----------------------------------HELEPR FUNCTIONS----------------------------------#

def _build_daily_summaries(transactions: list[dict]) -> list[dict]:
    grouped = defaultdict(
        lambda: {
            "cash_withdrawal": Decimal("0.00"),
            "extra": Decimal("0.00"),
            "lunch": Decimal("0.00"),
            "other": Decimal("0.00"),
            "recharge": Decimal("0.00"),
            "tea": Decimal("0.00"),
            "credit": Decimal("0.00"),
            "total_debit": Decimal("0.00"),
            "total_credit": Decimal("0.00"),
        }
    )

    for tx in transactions:
        date = tx["date"]
        amount = Decimal(str(tx["amount"]))
        tx_type = tx["type"]
        category = tx.get("category", "other")

        if tx_type == "credit":
            grouped[date]["credit"] += amount
            grouped[date]["total_credit"] += amount
        else:
            debit_category = category if category in DEBIT_CATEGORIES else "other"
            grouped[date][debit_category] += amount
            grouped[date]["total_debit"] += amount

    result = []
    for date, row in sorted(grouped.items(), key=lambda item: item[0]):
        data = {"date": date}
        data.update(row)
        result.append(data)
    return result
