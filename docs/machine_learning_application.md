# Machine Learning Application Analysis and Design

## Purpose

This document records the current implementation progress of the ML layer in BrainIQ and defines the target design for the machine learning application.

It covers:

- what is already implemented,
- what is still stubbed or partially wired,
- where the current ML flow is integrated into the backend,
- what needs to be fixed before the ML application is production-ready.

Related planning document:

- `docs/regression_prediction_plan.md` for future spend forecasting with regression models.

## Current ML Status

### Summary

The core ML stack is implemented for feature engineering, dataset export, training, metrics, and runtime-safe inference.

The strongest part of the current system is the hybrid transaction categorization flow:

- rule-based categorization remains primary,
- ML fallback is available and wired into the FastAPI parse flow,
- model loading is runtime-safe,
- confidence and category source metadata are preserved in API flow and database models.

The weakest part is now the more advanced ML lifecycle pieces:

- `ml/features.py` is implemented,
- `ml/predict.py` is implemented and runtime-safe,
- `ml/preprocessing/build_dataset.py` and `ml/training/train_classifier.py` now run against the real Django data model,
- training now writes validation metrics alongside the model artifact,
- dedicated ML unit tests exist for feature building, dataset export, feature engineering, training artifact creation, and inference artifact loading.

The remaining work is model governance rather than basic plumbing.

## Function-by-Function Progress

### `ml/features.py`

Current state: implemented.

- `build_feature_row()` derives structured transaction features.
- `build_features()` converts raw transaction rows into enriched ML-ready records.
- Combined text includes description, counterparty, amount bucket, weekday, month, year, type, and subtype tokens.

Progress rating: 85%.

### `ml/predict.py`

Current state: implemented and runtime-safe.

- `HybridTransactionCategorizer` lazily loads classifier and vectorizer artifacts.
- Prediction returns `None` when artifacts are missing or invalid.
- The module exposes a CLI entry point for local inference.

Progress rating: 90%.

### `ml/preprocessing/build_dataset.py`

Current state: implemented and runnable.

- `build_dataset(output_path)` exports labeled transactions into CSV.
- It reads from the Django `Transaction` model and writes structured columns including date, text, amount, subtype, and category.
- It uses the shared ML feature builder so export and training stay aligned.

Remaining limitation:

- It still depends on the current Django transaction schema, so any schema change should be reflected here and in the trainer.

Progress rating: 90%.

### `ml/training/train_classifier.py`

Current state: implemented and runnable.

- `train_model(dataset_path, model_path, vectorizer_path)` trains a TF-IDF + Logistic Regression classifier.
- It reads a CSV dataset, builds enriched text features from the shared ML feature builder, fits a classifier, and writes `joblib` artifacts.
- It performs a train/validation split when the dataset is large enough and persists metrics as a JSON sidecar next to the model artifact.
- It supports CLI execution through `main()`.

Remaining gaps:

- There is no model versioning or promotion workflow yet.

Progress rating: 95%.

### `ml/inference/predict.py`

Current state: implemented and runtime-safe.

- `HybridTransactionCategorizer` lazily loads model and vectorizer artifacts.
- If artifacts are missing or loading fails, prediction returns `None` instead of crashing.
- `predict_category()` transforms text and returns a category only if it is in the allowed set.
- `main()` provides a CLI prediction entry point.

This module is already integrated into the FastAPI parse flow.

Progress rating: 90%.

### `ml/inference/__init__.py`

Current state: package marker only.

- Contains no runtime logic.
- No issue by itself.

Progress rating: 100% as a package initializer.

### `ml/preprocessing/__init__.py`

Current state: package marker only.

- Contains no runtime logic.
- No issue by itself.

Progress rating: 100% as a package initializer.

### `ml/training/__init__.py`

Current state: package marker only.

- Contains no runtime logic.
- No issue by itself.

Progress rating: 100% as a package initializer.

## Backend Integration Status

### FastAPI parsing flow

The ML fallback is already wired into the parser pipeline in `backend/fastapi_service/main.py`.

Current behavior:

1. PDF transactions are extracted.
2. Rule mappings are built.
3. `HybridTransactionCategorizer` predicts a fallback category.
4. `categorize_transaction()` merges rules + ML fallback.
5. Category source and confidence are attached to each transaction.
6. Unmatched rows are logged for future ML training.
7. Transactions are optionally persisted.

