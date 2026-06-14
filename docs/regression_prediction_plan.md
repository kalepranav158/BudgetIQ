# Regression Prediction Plan

## Purpose

This document defines the rollout plan for future spend prediction using regression models.

Primary objective:

- predict future spending amounts (not categories),
- start with daily total debit forecasting,
- evolve into monthly and per-category forecasting.

## Scope

In scope:

- daily spend regression dataset generation,
- baseline regression training and evaluation,
- versioned artifact + manifest governance,
- backend-ready forecasting contract.

Out of scope (for now):

- deep learning forecasters,
- real-time online learning,
- full MLOps registry integration.

## Targets

Phase targets:

1. Next-day total debit prediction.
2. Next 7-day aggregate debit prediction.
3. Next-month total debit prediction.

## Model Candidates

Baseline candidates:

- `LinearRegression`
- `Ridge`

Future candidates:

- `Lasso` / `ElasticNet`
- `RandomForestRegressor`
- `GradientBoostingRegressor`

## Feature Plan

Initial features for daily forecast:

- lag features: `lag_1`, `lag_3_mean`, `lag_7_mean`, `lag_14_mean`
- calendar features: `weekday`, `month`, `is_weekend`

Target:

- `target_total_debit`

## Validation Strategy

Use chronological validation only:

- first 80% rows as train,
- last 20% rows as validation,
- no random shuffling.

Primary metrics:

- MAE
- RMSE
- MAPE (safe denominator)

## Artifact Governance

For each training run:

- save unversioned model for compatibility,
- save versioned model artifact,
- save metrics sidecar,
- save manifest pointing to promoted version.

## Delivery Phases

### Phase 1 (implemented in this sprint)

- build regression dataset exporter,
- train baseline regression models,
- pick winner by validation MAE,
- persist model + metrics + manifest,
- add automated tests.

### Phase 2

- add inference helper and forecast endpoint,
- expose model version and confidence band in API payload.

### Phase 3

- add dashboard forecast cards/overlays,
- add drift monitoring and retraining triggers.

## Acceptance Criteria

Phase 1 is complete when:

- regression dataset CLI exports rows from transaction history,
- baseline trainer produces model artifacts and manifest,
- metrics include train and validation summaries,
- tests validate export and training behavior.