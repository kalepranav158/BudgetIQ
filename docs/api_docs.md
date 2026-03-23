# API Docs

Base application entrypoint: `backend.api.main:app`

## Endpoints

### `POST /transactions/import`

Imports an SBI/YONO PDF statement into the normalized transaction database.

Form fields:

- `pdf_file`: PDF upload
- `password`: optional statement password override

Response:

```json
{
  "imported_count": 42,
  "duplicate_count": 3,
  "total_parsed": 45,
  "categories": ["food", "income", "recharge"]
}
```

### `GET /transactions`

Query parameters:

- `start_date`: optional `YYYY-MM-DD`
- `end_date`: optional `YYYY-MM-DD`
- `category`: optional category filter
- `limit`: max rows, default `200`

### `GET /analytics/category-summary`

Returns transaction count, debit, credit, and net amount grouped by category.

Query parameters:

- `start_date`: optional `YYYY-MM-DD`
- `end_date`: optional `YYYY-MM-DD`

### `GET /analytics/monthly`

Returns month-wise debit, credit, net amount, transaction count, and top spend category.

Query parameters:

- `year`: optional year filter

### `GET /health`

Simple runtime health response.