### Database persistence

The database model already stores ML metadata:

- `category_source`
- `confidence`

This means prediction provenance is preserved and can be analyzed later.

### Pagination and retrieval

The transaction retrieval endpoint supports pagination now.

- `limit`
- `offset`
- sorted by `-date, -id`

## What Is Implemented Well

- Hybrid categorization exists and works in the request flow.
- Runtime-safe model loading prevents crashes when artifacts are missing.
- Metadata persistence is available for category source and confidence.
- Unmatched fallback rows are written to `ml/data/unmatched_transactions.csv`.
- The parser API supports pagination.
- Core API tests already cover ML fallback and pagination behavior.

## Current Gaps

### High priority

- Artifact versioning exists, but there is no central model registry or automated promotion workflow yet.

### Medium priority

- `ml/features.py` now exists, but it should be expanded if model quality is not strong enough.
- Metrics are captured, but there is no promotion policy based on those metrics.

### Lower priority

- No explicit retraining workflow exists.
- No active learning loop from corrected labels.
- No concept drift checks.
- No scheduled retraining or model promotion flow.

## Target Design for the ML Application

### Goal

The ML application should become a clean, reproducible transaction intelligence pipeline that can:

- build labeled datasets from persisted transactions,
- engineer features consistently,
- train and evaluate a classifier,
- save versioned artifacts,
- serve predictions through the backend hybrid flow,
- collect feedback from unmatched or corrected records.

### Recommended ML Architecture

#### 1. Data preparation layer

Responsibilities:

- normalize transaction text,
- extract useful fields from descriptions,
- export training rows with labels,
- maintain a stable schema for text, counterparty, category, subtype, and source metadata.

#### 2. Feature engineering layer

Responsibilities:

- create reusable text normalization helpers,
- build merchant and counterparty features,
- optionally add transaction amount buckets, day-of-week, month, and direction features,
- keep training and inference feature logic aligned.

#### 3. Training layer

Responsibilities:

- load the dataset,
- split train and validation sets,
- train baseline TF-IDF + Logistic Regression,
- report metrics,
- persist model and vectorizer artifacts,
- store model metadata such as version, date, and score.

#### 4. Inference layer

Responsibilities:

- lazily load model artifacts,
- predict fallback category only when rule logic does not resolve the category,
- return `None` safely when the model is unavailable,
- expose CLI and backend-friendly entry points.

#### 5. Feedback loop

Responsibilities:

- log unmatched items,
- capture corrections from human review,
- periodically rebuild training data,
- retrain on a regular cadence.

## Proposed ML Flow

```text
Transactions in DB
  -> dataset export
  -> feature normalization
  -> model training
  -> artifact saving
  -> runtime inference in FastAPI
  -> unmatched logging / correction feedback
  -> retraining cycle
```

## Implementation Plan

### Phase 1: Make the current ML path clean and runnable

- Keep dataset export and training aligned with the shared feature builder.
- Add direct unit tests for dataset building, feature engineering, and training inputs.

### Phase 2: Formalize the feature schema

- Define the exact feature columns used by training and inference.
- Keep feature generation deterministic.
- Document any text normalization rules.

### Phase 3: Add model evaluation

- Split labeled data into train and validation sets.
- Track accuracy, macro F1, and per-class metrics.
- Refuse to promote a model that performs worse than the last approved baseline.

### Phase 4: Add artifact governance

- Save model metadata alongside artifacts.
- Record training date, dataset size, and performance score.
- Make artifact paths configurable.

### Phase 5: Close the feedback loop

- Use unmatched logging as a training source.
- Add a manual review workflow for corrected labels.
- Retrain on a regular cadence.

## Success Criteria

The ML application should be considered ready when:

- dataset export runs without broken imports,
- training runs end-to-end and writes artifacts,
- inference works with and without artifacts present,
- feature generation is shared between training and inference,
- model quality is measured before promotion,
- tests cover the ML pipeline components,
- backend integration continues to preserve category source and confidence.

## Current Verdict

The ML application is partially implemented and backend-integrated, but not yet complete as a standalone training-and-inference system.

Best current status:

- inference path: mostly ready,
- training path: partially ready,
- feature engineering: implemented,
- evaluation and model governance: not started,
- backend hybrid categorization: working.
