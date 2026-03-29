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

## FastAPI Parser Service

### GET /health
Health check endpoint for FastAPI parser.

### POST /parse-pdf
Parses uploaded SBI PDF and returns normalized transactions and daily summaries.

Form fields:
- file (required)
- password (optional)
- mappings (required JSON string list)

Response:
```json
{
  "transactions": [
    {
      "date": "2024-07-01",
      "description": "UPI/ZOMATO",
      "amount": "249.00",
      "type": "debit",
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
