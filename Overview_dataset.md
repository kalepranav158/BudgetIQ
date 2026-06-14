# Overview Dataset Report

Generated on: 2026-04-16

## 1) Data Sources Used

- Transaction database: db.sqlite3, table transactions
- Regression dataset: ml/data/regression_daily_dataset.csv
- Model metadata: ml/models/daily_spend_regressor.manifest.json
- Model metrics: ml/models/daily_spend_regressor.metrics.json

## 2) Best Model (Current)

Current selected best model from manifest:

- Model type: regression
- Selected model: linear_regression
- Model version: v20260414T032102Z-a2e95537
- Training rows: 21,840
- Validation rows: 5,461
- Total rows: 27,301

Validation metrics:

- MAE: 0.5819
- RMSE: 14.9210
- MAPE: 0.003845

Candidate comparison:

- linear_regression and ridge currently show the same validation metrics in the saved metrics file.
- Since metrics are tied, linear_regression is selected as the promoted model.

## 3) Dataset Type Analysis (transactions)

### 3.1 Overall size and timeline

- Total transactions: 226
- Date range: 2024-07-01 to 2099-04-13
- Unique source files: 5

Observation:

- The dataset includes future dates (2099), which are likely synthetic/test records mixed with production-like records.

### 3.2 Transaction type distribution

- debit: 213 (94.25%)
- credit: 13 (5.75%)

Insight:

- This is a strongly debit-dominant dataset, so spend analysis is reliable, but credit-side behavior is underrepresented.

### 3.3 Subtype distribution

- transfer_out: 134 (59.29%)
- expense: 77 (34.07%)
- transfer_in: 13 (5.75%)
- atm_withdrawal: 2 (0.88%)

Insight:

- transfer_out and expense dominate behavior, indicating most records are outflow-linked UPI/transfer activity plus normal expenses.

### 3.4 Amount behavior by type

- debit
  - average: 93.25
  - min: 1.00
  - max: 1500.00
- credit
  - average: 831.85
  - min: 1.00
  - max: 5000.00

Insight:

- Credit transactions are fewer but much larger on average.

## 4) Category and Spending Analysis

### 4.1 Total flow

- Total debit: 19,862.85
- Total credit: 10,814.00
- Net flow (credit - debit): -9,048.85

Insight:

- Net is negative, so outflows exceed inflows in the current dataset.

### 4.2 Category spend (debit-led)

- other
  - debit: 15,796.80
  - credit: 10,814.00
  - transactions: 179
  - debit share: 79.53%
- lunch
  - debit: 3,854.05
  - credit: 0.00
  - transactions: 35
  - debit share: 19.40%
- recharge
  - debit: 212.00
  - credit: 0.00
  - transactions: 12
  - debit share: 1.07%

Insights:

- Category other is very dominant. This suggests mapping coverage can be improved to reduce uncategorized or broad-bucket expenses.
- lunch is the second major spend area and already meaningful for budgeting insights.
- recharge is minor in both volume and amount.

### 4.3 Category source quality

- category_source distribution:
  - keyword: 226

Insight:

- All records are currently tagged as keyword source in this snapshot. Regex/account/ML rule contribution is not visible in persisted history yet.

## 5) Monthly Spending Overview

Monthly rollup from transaction table:

- 2024-07: debit 1,743.00, credit 0.00, tx 7
- 2025-04: debit 10,396.30, credit 10,814.00, tx 149
- 2099-01: debit 6,570.00, credit 0.00, tx 60
- 2099-02: debit 42.50, credit 0.00, tx 1
- 2099-04: debit 1,111.05, credit 0.00, tx 9

Peak months:

- Peak debit month: 2025-04 (10,396.30)
- Peak credit month: 2025-04 (10,814.00)

Insight:

- 2025-04 is the most active month by both transaction count and flow.

## 6) Data Quality Checks

Missing/empty fields in transactions:

- missing category_source: 0
- missing confidence: 0
- missing category: 0
- missing subtype: 0

Insight:

- Required analytical fields are now consistently populated for all rows.

## 7) Regression Dataset Profile

File: ml/data/regression_daily_dataset.csv

- Rows: 27,301
- Columns:
  - date
  - target_total_debit
  - lag_1
  - lag_3_mean
  - lag_7_mean
  - lag_14_mean
  - weekday
  - month
  - is_weekend
- Date range: 2024-07-15 to 2099-04-13

Target statistics:

- min: 0.00
- max: 987.60
- average: 0.1164
- weekend ratio in rows: 28.57%

Insight:

- The very low average target indicates many zero-spend days relative to a few spike days.
- This imbalance can affect model behavior and should be considered when interpreting forecast confidence.

## 8) Key Conclusions

1. Current best promoted model is linear_regression (version v20260414T032102Z-a2e95537).
2. Dataset is debit-heavy with transfer_out-dominant subtype behavior.
3. Spending is concentrated in category other (nearly 80% of debit), so mapping enrichment is the highest-impact improvement area.
4. Net flow is negative overall for current data snapshot.
5. Data quality for core classification columns is clean (no nulls in category_source/confidence/category/subtype).
6. Regression target distribution appears sparse with many zeros, suggesting potential gain from handling zero-inflated behavior or segment-wise modeling in future iterations.
