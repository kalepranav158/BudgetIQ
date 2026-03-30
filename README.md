# Smart Budget ML System

BudgetIQ is a clean backend rebuild using Django + FastAPI for SBI PDF transaction ingestion, categorization, and daily expense aggregation.

## Documentation Index
- docs/setup.md
- docs/architecture.md
- docs/api.md
- docs/progress_log.md
- docs/sprint_tracker.md

## Stack
- Django (API, ORM, data persistence)
- FastAPI (PDF parsing microservice)
- pdfplumber (statement extraction)
- PostgreSQL (preferred) or SQLite (development)

## Project Structure
```text
BudgetIQ/
  backend/
    django_app/
      models.py
      views.py
      services/
        aggregator.py
        db_service.py
        fastapi_client.py
    fastapi_service/
      main.py
      parser/
        pdf_parser.py
        categorizer.py
    shared/
      schemas.py
  ml/
    features.py
    predict.py
  docs/
    api.md
    architecture.md
```

## Database Tables
### transactions
- id
- date
- description
- amount
- type (debit/credit)
- subtype (expense/transfer_out/transfer_in/atm_withdrawal/salary/refund)
- category
- source_file
- created_at

### daily_expense_summary
- id
- date (unique)
- month_id (FK -> monthly_summary)
- cash_withdrawal
- extra
- lunch
- other
- recharge
- tea
- credit
- total_debit
- total_credit

### monthly_summary
- id
- year
- month
- total_debit
- total_credit
- created_at

### category_mapping
- id
- keyword
- category
- created_at

### regex_category_mapping
- id
- name
- pattern
- category
- priority
- created_at

## Setup
1. Create and activate virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment config:
   ```bash
   copy .env.example .env
   ```
4. Run Django migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
5. Start FastAPI parser service:
   ```bash
   uvicorn backend.fastapi_service.main:app --host 127.0.0.1 --port 8001 --reload
   ```
6. Start Django API service:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

## API Endpoints
### Django
- `GET /health`
- `GET /category-mapping`
- `POST /category-mapping/create`
- `GET /regex-mapping`
- `POST /regex-mapping/create`
- `POST /upload-pdf`

### FastAPI
- `GET /health`
- `POST /parse-pdf`
- `GET /get_transactions`
- `GET /get_regex_mappings`

See detailed examples in docs/api.md.

## Sample Test Flow
1. Add mapping:
   - POST `/category-mapping/create` with `keyword=ZOMATO`, `category=lunch`
2. Upload PDF:
   - POST `/upload-pdf` form-data with `file=@july2024.pdf` and optional `password`
3. Verify output:
   - Raw transactions in `transactions`
   - Daily rollups in `daily_expense_summary`

## Notes
- No frontend included.
- No ML models implemented.
- System is ML-ready via clean transactional + daily summary schema.
- Monthly rollups are automatically updated during daily summary upserts.
