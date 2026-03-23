# Progress Log

## 2026-03-17

- Audited the legacy Django workspace and mapped parser, schema, templates, and data artifacts.
- Identified architectural issues: hardcoded credentials, parser/view contract mismatch, empty local SQLite database, and duplicate one-off scripts.
- Added a new `backend/` package with FastAPI APIs, SQLAlchemy models, normalized ingestion, analytics, and rule-plus-ML categorization.
- Added `ml/` scaffolding for dataset export, model training, and inference.
- Patched the Django app to use shared parser and categorization logic while keeping the upload workflow available.
- Added root documentation, `.gitignore`, `.env` templates, and unified `requirements.txt`.
