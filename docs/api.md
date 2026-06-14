# BudgetIQ API Documentation

## Django API

### GET /health
Health check endpoint for Django API.

### GET /category-mapping
Returns all keyword-category mappings.

Response:
```json
{
  "mappings": [
    {"keyword": "ZOMATO", "category": "lunch"}
  ]
}
```

### POST /category-mapping/create
Create or update keyword mappings.

Form fields:
- keyword (required)
- category (required)

### GET /regex-mapping
Returns all regex-category mappings.

Response:
```json
{
  "mappings": [
    {
      "id": 1,
      "name": "Swiggy",
      "pattern": "SWIGGY|BUNDL",
      "category": "lunch",
      "priority": 1
    }
  ]
}
```

### POST /regex-mapping/create
Create or update regex mapping rows.

Form fields:
- name (required)
- pattern (required, regex string)
- category (required)
- priority (optional, default 100)

### POST /upload-pdf
Uploads SBI PDF statement and stores transactions + summary.

Form fields:
- file (required, PDF)
- password (optional)

Response:
```json
{
  "message": "PDF processed successfully",
  "saved_transactions": 32,
  "transactions": [...],
  "summaries": [...]
}
```

Behavior notes:
- Daily summaries are upserted into `daily_expense_summary`.
- Monthly totals are auto-maintained in `monthly_summary`.

## FastAPI Parser Service

### GET /health
Health check endpoint for FastAPI parser.

### POST /parse-pdf
Parses uploaded SBI PDF and returns normalized transactions and daily summaries.

Form fields:
- file (required)
- password (optional)
- mappings (required JSON string list)
- persist (optional, default true)

Response:
```json
{
  "transactions": [
    {
      "date": "2024-07-01",
      "description": "UPI/ZOMATO",
      "amount": "249.00",
      "type": "debit",
      "subtype": "expense",
      "balance": "12000.00",
      "category": "lunch"
    }
  ],
  "summaries": [
    {
      "date": "2024-07-01",
      "cash_withdrawal": "0.00",
      "extra": "0.00",
      "lunch": "249.00",
      "other": "0.00",
      "recharge": "0.00",
      "tea": "0.00",
      "credit": "0.00",
      "total_debit": "249.00",
      "total_credit": "0.00"
    }
  ]
}
```

### GET /get_transactions
Returns persisted transactions from the Django database.

Response:
```json
{
  "transactions": [
    {
      "id": 1,
      "date": "2024-07-01",
      "description": "UPI/ZOMATO",
      "amount": 249.0,
      "type": "debit",
      "subtype": "expense",
      "category": "lunch",
      "category_source": "keyword",
      "confidence": 1.0
    }
  ]
}
```

### GET /forecast_daily_spend
Returns regression-based daily debit forecast for the requested horizon.

Query params:
- `days` (optional, default 7, allowed 1-60)

Response:
```json
{
  "days": 7,
  "model_version": "v20260414T010101Z-abcd1234",
  "selected_model": "ridge",
  "last_observed_date": "2026-04-13",
  "recent_actuals": [
    {
      "date": "2026-04-13",
      "actual_total_debit": 430.0
    }
  ],
  "forecast": [
    {
      "date": "2026-04-14",
      "predicted_total_debit": 450.0,
      "lower_bound": 420.0,
      "upper_bound": 480.0
    }
  ]
}
```

Error notes:
- `400` for invalid horizon or insufficient historical data.
- `503` when regression artifact is not available.

### GET /get_regex_mappings
Returns regex mappings available to FastAPI parser.

### GET /get_all_daily_summaries
Builds and returns daily summaries from persisted transaction rows.

### GET /get_monthly_summaries
Returns persisted monthly debit and credit totals.
