# BudgetIQ Project Structure Guide

## 📂 Directory Overview

### Root Level Files
```
BudgetIQ/
├── manage.py              # Django management CLI
├── requirements.txt       # Python dependencies
├── pytest.ini            # Pytest configuration
├── .gitignore           # Git exclusion rules
├── README.md            # Project overview
├── PROJECT_README.md    # Comprehensive project guide
└── LICENSE              # MIT License
```

---

## 🔧 Backend (`backend/`)

### Django Application (`backend/django_app/`)

Core Django application with models, views, and business logic.

```
django_app/
├── __init__.py
├── models.py            # Database models:
│                        # - Transaction: Financial records
│                        # - Category: Transaction categories  
│                        # - LowConfidenceFlagRecord: Flagged predictions
│                        # - RetrainingCycle: Active learning jobs
│                        # - ParseJob: Document parsing jobs
│
├── views.py             # API endpoints:
│                        # - TransactionViewSet
│                        # - CategoryViewSet
│                        # - ForecastViewSet
│                        # - AnalyticsViewSet
│
├── urls.py              # URL routing for all endpoints
├── admin.py             # Django admin configuration
├── apps.py              # App configuration
├── reparse_job.py       # Document reprocessing logic
│
├── migrations/          # Database migrations
│   ├── 0001_initial.py
│   ├── 0002_*.py
│   └── 0011_active_learning_models.py  # Latest: Active learning models
│
├── management/          # Custom management commands
│   └── commands/
│       └── run_reparse_worker.py  # Background worker for reprocessing
│
└── services/            # Business logic modules
    ├── __init__.py
    ├── db_service.py    # Database operations
    └── categorizer.py   # Classification pipeline
```

### FastAPI Service (`backend/fastapi_service/`)

High-performance parsing and ML serving service.

```
fastapi_service/
├── __init__.py
├── main.py              # FastAPI app initialization
│                        # Endpoints for:
│                        # - /parse (document parsing)
│                        # - /predict (category prediction)
│                        # - /forecast (spending forecast)
│
└── parser/              # Document processing
    ├── __init__.py
    ├── pdf_parser.py    # PDF extraction via pdfplumber
    ├── categorizer.py   # TF-IDF + LogisticRegression
    └── utils.py         # Parsing utilities
```

### Shared Modules (`backend/shared/`)

Shared utilities and schemas across services.

```
shared/
├── __init__.py
└── schemas.py           # Pydantic models:
                         # - TransactionSchema
                         # - ForecastSchema
                         # - CategorySchema
```

### Settings (`backend/`)
```
backend/
├── __init__.py
├── settings.py          # Django configuration
├── urls.py             # Root URL configuration
├── wsgi.py             # WSGI server entry
└── asgi.py             # ASGI server entry
```

---

## 🧠 Machine Learning (`ml/`)

### Training (`ml/training/`)

Model training pipelines with version management.

```
training/
├── train_hurdle.py          # Two-stage hurdle model:
│                            # Stage 1: Binary classifier (spend vs zero)
│                            # Stage 2: Quantile regressor (spending amount)
│                            # Uses StratifiedShuffleSplit for imbalanced data
│                            # Outputs versioned models with metrics
│
├── train_classifier.py      # Category classifier training
│                            # TF-IDF vectorization
│                            # LogisticRegression with class_weight='balanced'
│
└── train_regressor.py       # Spending amount regression
                             # GradientBoostingRegressor with quantile loss
                             # For non-zero spending days
```

### Inference (`ml/inference/`)

Model serving and prediction endpoints.

```
inference/
├── __init__.py
├── hurdle_forecast.py       # Two-stage forecast generation:
│                            # - 7-60 day spending forecasts
│                            # - Prediction intervals (confidence bands)
│                            # - P(spend) * E[spend|nonzero] combination
│
├── predict.py              # Category predictions:
│                           # - Transaction categorization
│                           # - Confidence scoring
│                           # - Fallback handling
│
└── forecast.py             # Regression-based forecasting:
                            # - Daily spend prediction
                            # - Trend analysis
```

### Data Preprocessing (`ml/preprocessing/`)

Dataset building and data cleaning.

