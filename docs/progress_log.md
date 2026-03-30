# Progress Log

## 2026-03-30

- Added transaction subtype support (`expense`, `transfer_out`, `transfer_in`, `atm_withdrawal`, `salary`, `refund`) to parsing and persistence flow.
- Added monthly subtype aggregation model and recalculation logic for subtype-level analytics.
- Added regex mapping model (`regex_category_mapping`) with name, regex pattern, category, and priority.
- Added Django endpoints for regex mapping management:
	- `GET /regex-mapping`
	- `POST /regex-mapping/create`
- Added FastAPI endpoint to inspect regex mappings:
	- `GET /get_regex_mappings`
- Updated parser categorizer to support regex-first mapping with keyword fallback and UPI counterparty extraction.
- Added tests for regex categorization behavior and parser endpoint coverage for all PDFs in `IO`.
- Fixed a view merge issue that had broken `create_category_mapping` response flow.

## 2026-03-29

- Stabilized FastAPI startup by correcting Django settings bootstrapping.
- Implemented and stabilized `GET /get_transactions` endpoint.
- Resolved async ORM usage and JSON serialization errors for transaction responses.
- Integrated `MonthlySummary` into daily upsert dataflow with automatic rollup recalculation.
- Added and applied migration `0002_monthlysummary_daily_month_fk` with backfill logic.
- Updated architecture, API docs, and README to reflect current production flow.
- Added sprint execution checklist in `docs/sprint_tracker.md`.

## 2026-03-17

- Audited the legacy Django workspace and mapped parser, schema, templates, and data artifacts.
- Identified architectural issues: hardcoded credentials, parser/view contract mismatch, empty local SQLite database, and duplicate one-off scripts.
- Added a new `backend/` package with FastAPI APIs, SQLAlchemy models, normalized ingestion, analytics, and rule-plus-ML categorization.
- Added `ml/` scaffolding for dataset export, model training, and inference.
- Patched the Django app to use shared parser and categorization logic while keeping the upload workflow available.
- Added root documentation, `.gitignore`, `.env` templates, and unified `requirements.txt`.
