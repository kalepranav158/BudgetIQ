import json
import logging
from collections import defaultdict
from decimal import Decimal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.fastapi_service.parser.categorizer import build_keyword_map, categorize_description
from backend.fastapi_service.parser.pdf_parser import extract_transactions_from_pdf
from backend.shared.schemas import ParsePdfResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BudgetIQ PDF Parsing Service", version="1.0.0")

DEBIT_CATEGORIES = ["cash_withdrawal", "extra", "lunch", "other", "recharge", "tea"]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "budgetiq-fastapi"}


@app.post("/parse-pdf")
async def parse_pdf(
    file: UploadFile = File(...),
    password: str | None = Form(default=None),
    mappings: str = Form(default="[]"),
) -> JSONResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        mapping_rows = json.loads(mappings)
        if not isinstance(mapping_rows, list):
            raise ValueError("mappings must be a JSON list")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid mappings payload") from exc

    content = await file.read()

    try:
        transactions = extract_transactions_from_pdf(content, password=password)
    except Exception as exc:
        logger.exception("PDF parsing failed")
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc

    keyword_map = build_keyword_map(mapping_rows)
    for tx in transactions:
        tx["category"] = categorize_description(tx["description"], keyword_map)

    summaries = _build_daily_summaries(transactions)

    payload = ParsePdfResponse(transactions=transactions, summaries=summaries)
    return JSONResponse(content=payload.model_dump(mode="json"))


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
