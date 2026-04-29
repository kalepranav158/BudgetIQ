# Progress Log

## 2026-04-29

- Completed parser robustness updates for statement format variance:
	- SBI start-line detection now supports numeric dates and optional post-date columns.
	- Date parsing expanded to `%d/%m/%Y`, `%d-%m-%Y`, and `%d %b %Y`.
	- Amount-column regex now tolerates missing `Ref` column variants.
- Improved encrypted PDF handling in FastAPI parsing flow:
	- Added explicit password/encryption exception handling and clearer client-facing parse errors.
- Enabled dynamic category support end-to-end:
	- Frontend mapping forms now support creating custom categories.
	- Backend categorization/schema layer accepts non-hardcoded category labels.
- Implemented transaction reclassification workflow:
	- Added reparse job model and worker command (`run_reparse_worker`).
	- Added enqueue/status APIs for background reclassification.
	- Added synchronous reclassify path for dashboard-triggered immediate runs.
	- Added dashboard reclassification status cards (status, rows updated, last run, progress).
- Fixed dashboard refresh gap after reclassification:
	- Corrected React Query invalidation keys to actual query keys (`dailySummaries`, `monthlySummaries`).
	- Added active query refetch after reclassify completion.
- Fixed dashboard reclassify timeout behavior:
	- Increased synchronous reclassify request timeout to 180s on frontend mutation.

### Current Phase State (as of 2026-04-29)

- Phase A: Parser Reliability -> **Complete (for current known statement formats)**
- Phase B: Dynamic Categorization -> **Complete (keyword + custom categories)**
- Phase C: Reclassification UX -> **Complete for dashboard-triggered manual runs**
- Phase D: Background Processing -> **Partial (worker command implemented; no Celery/RQ orchestration)**
- Phase E: ML Production Integration -> **Partial (infrastructure present; classification still rule-dominant in current live flow)**

## 2026-04-16

- Improved classification precision in `categorizer.py` with safer short-keyword matching to reduce substring false positives.
- Added keyword matching priority by keyword length so specific merchant patterns are evaluated before generic tokens.
- Improved account-rule matching with tolerant name comparison when UPI ID matches exactly, returning calibrated confidence (`0.95` for fuzzy name + exact UPI, `0.9` for fuzzy name-only fallback).
- Hardened rule parsing with safe priority casting to avoid crashes from malformed mapping rows.
- Added regression tests for short-keyword false positives and fuzzy UPI account-name matching.
- Validated targeted suite: `tests/test_categorizer.py` and `tests/test_categorization.py` (`9 passed`).

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
