# BudgetIQ Backend Architecture

## Pipeline
1. Django receives PDF upload via `/upload-pdf`.
2. Django fetches current keyword mappings from `category_mapping`.
3. Django calls FastAPI `/parse-pdf` with file + password + mapping payload.
4. FastAPI extracts PDF rows using `pdfplumber` and parses SBI date format (`01 Jul 2024`).
5. FastAPI categorizes transactions by keyword matching.
6. FastAPI returns `transactions` and `summaries` JSON.
7. Django persists raw rows into `transactions` and upserts `daily_expense_summary`.

## Components
- backend/django_app/models.py: strict schema tables
- backend/django_app/views.py: upload + category mapping APIs
- backend/django_app/services/db_service.py: persistence logic
- backend/fastapi_service/main.py: parser service entrypoint
- backend/fastapi_service/parser/pdf_parser.py: PDF extraction + parsing
- backend/fastapi_service/parser/categorizer.py: keyword to category assignment
- backend/shared/schemas.py: shared request/response models
- ml/features.py and ml/predict.py: ML-ready placeholders
