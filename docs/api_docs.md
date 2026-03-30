# API Docs

This project has two running services:

1. Django API at `http://127.0.0.1:8000`
2. FastAPI parser service at `http://127.0.0.1:8001`

## Django Endpoints

### `GET /health`
Service health check.

### `GET /category-mapping`
Returns keyword-category mapping rows.

### `POST /category-mapping/create`
Creates or updates one keyword-category mapping.

Form fields:
- `keyword` (required)
- `category` (required)

### `GET /regex-mapping`
Returns regex mapping rows used for parser categorization.

### `POST /regex-mapping/create`
Creates or updates one regex mapping row.

Form fields:
- `name` (required)
- `pattern` (required)
- `category` (required)
- `priority` (optional, default `100`)

### `POST /upload-pdf`
Uploads statement PDF, forwards parse request to FastAPI, persists data in Django DB.

Form fields:
- `file` (required)
- `password` (optional)

Resulting persistence:
- `transactions` rows inserted
- `daily_expense_summary` rows upserted
- `monthly_summary` rows linked and recalculated

## FastAPI Endpoints

### `GET /health`
Service health check.

### `POST /parse-pdf`
Parses PDF and returns normalized transactions plus daily summary output.

Form fields:
- `file` (required)
- `password` (optional)
- `mappings` (required JSON string list)
- `persist` (optional, default `true`)

### `GET /get_transactions`
Returns persisted transaction rows from Django ORM.

### `GET /get_all_daily_summaries`
Builds daily summaries from persisted transactions.

### `GET /get_monthly_summaries`
Returns persisted monthly debit/credit rollups.

### `GET /get_regex_mappings`
Returns parser-side regex mappings from `regex_category_mapping`.
