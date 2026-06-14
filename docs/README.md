# BudgetIQ Documentation Index

Last Updated: 2026-04-16

This index groups the existing documentation by domain and records the current doc version for each file.

## Versioning Convention

- Doc versions are tracked as `vYYYY-MM-DD`.
- When a document changes materially, update the version in this index and in the document header.
- Planning documents should stay separate from implementation docs.

## Backend Docs

| File | Version | Purpose |
|---|---|---|
| [setup.md](setup.md) | v2026-04-16 | Local setup, environment variables, and run commands |
| [architecture.md](architecture.md) | v2026-04-16 | Backend pipeline, service flow, and dataflow |
| [api.md](api.md) | v2026-04-16 | Django and FastAPI endpoint reference |
| [api_docs.md](api_docs.md) | v2026-04-16 | Legacy endpoint and integration notes |
| [progress_log.md](progress_log.md) | v2026-04-16 | Chronological progress log |
| [sprint_tracker.md](sprint_tracker.md) | v2026-04-16 | Sprint checklist and execution status |
| [WORKFLOWS.md](WORKFLOWS.md) | v2026-04-16 | Operational workflows and mapping guidance |

## Frontend Docs

| File | Version | Purpose |
|---|---|---|
| [overview_frontend.md](overview_frontend.md) | v2026-04-16 | Frontend route and feature map |
| [overview_dashboard.md](overview_dashboard.md) | v2026-04-16 | Dashboard layout, routes, and visualization plan |
| [frontend_regression_forecast_plan.md](frontend_regression_forecast_plan.md) | v2026-04-16 | Forecast UI integration plan |

## ML Docs

| File | Version | Purpose |
|---|---|---|
| [ml_pipeline.md](ml_pipeline.md) | v2026-04-16 | Transaction classification pipeline and model strategy |
| [machine_learning_application.md](machine_learning_application.md) | v2026-04-16 | ML layer analysis, current status, and target design |
| [regression_prediction_plan.md](regression_prediction_plan.md) | v2026-04-16 | Regression forecasting rollout plan |

## Recommended Reading Order

1. [setup.md](setup.md)
2. [architecture.md](architecture.md)
3. [api.md](api.md)
4. [overview_frontend.md](overview_frontend.md)
5. [ml_pipeline.md](ml_pipeline.md)
6. [regression_prediction_plan.md](regression_prediction_plan.md)
7. [sprint_tracker.md](sprint_tracker.md)

## Next Implementation Gate

Before new code changes, update the relevant doc version here and add the implementation intent to [sprint_tracker.md](sprint_tracker.md).