```
preprocessing/
├── __init__.py
├── build_dataset.py         # Training dataset pipeline:
│                            # - Load transaction history
│                            # - Feature engineering
│                            # - Label creation
│                            # - Train/test split
│
├── build_regression_dataset.py  # Spending amount dataset
├── sanitize.py              # Data quality checks:
│                            # - Outlier detection
│                            # - Missing value handling
│                            # - Duplicate removal
│
└── audit_dataset.py         # Dataset quality audits:
                             # - Distribution analysis
                             # - Label balance checks
```

### Active Learning (`ml/`)

Confidence-based retraining automation.

```
ml/
├── active_learning.py       # Core active learning module:
│                            # - flag_low_confidence_transactions():
│                            #   Flag predictions < 0.6 confidence
│                            # - capture_corrections():
│                            #   Read CSV with corrected categories
│                            # - check_and_trigger_retraining():
│                            #   Auto-retrain when 80+ corrections
│                            # - get_active_learning_report():
│                            #   Status dashboard
```

### Model Artifacts (`ml/models/`)

Trained models with metadata.

```
models/
├── hurdle_stage1_classifier.joblib              # Binary classifier
├── hurdle_stage1_classifier.manifest.json       # Model metadata
├── hurdle_stage1_classifier.metrics.json        # Performance metrics
├── hurdle_stage1_classifier.vXXXXX-XXXXX.joblib # Versioned backup
│
├── hurdle_stage2_quantile_regressor.joblib      # Quantile regressor
├── hurdle_stage2_quantile_regressor.manifest.json
├── hurdle_stage2_quantile_regressor.metrics.json
│
├── daily_spend_regressor.joblib                 # Regression model
├── daily_spend_regressor.manifest.json
└── daily_spend_regressor.metrics.json
```

### Training Data (`ml/data/`)

Datasets for model training and evaluation.

```
data/
├── training_dataset.csv         # Historical transactions:
│                               # - 12,000+ records
│                               # - Features: amount, date, source, etc.
│                               # - Labels: categories, has_spend
│
├── regression_daily_dataset.csv # Daily spending data:
│                               # - Time-series format
│                               # - Aggregated by day
│
├── clean_transactions.csv       # Cleaned transaction data
├── unmatched_transactions.csv   # Transactions without category
├── quarantine_synthetic.csv     # Synthetic/test data
│
├── class_audit.json            # Category distribution audit
├── sanitization_report.json    # Data quality report
└── README.md                   # Data documentation
```

### Experiment Reporting (`ml/`)

Specification compliance tracking.

```
ml/
├── experiment_reporting.py     # ExperimentMetrics class:
│                              # - count_transactions()
│                              # - count_ingestion_source_files()
│                              # - measure_classification_metrics()
│                              # - measure_forecasting_metrics()
│                              # - measure_active_learning_impact()
│                              # - generate_spec_report()
│                              # Generates JSON report with 6 claims
```

### Core Modules (`ml/`)

```
ml/
├── artifacts.py             # Model versioning:
│                            # - save_model_with_version()
│                            # - load_latest_model()
│                            # - VersionedModel wrapper
│
├── utils.py                 # Shared utilities:
│                            # - Data loading
│                            # - Path resolution
│                            # - Feature engineering
│
├── features.py              # Feature extraction:
│                            # - TF-IDF vectorization
│                            # - Temporal features
│                            # - Statistical features
│
└── predict.py              # Prediction wrappers
```

---

## 💻 Frontend (`frontend/`)

React + Vite SPA for dashboards and analytics.

```
frontend/
├── index.html               # HTML entry point
├── vite.config.js          # Vite build configuration
├── vitest.config.js        # Vitest (unit testing)
├── package.json            # npm dependencies
├── package-lock.json       # Lock file
│
└── src/
    ├── main.jsx            # React entry point
    ├── App.jsx             # Root component
    ├── routes.jsx          # Route definitions
    │
    ├── components/         # Reusable UI components
    │   ├── Layout/
    │   ├── Charts/
    │   └── Forms/
    │
    ├── pages/              # Page-level components
    │   ├── Dashboard.jsx
    │   ├── Transactions.jsx
    │   ├── Forecasts.jsx
    │   └── Analytics.jsx
    │
    ├── features/           # Feature modules
    │   ├── transactions/
    │   ├── forecasts/
    │   └── analytics/
    │
    ├── hooks/              # Custom React hooks
    │   ├── useApi.js
    │   ├── useFetch.js
    │   └── useAuth.js
    │
    ├── utils/              # Utility functions
    │   ├── api.js          # API client
    │   ├── formatters.js
    │   └── validators.js
    │
    ├── constants/          # Constants & config
    │   ├── api.js
    │   └── messages.js
    │
    ├── styles/             # CSS/SCSS
    │   ├── index.css
    │   └── variables.css
    │
    └── test/               # Component tests
        ├── App.test.jsx
        └── utils.test.js
```

