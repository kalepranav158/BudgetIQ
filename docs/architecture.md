# BudgetIQ Backend Architecture

## Pipeline
1. Django receives PDF upload via `/upload-pdf`.
2. Django fetches keyword mappings from `category_mapping` and regex mappings from `regex_category_mapping`.
3. Django calls FastAPI `/parse-pdf` with file + password + mapping payload.
4. FastAPI extracts PDF rows using `pdfplumber` and parses SBI date format (`01 Jul 2024`).
5. FastAPI categorizes transactions using regex rules first, then keyword fallback.
6. FastAPI derives subtype (`expense`, `transfer_out`, `transfer_in`, `atm_withdrawal`, `salary`, `refund`).
7. FastAPI returns `transactions` and `summaries` JSON.
8. Django persists rows into `transactions`, including subtype, and upserts `daily_expense_summary`.
9. Django recalculates `monthly_summary` and `monthly_subtype_summary` rollups.

## Components
- backend/django_app/models.py: strict schema tables
- backend/django_app/views.py: upload + category mapping APIs
- backend/django_app/services/db_service.py: persistence logic
- backend/fastapi_service/main.py: parser service entrypoint
- backend/fastapi_service/parser/pdf_parser.py: PDF extraction + parsing
- backend/fastapi_service/parser/categorizer.py: regex/keyword categorization + subtype derivation
- backend/shared/schemas.py: shared request/response models
- ml/features.py and ml/predict.py: ML-ready placeholders

## Dataflow: Daily to Monthly
1. `upsert_daily_summaries()` parses each summary date.
2. The service gets or creates `MonthlySummary(year, month)`.
3. The corresponding `DailyExpenseSummary` row is inserted/updated with `month` foreign key.
4. For touched months, totals are recalculated using all linked daily rows.
5. `monthly_summary.total_debit` and `monthly_summary.total_credit` are saved as source of truth.
