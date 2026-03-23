# Smart Budget ML System

Smart Budget ML System is a transition of the original Smart Budget Management System from a single Django upload flow into a modular, ML-ready architecture.

Current phase: transaction parsing, normalization, storage, analytics, and rule-based categorization. ML artifacts are present but disabled by default.

## What It Does

- Parses password-protected YONO SBI or SBI-style PDF statements
- Extracts transaction date, description, debit, credit, balance, and counterparty fields
- Categorizes transactions with a rule-based engine and saved counterparty mappings
- Stores normalized transactions for analytics and future ML activation
- Exposes FastAPI endpoints for transactions, category summary, and monthly analytics
- Keeps the existing Django upload UI available as a compatibility layer

## Tech Stack

- Python
- Django for the legacy upload interface
- FastAPI for the normalized API layer
- SQLAlchemy with SQLite by default for normalized storage
- pdfplumber for PDF extraction


## Project Layout

```text
backend/
database/
docs/
ml/
smartbudget/
tests/
main.py
requirements.txt
```

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Import a statement into the normalized store.

```bash
python main.py path/to/statement.pdf --password YOUR_PASSWORD
```

4. Start the API.

```bash
uvicorn backend.api.main:app --reload
```

5. Optional: run the legacy Django UI.

```bash
cd smartbudget
python manage.py migrate
python manage.py runserver
```

## ML Status

- ML files are scaffolded under `ml/` and can be enabled later.
- Runtime categorization is currently rule-based.
- To enable ML fallback later, set `ENABLE_ML_CATEGORIZATION=1` in `.env` after preparing model artifacts.

## Running Tests

```bash
pytest
```

## Notes

- The canonical API and data path is the normalized database in `database/connection/`.
- The Django app remains available during migration and still stores its own legacy tables.
- `.env.example` documents the environment variables used by both paths.
