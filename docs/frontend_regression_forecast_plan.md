# Frontend Regression Forecast Plan

## Objective

Integrate regression-based daily spend forecasting into the dashboard so users can view upcoming debit predictions directly in the frontend.

## Scope

In scope:

- define backend forecast API contract,
- add backend endpoint powered by the trained daily spend regressor,
- add frontend hook to fetch forecasts,
- add dashboard forecast panel with key metrics and day-wise predictions.
- add user-selectable forecast horizon and chart visualization.

Out of scope:

- category-level forecasting,
- confidence calibration via quantile models,
- custom model selection in UI.

## API Contract

Endpoint:

- `GET /forecast_daily_spend?days=7`

Response:

- `days`: requested horizon,
- `model_version`: version from model manifest,
- `selected_model`: winning regressor name,
- `last_observed_date`: last date used as historical anchor,
- `forecast`: list of rows with:
  - `date`
  - `predicted_total_debit`
  - `lower_bound`
  - `upper_bound`

Error behavior:

- `400`: invalid horizon or insufficient history,
- `503`: model artifacts unavailable.

## Frontend Design

Dashboard adds a new section: `Spend Forecast (Regression)`.

Contents:

- summary cards:
  - next-day forecast,
  - 7-day forecast total,
  - model version,
  - selected model,
- compact table for next 7 days with predicted debit and confidence band.
- horizon selector (`7`, `14`, `30` days),
- forecast trend chart showing predicted values and lower/upper bounds.
- toggle to overlay recent actual debit against forecast trend.
- state persistence via query params (`forecastDays`, `showForecast`, `showBand`, `showActualOverlay`).

Loading and fallback:

- show skeleton while loading,
- show friendly message when forecast API is unavailable.

## Implementation Phases

### Phase 1 (this implementation)

- backend endpoint + model loading logic,
- frontend hook,
- dashboard forecast panel,
- API tests for endpoint contract.

### Phase 2

- forecast chart visualization,
- user-selectable horizon,
- drilldown linking forecast to historical trend context.

Status:

- Phase 1: completed.
- Phase 2: partially completed (chart + horizon selector implemented).

## Acceptance Criteria

- dashboard renders regression forecast values from API,
- dashboard supports horizon switching (`7`/`14`/`30`) with refreshed API query,
- dashboard renders forecast trend chart and tabular forecast values,
- API test passes for forecast endpoint response shape,
- existing API and ML tests remain green.