---

## 📚 Documentation (`docs/`)

Comprehensive guides and API documentation.

```
docs/
├── README.md                        # Documentation index
├── ARCHITECTURE.md                  # Detailed architecture
├── api_docs.md                     # API endpoints reference
├── setup.md                        # Installation guide
├── WORKFLOWS.md                    # Common workflows
├── ml_pipeline.md                  # ML process documentation
├── hurdle_active_learning.md       # Hurdle model & AL guide
│
├── frontend_regression_forecast_plan.md
├── machine_learning_application.md
├── ML_Restructure.md
├── overview_dashboard.md
├── overview_frontend.md
├── regression_prediction_plan.md
└── progress_log.md
```

---

## 🧪 Tests (`tests/`)

Comprehensive test suite with validation.

```
tests/
├── test_hurdle_model.py            # Hurdle model tests:
│                                  # - Dataset loading
│                                  # - Stratified splitting
│                                  # - Metric computation
│                                  # - Stage 1 classifier
│                                  # - Stage 2 regressor
│
├── test_active_learning.py         # Active learning tests:
│                                  # - Low-confidence flagging
│                                  # - Correction capture
│                                  # - Retraining triggers
│                                  # - Status reporting
│
├── test_api.py                    # API endpoint tests
├── test_categorization.py         # Categorization tests
├── test_categorizer.py            # Categorizer unit tests
├── test_ml_pipeline.py            # ML pipeline tests
├── test_ml_regression.py          # Regression model tests
└── test_parser.py                 # Parser tests
```

---

## 📦 Database (`database/`)

Database connection and migration management.

```
database/
├── connection/
│   ├── __init__.py
│   └── session.py              # SQLAlchemy session factory
│
└── migrations/
    ├── README.md
    └── [Migration scripts]
```

---

## 📋 Validation & Configuration

```
BudgetIQ/
├── validate_implementations.py     # Full system validation:
│                                  # - Checks 9 implementation aspects
│                                  # - Validates all modules work together
│                                  # - Generates detailed report
│
├── .gitignore                     # Git exclusion rules
├── pytest.ini                     # Pytest configuration
├── requirements.txt               # Python dependencies:
│                                 # - Django==5.1.6
│                                 # - FastAPI==0.116.0
│                                 # - scikit-learn==1.5.2
│                                 # - And 20+ others
└── .env.example                  # Environment template
```

---

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                  User Interface                          │
│           (React Frontend - Port 5173)                   │
└─────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐   ┌──────────────┐   ┌──────────┐
   │ Django  │   │   FastAPI    │   │ WebSocket│
   │API      │   │   Service    │   │ Events   │
   │Port8000 │   │   Port8001   │   │          │
   └─────────┘   └──────────────┘   └──────────┘
        │              │                │
        └──────────────┼────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐  ┌──────────┐   ┌──────────┐
   │Database │  │  Cache   │   │   ML     │
   │ SQLite  │  │ System   │   │  Models  │
   │         │  │          │   │          │
   └─────────┘  └──────────┘   └──────────┘
        │
  ┌─────────────────┐
  │ ML Pipeline     │
  ├─────────────────┤
  │ Training        │
  │ Inference       │
  │ Active Learning │
  └─────────────────┘
```

---

## 🚀 Environment Setup

### Required Environment Variables

Create `.env` file:
```
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
FASTAPI_PORT=8001
LOG_LEVEL=INFO
```

---

## 📊 File Statistics

- **Python Files**: 50+
- **JavaScript Files**: 30+
- **Test Files**: 10+
- **Documentation**: 15+ markdown files
- **Total Lines of Code**: 5,000+

---

## 🔑 Key Configuration Files

| File | Purpose |
|------|---------|
| `manage.py` | Django CLI entry point |
| `requirements.txt` | Python dependencies |
| `pytest.ini` | Test configuration |
| `frontend/vite.config.js` | Frontend build config |
| `backend/settings.py` | Django settings |
| `.gitignore` | Git exclusion rules |

---

**For more details, see individual module documentation in `docs/`**
