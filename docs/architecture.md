# Architecture

## System Design

```text
PDF / YONO SBI statement
        |
        v
backend.utils.parsing.StatementParser
        |
        v
backend.services.categorization.HybridTransactionCategorizer
        |
        +--> Rule-based decision from counterparty + keyword config
        |
        +--> ML classifier fallback when artifacts are available
        |
        v
backend.services.transaction_service.TransactionIngestionService
        |
        v
SQLAlchemy normalized store (database/connection/smart_budget.db)
        |
        +--> FastAPI read APIs
        |
        +--> ML dataset export and training pipeline

Legacy compatibility path:
Django upload view -> shared parser/categorizer -> Django Raw_Transaction + DailyTransactionSummary tables
```

## Data Flow

1. A statement PDF is uploaded through the Django page or the FastAPI import route.
2. The parser extracts transaction rows from table structures first and falls back to text parsing.
3. Each transaction is normalized into date, description, debit, credit, balance, amount, and counterparty fields.
4. The hybrid categorizer applies deterministic rules first and falls back to the ML classifier when available.
5. Transactions are stored in the normalized `transactions` table with category, channel, amount, and deduplication fingerprint.
6. Analytics APIs aggregate transactions by date range, category, and month.
7. The ML dataset export uses stored transactions to build labeled training CSVs.

## Key Improvements

- Removed hardcoded database credentials from runtime code.
- Added a normalized persistence model for API and ML workflows.
- Preserved the existing Django upload experience during the transition.
- Separated parsing, categorization, persistence, analytics, and ML training concerns.
