# ML Restructure Plan — BudgetIQ

**Document Type**: Implementation-ready ML roadmap
**Last Updated**: 2026-04-16
**Scope**: Transaction category classification + daily spend regression forecasting

---

## Table of Contents

1. [Current State Diagnosis](#1-current-state-diagnosis)
2. [Critical Dataset Problems](#2-critical-dataset-problems)
3. [Model Selection Analysis](#3-model-selection-analysis)
4. [Restructure Workflow Overview](#4-restructure-workflow-overview)
5. [Phase 1 — Data Triage and Sanitization](#5-phase-1--data-triage-and-sanitization)
6. [Phase 2 — Feature Maturity](#6-phase-2--feature-maturity)
7. [Phase 3 — Classification Pipeline Rebuild](#7-phase-3--classification-pipeline-rebuild)
8. [Phase 4 — Regression Pipeline Rebuild](#8-phase-4--regression-pipeline-rebuild)
9. [Phase 5 — Evaluation and Governance](#9-phase-5--evaluation-and-governance)
10. [Phase 6 — Inference Integration and Feedback Loop](#10-phase-6--inference-integration-and-feedback-loop)
11. [File and Folder Structure](#11-file-and-folder-structure)
12. [Dependency Map](#12-dependency-map)
13. [Risk Register](#13-risk-register)
14. [Source References](#14-source-references)

---

## 1. Current State Diagnosis

### 1.1 What exists

| Component | Status | Notes |
|---|---|---|
| TF-IDF + Logistic Regression classifier | Implemented | Baseline only; no class balance handling |
| LinearRegression / Ridge regressor | Implemented | Tied validation metrics — sign of data contamination |
| Dataset export (`build_dataset.py`) | Implemented | Pulls from Django Transaction model |
| Regression dataset exporter | Implemented | 27,301 rows — heavily inflated by synthetic dates |
| Manifest + metrics governance | Implemented | Version tagging in place |
| ML fallback in FastAPI parse flow | Wired | Returns `None` safely when artifacts missing |
| Category source + confidence persistence | Implemented | All records show `keyword` source; ML contribution is zero |

### 1.2 What the dataset report reveals

**Classification dataset** (226 transactions):
- Debit-dominant: 94.25% debit, 5.75% credit
- Category spread is extremely imbalanced: `other` = 79.53% of all debit spend
- `lunch` = 19.4%, `recharge` = 1.07%; no `tea`, `extra`, or `cash_withdrawal` representation
- 100% of records tagged `keyword` source — ML fallback has never been exercised on real data
- 69 transactions have dates in 2099 (synthetic/test records present in production table)

**Regression dataset** (27,301 rows, 2024-07-15 to 2099-04-13):
- Target mean = 0.1164, max = 987.60 — extreme zero inflation
- Linear and Ridge show identical validation metrics — model is effectively predicting near-constant zero
- Future-date rows (2099) dominate the dataset and introduce lag feature leakage
- MAPE = 0.38% is artifically low because the model is predicting zeros on zero-target rows

**Root cause summary**: The dataset is contaminated with synthetic test records, is severely class-imbalanced for classification, and has a zero-inflated regression target. Any model trained on this data as-is will report misleadingly good metrics while performing poorly on real spend prediction.

---

## 2. Critical Dataset Problems

Sorted by severity and impact on model quality.

### Problem 1 — Synthetic future-date contamination (CRITICAL)

- 69 of 226 transactions (30.5%) have dates in 2099
- The regression dataset has rows from 2099-01 through 2099-04 with non-trivial spend values (e.g., 2099-01: ₹6,570 debit across 60 transactions)
- Lag features computed over these rows are meaningless: `lag_1` for a 2099-01-02 row references a 2099-01-01 value, not real behavioral history
- Impact: the model learns from temporal patterns that do not exist in real data

**Fix**: Hard filter — exclude any row with `date.year > 2026` from all datasets. Flag these rows in a quarantine table for manual review.

### Problem 2 — Zero-inflated regression target (HIGH)

- Average daily debit = 0.1164 across 27,301 rows — the overwhelming majority of rows have `target_total_debit = 0`
- This happens because the regression dataset is built from a daily time series spanning every calendar day, most of which had no recorded transactions
- A standard linear regressor minimizes squared error by predicting near-zero everywhere, achieving low RMSE but giving useless forecasts for active spend days
- Weekend ratio = 28.57%, suggesting calendar density is correct but financial density is not

**Fix**: Use a two-stage hurdle model. Stage 1: binary classifier (spend day vs. zero day). Stage 2: regressor trained only on non-zero spend days. Combine predictions at inference time.

### Problem 3 — Severe class imbalance in classification (HIGH)

- `other`: 79.53% of debit, 179 transactions
- `lunch`: 19.4%, 35 transactions
- `recharge`: 1.07%, 12 transactions
- `tea`, `extra`, `cash_withdrawal`: 0 representation in current data
- A naive classifier will achieve ~80% accuracy by predicting `other` for everything — useless for budgeting

**Fix**: Apply class-weighted training. Use stratified sampling if adding synthetic minority examples. Evaluate per-class F1, not overall accuracy.

### Problem 4 — Regression dataset scale mismatch (MEDIUM)

- Training rows: 21,840 (of which most have zero target)
- Validation rows: 5,461
- Linear and Ridge metrics are identical: MAE=0.5819, RMSE=14.92, MAPE=0.0038
- This near-identical result indicates neither model has learned any meaningful signal; both are outputting the same near-zero constant

**Fix**: After synthetic data removal and zero-day filtering, the real training set will shrink significantly. Recalibrate train/validation split to remain chronological.

### Problem 5 — Missing category coverage in ML training data (MEDIUM)

- Three valid spend categories have zero transactions in the current export: `tea`, `extra`, `cash_withdrawal`
- The ML classifier cannot learn these classes and will never predict them
- If rules fail to catch a `tea` transaction, it falls into `other` silently

**Fix**: Do not train on categories with fewer than 5 examples. Mark those as rule-only categories and document this explicitly. Expand training data before enabling ML for those classes.

### Problem 6 — All category_source values are `keyword` (LOW-MEDIUM)

- No evidence that regex or account-rule mappings have contributed to any persisted record
- ML fallback is wired but has never been exercised in production
- This means the classifier has never been validated on real inference

**Fix**: After fixing rule coverage, run a retroactive re-categorization pass on the 226 transactions using the current rule stack to populate realistic `category_source` values. This gives the ML layer proper training signal.

---

## 3. Model Selection Analysis

### 3.1 Classification models — ranking and rationale

The task is short-text multi-class classification over 6–7 spending categories with severe class imbalance and a small labeled dataset (up to ~157 real transactions after decontamination).

#### Tier 1 — Recommended for this dataset size and text length

| Model | Why it fits | Key config |
|---|---|---|
| **TF-IDF + LogisticRegression (class_weight='balanced')** | Interpretable, fast, works on short merchant text, handles imbalance via class weights | `C=1.0`, `solver='lbfgs'`, `max_iter=1000`, `class_weight='balanced'` |
| **TF-IDF + SGDClassifier (modified Huber)** | Online-capable, tolerant to label noise, good for short text | `loss='modified_huber'`, `class_weight='balanced'`, `alpha=1e-4` |
| **TF-IDF + LinearSVC** | Strong for imbalanced multi-class, better margin separation than LogReg on small sets | `class_weight='balanced'`, `C=0.5` |

#### Tier 2 — Recommended when training set exceeds 500 real transactions

| Model | Why it fits | Key config |
|---|---|---|
| **LightGBM (text features as TF-IDF → dense)** | Handles class imbalance natively via `is_unbalance=True`, produces calibrated probabilities | `objective='multiclass'`, `num_leaves=31`, `is_unbalance=True` |
| **fastText** | Excellent for merchant name classification — subword embeddings capture `ZOMATO`, `ZOMA`, `ZOM` variants | `epoch=25`, `lr=0.1`, `wordNgrams=2` |

#### Tier 3 — Future only (requires 2000+ examples or fine-tuning budget)

| Model | Notes |
|---|---|
| Sentence-BERT + cosine classifier | Semantic understanding of payment descriptions |
| DistilBERT fine-tuned | Only if categories become complex prose descriptions |

**Recommended immediately**: Stick with TF-IDF + LogisticRegression, but add `class_weight='balanced'` and switch evaluation to macro F1. This single change will expose how poorly the model handles minority categories and drive better data collection.

### 3.2 Regression models — ranking and rationale

The task is time-series daily spend forecasting with a zero-inflated target, small real history (~7 real months of data), and lag/calendar features.

#### Recommended architecture: Two-stage hurdle model

**Stage 1 — Spend-day classifier** (binary: spend > 0 or not)

| Model | Why | Config |
|---|---|---|
| **LogisticRegression** | Simple, interpretable, calibrated probability of a spend day | `class_weight='balanced'`, features: lag flags + calendar |
| **GradientBoostingClassifier** | Handles nonlinear interactions between weekday and lag | `n_estimators=100`, `max_depth=3` |

**Stage 2 — Spend magnitude regressor** (trained only on days where spend > 0)

| Model | Why | Config |
|---|---|---|
| **Ridge** | Regularized, handles small datasets well, stable | `alpha=1.0`, chronological CV |
| **HuberRegressor** | Robust to amount outliers (large one-off transactions) | `epsilon=1.35`, `alpha=0.01` |
| **QuantileRegressor (q=0.1, 0.5, 0.9)** | Native confidence band production without post-hoc heuristics | Three separate fits; combine for lower/median/upper |
| **LightGBM (Tweedie objective)** | Handles zero-inflated spend natively in a single model; best when data grows | `objective='tweedie'`, `tweedie_variance_power=1.5` |

**Recommended immediately**: HuberRegressor on real non-zero spend days (after synthetic data removal). Add QuantileRegressor (0.1/0.9) for confidence bands. This replaces the current linear model that is predicting near-zero everywhere.

**Recommended when 12+ months of real data exist**: LightGBM with Tweedie objective as a single-model replacement for the two-stage setup.

#### Why not ARIMA or Prophet right now

- ARIMA requires a stationary, continuous, dense time series — the current data has months with 7 transactions and months with 149
- Prophet requires at minimum 2 full seasonal cycles (2 years) for meaningful seasonality detection
- Both are viable at 18+ months of real data

---

## 4. Restructure Workflow Overview

```
Raw transaction DB (contaminated)
        |
        v
[Phase 1] DATA TRIAGE
  - Filter synthetic dates (year > 2026)
  - Quarantine 2099 records
  - Validate real date range
  - Deduplicate
        |
        v
[Phase 2] FEATURE MATURITY
  - Outlier detection and treatment (IQR + winsorization)
  - Transaction-level feature enrichment
  - Regression dataset rebuild from clean data only
  - Class distribution audit
        |
        v
[Phase 3] CLASSIFICATION PIPELINE
  - Rebuild training set from clean transactions
  - Apply class_weight='balanced'
  - Train TF-IDF + LogReg (balanced)
  - Evaluate: macro F1, per-class report
  - Compare with LinearSVC
  - Promote best artifact
        |
        v
[Phase 4] REGRESSION PIPELINE
  - Build hurdle dataset (binary: spend/no-spend) from clean data
  - Build magnitude dataset (non-zero spend days only)
  - Train Stage 1: binary classifier
  - Train Stage 2: HuberRegressor + QuantileRegressor
  - Evaluate: MAE on non-zero days, coverage of confidence band
  - Promote best artifact
        |
        v
[Phase 5] EVALUATION AND GOVERNANCE
  - Per-class classification report (not just accuracy)
  - Regression MAE on real dates only
  - Model promotion policy: must beat baseline on real-date validation
  - Version manifest update
        |
        v
[Phase 6] INFERENCE INTEGRATION
  - Update FastAPI hybrid categorizer with balanced classifier
  - Update forecast endpoint to use hurdle model
  - Add confidence band from QuantileRegressor
  - Log unmatched for retraining
```

---

## 5. Phase 1 — Data Triage and Sanitization

### Objective

Produce a clean, real-world-only transaction dataset and a corresponding regression time series. No model should ever see synthetic 2099 data.

### 5.1 Date decontamination

```python
# ml/preprocessing/sanitize.py

SYNTHETIC_YEAR_THRESHOLD = 2027  # Anything >= this year is quarantine

def split_real_vs_synthetic(df: pd.DataFrame, date_col: str = "date") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (real_df, quarantine_df).
    real_df: rows with date.year < SYNTHETIC_YEAR_THRESHOLD
    quarantine_df: rows with date.year >= SYNTHETIC_YEAR_THRESHOLD
    """
    df[date_col] = pd.to_datetime(df[date_col])
    mask = df[date_col].dt.year < SYNTHETIC_YEAR_THRESHOLD
    return df[mask].copy(), df[~mask].copy()
```

Action items:
- Run this split on both `transactions` table and `ml/data/regression_daily_dataset.csv`
- Write quarantine records to `ml/data/quarantine_synthetic.csv` for manual review
- Log count of quarantined rows in the sanitization report

Expected outcome after decontamination:
- Real transactions: ~157 rows (226 - 69 synthetic)
- Real regression rows: rows from 2024-07-01 to current date only
- Real unique months: 2 (Jul 2024 and Apr 2025)

### 5.2 Deduplication

```python
# Check for duplicate (date, description, amount, type) combinations
df.drop_duplicates(subset=["date", "description", "amount", "type"], keep="first", inplace=True)
```

### 5.3 Outlier detection — transaction amounts

Use IQR-based detection per transaction type (debit/credit separately).

```python
def flag_amount_outliers(df: pd.DataFrame, group_col: str = "type", amount_col: str = "amount") -> pd.DataFrame:
    """
    Adds 'is_outlier' column. Uses 1.5 * IQR rule per group.
    """
    df["is_outlier"] = False
    for group, gdf in df.groupby(group_col):
        q1 = gdf[amount_col].quantile(0.25)
        q3 = gdf[amount_col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_mask = (gdf[amount_col] < lower) | (gdf[amount_col] > upper)
        df.loc[gdf[outlier_mask].index, "is_outlier"] = True
    return df
```

**Do not remove outliers from the transaction record.** They are real spend events. Instead:
- Flag them with `is_outlier=True`
- For regression training: winsorize at 99th percentile per group so a single ₹5,000 credit does not dominate gradient
- For classification training: keep as-is; amount outliers do not affect text categorization

### 5.4 Regression target winsorization

```python
from scipy.stats.mstats import winsorize

# Applied only to regression dataset, not to raw transactions
df["target_total_debit_winsorized"] = winsorize(df["target_total_debit"], limits=[0.0, 0.01])
# Caps the top 1% of spend values to reduce regressor sensitivity to one-off spikes
```

### 5.5 Sanitization report output

Write `ml/data/sanitization_report.json` after every sanitization run:

```json
{
  "run_date": "2026-04-16",
  "input_transactions": 226,
  "quarantined_synthetic": 69,
  "real_transactions": 157,
  "duplicates_removed": 0,
  "amount_outliers_flagged_debit": 4,
  "amount_outliers_flagged_credit": 1,
  "regression_rows_before": 27301,
  "regression_rows_after_decontamination": 320,
  "real_date_range": ["2024-07-01", "2025-04-30"]
}
```

### Phase 1 Acceptance Criteria

- [ ] `ml/data/clean_transactions.csv` exists with only real-date rows
- [ ] `ml/data/quarantine_synthetic.csv` exists with 2099 records
- [ ] `ml/data/sanitization_report.json` written with correct counts
- [ ] Zero rows with `date.year >= 2027` in clean dataset
- [ ] `is_outlier` column present on all clean transaction rows

---

## 6. Phase 2 — Feature Maturity

### Objective

Enrich the clean transaction dataset with ML-ready features. Rebuild the regression time series from clean data only. Audit class distribution and document coverage gaps honestly.

### 6.1 Classification feature enrichment

Extend the existing `build_feature_row()` in `ml/features.py`:

```python
def build_feature_row(txn: dict) -> dict:
    """
    Current fields (keep all existing):
      combined_text, amount_bucket, weekday, month, year, type, subtype

    Add:
    """
    row = {}

    # --- Text features ---
    description = str(txn.get("description", "")).upper().strip()
    row["description_clean"] = description

    # Extract UPI counterparty if present
    row["counterparty"] = extract_upi_counterparty(description)  # existing helper

    # Bigram prefix for merchant name detection (first 2 words of description)
    tokens = description.split()
    row["prefix_bigram"] = " ".join(tokens[:2]) if len(tokens) >= 2 else tokens[0] if tokens else ""

    # Combined text for TF-IDF (keep existing)
    row["combined_text"] = build_combined_text(txn)

    # --- Amount features ---
    amount = float(txn.get("amount", 0))
    row["amount"] = amount
    row["amount_log1p"] = math.log1p(amount)   # compress large values
    row["amount_bucket"] = assign_amount_bucket(amount)  # existing

    # --- Temporal features ---
    date = pd.to_datetime(txn.get("date"))
    row["weekday"] = date.weekday()
    row["month"] = date.month
    row["is_weekend"] = int(date.weekday() >= 5)
    row["day_of_month"] = date.day

    # --- Transaction metadata ---
    row["type"] = txn.get("type", "")
    row["subtype"] = txn.get("subtype", "")
    row["is_upi"] = int("UPI" in description)
    row["is_transfer"] = int("TRANSFER" in description or txn.get("subtype") == "transfer_out")

    return row
```

New fields added and why:

| Field | Reason |
|---|---|
| `amount_log1p` | Compresses the ₹1–₹5,000 range; prevents large credit values from distorting log-scale patterns |
| `prefix_bigram` | Captures "UPI/ZOMATO" vs "ATM CASH" patterns missed by full-string TF-IDF |
| `is_upi` | Binary flag — UPI transactions have structurally different descriptions than ATM/NEFT |
| `is_transfer` | Disambiguates subtype-level spending from counterparty UPI activity |
| `day_of_month` | Salary-aligned credit typically hits on fixed days; useful for credit/transfer classification |

### 6.2 Regression dataset rebuild

After Phase 1 sanitization, rebuild `ml/data/regression_daily_dataset.csv` from the clean transaction set only.

```python
# ml/preprocessing/build_regression_dataset.py

def build_regression_dataset(clean_txn_path: str, output_path: str) -> None:
    df = pd.read_csv(clean_txn_path, parse_dates=["date"])

    # Daily aggregation — real dates only
    daily = df[df["type"] == "debit"].groupby("date")["amount"].sum().reset_index()
    daily.columns = ["date", "target_total_debit"]

    # Build full calendar (no gaps) from min to max real date
    full_range = pd.date_range(start=daily["date"].min(), end=daily["date"].max(), freq="D")
    daily = daily.set_index("date").reindex(full_range, fill_value=0.0).reset_index()
    daily.columns = ["date", "target_total_debit"]

    # Apply winsorization
    daily["target_total_debit_winsorized"] = winsorize(daily["target_total_debit"], limits=[0.0, 0.01])

    # Build lag features
    daily["lag_1"]      = daily["target_total_debit"].shift(1).fillna(0)
    daily["lag_3_mean"] = daily["target_total_debit"].shift(1).rolling(3).mean().fillna(0)
    daily["lag_7_mean"] = daily["target_total_debit"].shift(1).rolling(7).mean().fillna(0)
    daily["lag_14_mean"]= daily["target_total_debit"].shift(1).rolling(14).mean().fillna(0)

    # Binary hurdle target
    daily["is_spend_day"] = (daily["target_total_debit"] > 0).astype(int)

    # Calendar features
    daily["weekday"]    = daily["date"].dt.weekday
    daily["month"]      = daily["date"].dt.month
    daily["is_weekend"] = (daily["date"].dt.weekday >= 5).astype(int)
    daily["day_of_month"] = daily["date"].dt.day

    # Drop rows where lag_14_mean is NaN (first 14 days)
    daily = daily.dropna()

    daily.to_csv(output_path, index=False)
    print(f"Regression dataset: {len(daily)} rows written to {output_path}")
```

Expected output size after decontamination: approximately 270–310 rows (2024-07-15 to 2025-04-30, minus 14-day lag warmup).

### 6.3 Class distribution audit

After rebuilding the clean classification dataset, generate a class distribution report:

```python
# ml/preprocessing/audit_dataset.py

def audit_class_distribution(df: pd.DataFrame, label_col: str = "category") -> dict:
    counts = df[label_col].value_counts()
    total = len(df)
    report = {}
    for cat, count in counts.items():
        report[cat] = {
            "count": int(count),
            "pct": round(100 * count / total, 2),
            "trainable": count >= 5,  # minimum threshold to train a class
            "note": "OK" if count >= 20 else ("sparse" if count >= 5 else "SKIP — below threshold")
        }
    return report
```

Classes with fewer than 5 examples must be excluded from ML training and documented as rule-only. Classes with 5–19 examples are trainable but require `class_weight='balanced'`.

### Phase 2 Acceptance Criteria

- [ ] `ml/data/regression_daily_dataset.csv` rebuilt from clean transactions only
- [ ] Regression dataset has no rows with `date.year >= 2027`
- [ ] `is_spend_day` binary column present in regression dataset
- [ ] `target_total_debit_winsorized` column present
- [ ] Classification dataset has `amount_log1p`, `is_upi`, `is_transfer`, `prefix_bigram` columns
- [ ] Class audit report written to `ml/data/class_audit.json`
- [ ] Classes below threshold documented and excluded from training

---

## 7. Phase 3 — Classification Pipeline Rebuild

### Objective

Train a balanced, properly evaluated transaction category classifier. Replace the current naive LogReg with a class-weight-balanced variant and measure performance on minority classes.

### 7.1 Training changes

```python
# ml/training/train_classifier.py (changes)

from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import StratifiedShuffleSplit

def train_model(dataset_path: str, model_dir: str) -> dict:
    df = pd.read_csv(dataset_path)

    # --- Load class audit and drop under-threshold classes ---
    with open("ml/data/class_audit.json") as f:
        audit = json.load(f)
    trainable_classes = [c for c, v in audit.items() if v["trainable"]]
    df = df[df["category"].isin(trainable_classes)]

    X = df["combined_text"].values
    y = df["category"].values

    # --- Stratified split (respects class proportions) ---
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, val_idx = next(sss.split(X, y))
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    # --- Model A: LogReg balanced ---
    pipe_lr = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", LogisticRegression(
            class_weight="balanced",
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            multi_class="multinomial"
        ))
    ])
    pipe_lr.fit(X_train, y_train)
    preds_lr = pipe_lr.predict(X_val)
    f1_lr = f1_score(y_val, preds_lr, average="macro")

    # --- Model B: LinearSVC balanced + Platt calibration ---
    pipe_svc = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", CalibratedClassifierCV(
            LinearSVC(class_weight="balanced", C=0.5, max_iter=2000),
            cv=3
        ))
    ])
    pipe_svc.fit(X_train, y_train)
    preds_svc = pipe_svc.predict(X_val)
    f1_svc = f1_score(y_val, preds_svc, average="macro")

    # --- Select winner ---
    winner_name = "logreg_balanced" if f1_lr >= f1_svc else "linearsvc_balanced"
    winner_pipe = pipe_lr if f1_lr >= f1_svc else pipe_svc
    winner_f1 = max(f1_lr, f1_svc)

    # --- Full classification report ---
    winner_preds = winner_pipe.predict(X_val)
    report = classification_report(y_val, winner_preds, output_dict=True)

    # --- Persist ---
    version = f"v{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    joblib.dump(winner_pipe, f"{model_dir}/classifier_{version}.joblib")
    joblib.dump(winner_pipe, f"{model_dir}/classifier.joblib")  # unversioned alias

    metrics = {
        "version": version,
        "winner": winner_name,
        "macro_f1": round(winner_f1, 4),
        "logreg_balanced_f1": round(f1_lr, 4),
        "linearsvc_balanced_f1": round(f1_svc, 4),
        "per_class_report": report,
        "trainable_classes": trainable_classes,
        "train_size": len(X_train),
        "val_size": len(X_val),
    }
    with open(f"{model_dir}/classifier.metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics
```

### 7.2 What to measure (not just accuracy)

Metric priority order for classification:

1. **Macro F1** — primary. Treats all classes equally; exposes minority class failure
2. **Per-class F1** — secondary. Any class with F1 < 0.5 must be flagged
3. **Weighted F1** — informational only. Will be high due to `other` dominance; do not use for promotion decisions
4. **Overall accuracy** — do not use for imbalanced datasets; misleading

Promotion gate: new model must achieve macro F1 ≥ current baseline on the validation set. If no baseline exists, any model with macro F1 > 0.40 on the current dataset is promotable.

### 7.3 Handling the `other` category

`other` at 79.53% will dominate training signal even with balanced weights. Two mitigations:

**Mitigation A** (immediate): Apply `class_weight='balanced'` as above. This downweights `other` and upweights `lunch` and `recharge` during gradient computation.

**Mitigation B** (when more data is available): Relabel ambiguous transactions in `other` bucket manually. Any transaction that could be `extra`, `tea`, or `cash_withdrawal` but fell through rules should be relabeled before the next training run.

### Phase 3 Acceptance Criteria

- [ ] Classifier trained with `class_weight='balanced'`
- [ ] Macro F1 reported in `classifier.metrics.json`
- [ ] Per-class F1 report present for each trainable class
- [ ] Under-threshold classes excluded and listed explicitly
- [ ] Artifact versioned and manifest updated
- [ ] `classifier.joblib` (unversioned alias) updated for FastAPI inference pickup

---

## 8. Phase 4 — Regression Pipeline Rebuild

### Objective

Replace the zero-predicting linear model with a two-stage hurdle model that separately predicts whether a day will have spend, and how much that spend will be. Add QuantileRegressor for native confidence bands.

### 8.1 Hurdle model architecture

```
Input: lag features + calendar features for a target date
        |
        v
   [Stage 1: Binary Classifier]
   "Will there be any spend today?"
        |
   P(spend) < threshold → predicted_debit = 0, bounds = (0, low_percentile)
        |
   P(spend) >= threshold
        |
        v
   [Stage 2: Magnitude Regressor]
   "Given spend will occur, how much?"
   Trained ONLY on non-zero spend days
        |
        v
   predicted_debit = Stage2 output
   lower_bound = Q10 Regressor output
   upper_bound = Q90 Regressor output
```

### 8.2 Implementation

```python
# ml/training/train_regressor.py

from sklearn.linear_model import LogisticRegression, HuberRegressor, QuantileRegressor, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

FEATURE_COLS = ["lag_1", "lag_3_mean", "lag_7_mean", "lag_14_mean",
                "weekday", "month", "is_weekend", "day_of_month"]
BINARY_TARGET = "is_spend_day"
MAG_TARGET    = "target_total_debit_winsorized"

def train_hurdle_model(dataset_path: str, model_dir: str) -> dict:
    df = pd.read_csv(dataset_path, parse_dates=["date"])

    # Chronological split (no shuffling)
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    val_df   = df.iloc[split_idx:]

    X_train = train_df[FEATURE_COLS].values
    X_val   = val_df[FEATURE_COLS].values

    # -------------------------------------------------------
    # Stage 1: Binary classifier (spend vs. no-spend)
    # -------------------------------------------------------
    y_bin_train = train_df[BINARY_TARGET].values
    y_bin_val   = val_df[BINARY_TARGET].values

    stage1 = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", C=1.0, max_iter=500))
    ])
    stage1.fit(X_train, y_bin_train)
    spend_prob_val = stage1.predict_proba(X_val)[:, 1]
    spend_threshold = 0.4  # tunable; lower = more days predicted as spend days

    # -------------------------------------------------------
    # Stage 2: Magnitude regressor (non-zero train days only)
    # -------------------------------------------------------
    nonzero_mask_train = train_df[MAG_TARGET] > 0
    X_mag_train = X_train[nonzero_mask_train]
    y_mag_train = train_df.loc[nonzero_mask_train, MAG_TARGET].values

    # Median model (point estimate)
    stage2_median = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", HuberRegressor(epsilon=1.35, alpha=0.01, max_iter=300))
    ])
    stage2_median.fit(X_mag_train, y_mag_train)

    # Lower bound model (q=0.10)
    stage2_lower = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", QuantileRegressor(quantile=0.10, alpha=0.1, solver="highs"))
    ])
    stage2_lower.fit(X_mag_train, y_mag_train)

    # Upper bound model (q=0.90)
    stage2_upper = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", QuantileRegressor(quantile=0.90, alpha=0.1, solver="highs"))
    ])
    stage2_upper.fit(X_mag_train, y_mag_train)

    # -------------------------------------------------------
    # Evaluation on non-zero validation days only
    # -------------------------------------------------------
    nonzero_mask_val = val_df[MAG_TARGET] > 0
    X_val_nz   = X_val[nonzero_mask_val]
    y_val_nz   = val_df.loc[nonzero_mask_val, MAG_TARGET].values

    preds_median = stage2_median.predict(X_val_nz)
    preds_lower  = stage2_lower.predict(X_val_nz)
    preds_upper  = stage2_upper.predict(X_val_nz)

    mae  = mean_absolute_error(y_val_nz, preds_median)
    rmse = np.sqrt(mean_squared_error(y_val_nz, preds_median))
    coverage = np.mean((y_val_nz >= preds_lower) & (y_val_nz <= preds_upper))
    # coverage should be ~80% for a well-calibrated 10–90 band

    # -------------------------------------------------------
    # Persist
    # -------------------------------------------------------
    version = f"v{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    artifacts = {
        "stage1_binary":  stage1,
        "stage2_median":  stage2_median,
        "stage2_lower":   stage2_lower,
        "stage2_upper":   stage2_upper,
    }
    for name, artifact in artifacts.items():
        joblib.dump(artifact, f"{model_dir}/regressor_{name}_{version}.joblib")
        joblib.dump(artifact, f"{model_dir}/regressor_{name}.joblib")  # alias

    metrics = {
        "version": version,
        "architecture": "hurdle_two_stage",
        "stage1_model": "LogisticRegression_balanced",
        "stage2_model": "HuberRegressor + QuantileRegressor(0.1, 0.9)",
        "spend_threshold": spend_threshold,
        "train_rows_total": len(train_df),
        "train_rows_nonzero": int(nonzero_mask_train.sum()),
        "val_rows_total": len(val_df),
        "val_rows_nonzero": int(nonzero_mask_val.sum()),
        "mae_on_spend_days": round(float(mae), 4),
        "rmse_on_spend_days": round(float(rmse), 4),
        "confidence_band_coverage": round(float(coverage), 4),
        "note": "MAE and RMSE measured only on non-zero spend days. Coverage = fraction of actuals inside 10th-90th percentile band."
    }
    with open(f"{model_dir}/regressor.metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Update manifest
    manifest = {
        "promoted_version": version,
        "architecture": "hurdle_two_stage",
        "selected_model": "HuberRegressor",
        "training_rows": len(train_df),
        "validation_rows": len(val_df),
        "mae": round(float(mae), 4),
        "promoted_at": datetime.utcnow().isoformat()
    }
    with open(f"{model_dir}/daily_spend_regressor.manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return metrics
```

### 8.3 Inference changes for forecast endpoint

The `GET /forecast_daily_spend` endpoint must be updated to load all four artifacts (stage1, stage2_median, stage2_lower, stage2_upper) and combine predictions:

```python
def predict_day(features: np.ndarray, threshold: float = 0.4) -> dict:
    spend_prob = stage1.predict_proba(features)[0, 1]
    if spend_prob < threshold:
        return {"predicted": 0.0, "lower": 0.0, "upper": 0.0}
    median = float(stage2_median.predict(features)[0])
    lower  = float(stage2_lower.predict(features)[0])
    upper  = float(stage2_upper.predict(features)[0])
    # Clamp: lower <= median <= upper
    lower  = min(lower, median)
    upper  = max(upper, median)
    return {"predicted": max(0.0, median), "lower": max(0.0, lower), "upper": max(0.0, upper)}
```

### Phase 4 Acceptance Criteria

- [ ] Stage 1 binary classifier trained and persisted
- [ ] Stage 2 HuberRegressor trained on non-zero days only
- [ ] Stage 2 QuantileRegressor (0.10, 0.90) trained and persisted
- [ ] MAE reported on non-zero validation days (not all days)
- [ ] Confidence band coverage metric in `regressor.metrics.json` (target: ≥ 0.70)
- [ ] Forecast endpoint updated to load hurdle artifacts
- [ ] Old single linear/ridge model archived but not deleted

---

## 9. Phase 5 — Evaluation and Governance

### 9.1 Classification promotion policy

A new classifier artifact is promotable only if:
- Macro F1 on validation set ≥ current promoted model's macro F1
- No individual class (that has ≥ 5 training examples) has F1 < 0.30
- Training dataset is drawn from real-date transactions only

### 9.2 Regression promotion policy

A new regressor artifact is promotable only if:
- MAE on non-zero validation days ≤ current promoted model's MAE
- Confidence band coverage ≥ 0.65 (65% of actuals inside 10th–90th percentile band)
- Dataset has no rows with `date.year >= 2027`

### 9.3 Baseline values to beat (after Phase 1 decontamination)

These values must be re-measured on the clean dataset before any promotion gate applies. The current artifact metrics (MAE=0.58 on all days including zeros) are not valid baselines.

```json
{
  "classification_baseline": {
    "model": "LogReg_unbalanced",
    "macro_f1": "TBD after clean dataset rebuild",
    "note": "Measure on clean data first run"
  },
  "regression_baseline": {
    "model": "LinearRegression_all_days",
    "mae_on_spend_days": "TBD after clean data rebuild",
    "note": "Current MAE=0.58 is on zero-inflated full dataset — not a valid baseline"
  }
}
```

### 9.4 Manifest schema (updated)

```json
{
  "promoted_version": "v20260416T120000Z-abc12345",
  "classifier": {
    "artifact": "classifier.joblib",
    "versioned_artifact": "classifier_v20260416T120000Z-abc12345.joblib",
    "macro_f1": 0.62,
    "trainable_classes": ["other", "lunch", "recharge"],
    "excluded_classes": ["tea", "extra", "cash_withdrawal"],
    "trained_on_rows": 126,
    "promoted_at": "2026-04-16T12:00:00Z"
  },
  "regressor": {
    "architecture": "hurdle_two_stage",
    "stage1_artifact": "regressor_stage1_binary.joblib",
    "stage2_artifact": "regressor_stage2_median.joblib",
    "stage2_lower_artifact": "regressor_stage2_lower.joblib",
    "stage2_upper_artifact": "regressor_stage2_upper.joblib",
    "mae_on_spend_days": 85.4,
    "confidence_band_coverage": 0.72,
    "train_rows_nonzero": 47,
    "promoted_at": "2026-04-16T12:00:00Z"
  }
}
```

---

## 10. Phase 6 — Inference Integration and Feedback Loop

### 10.1 Classifier integration (FastAPI)

`HybridTransactionCategorizer` in `ml/inference/predict.py` already has lazy-load logic. Changes required:

- Load the new pipeline artifact (which wraps TF-IDF + classifier together as a sklearn Pipeline)
- Remove the separate vectorizer load — it is now embedded in the Pipeline object
- Confidence score: use `predict_proba()` from LogReg or CalibratedClassifierCV output

```python
def predict_category(self, text: str) -> tuple[str | None, float]:
    if self.pipeline is None:
        return None, 0.0
    proba = self.pipeline.predict_proba([text])[0]
    top_idx = proba.argmax()
    confidence = float(proba[top_idx])
    category = self.pipeline.classes_[top_idx]
    if confidence < 0.40:  # below confidence gate → defer to rules
        return None, confidence
    return category, confidence
```

### 10.2 Unmatched transaction logging

Already wired to `ml/data/unmatched_transactions.csv`. Enforce these fields:

| Field | Source |
|---|---|
| `date` | Transaction date |
| `description` | Raw description |
| `amount` | Transaction amount |
| `type` | debit / credit |
| `subtype` | From categorizer |
| `rule_applied` | Which rule tier was tried (regex/keyword/none) |
| `ml_predicted_category` | ML output, if any |
| `ml_confidence` | Confidence score |
| `final_category` | What was actually persisted |
| `logged_at` | UTC timestamp |

### 10.3 Retraining trigger conditions

Trigger a retraining run when any of the following are true:
- 50+ new real transactions have been added since last training run
- Unmatched log exceeds 20 rows in any rolling 30-day window
- A manual review batch has been completed (corrected labels added)

### 10.4 Active learning loop (future)

```
unmatched_transactions.csv
  → manual review UI (mapping page or admin)
  → corrections written back to transaction.category with category_source='manual'
  → next dataset export picks up corrected rows
  → retraining run
  → new artifact promoted if metrics improve
```

---

## 11. File and Folder Structure

```
ml/
├── data/
│   ├── clean_transactions.csv          ← Phase 1 output
│   ├── quarantine_synthetic.csv        ← Phase 1 output
│   ├── sanitization_report.json        ← Phase 1 output
│   ├── class_audit.json                ← Phase 2 output
│   ├── regression_daily_dataset.csv    ← Phase 2 rebuilt (real dates only)
│   ├── training_dataset.csv            ← Classification training export
│   └── unmatched_transactions.csv      ← Inference feedback
├── features.py                         ← Shared feature engineering (extended in Phase 2)
├── models/
│   ├── classifier.joblib               ← Unversioned alias
│   ├── classifier_v<VERSION>.joblib    ← Versioned artifact
│   ├── classifier.metrics.json
│   ├── regressor_stage1_binary.joblib
│   ├── regressor_stage2_median.joblib
│   ├── regressor_stage2_lower.joblib
│   ├── regressor_stage2_upper.joblib
│   ├── regressor.metrics.json
│   └── daily_spend_regressor.manifest.json
├── preprocessing/
│   ├── __init__.py
│   ├── sanitize.py                     ← Phase 1: date decontamination + outlier flagging
│   ├── audit_dataset.py                ← Phase 2: class distribution audit
│   ├── build_dataset.py                ← Classification dataset export (update to use clean data)
│   └── build_regression_dataset.py     ← Phase 2: regression dataset rebuild
├── training/
│   ├── __init__.py
│   ├── train_classifier.py             ← Phase 3: balanced classifier
│   └── train_regressor.py              ← Phase 4: hurdle model
└── inference/
    ├── __init__.py
    └── predict.py                      ← Phase 6: updated for Pipeline artifact + hurdle forecast
```

---

## 12. Dependency Map

```
Phase 1 (sanitize.py)
  └──> Phase 2 (build_regression_dataset.py, audit_dataset.py, feature enrichment)
         └──> Phase 3 (train_classifier.py) — blocked on Phase 1 and 2
         └──> Phase 4 (train_regressor.py)  — blocked on Phase 1 and 2
               └──> Phase 5 (promotion gates) — blocked on Phase 3 and 4
                     └──> Phase 6 (inference update, feedback loop)
```

No phase can be skipped. Phase 3 and Phase 4 can run in parallel after Phase 2 completes.

---

## 13. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Clean dataset too small for ML (< 100 real transactions) | High | High | Fall back to rule-only inference; ML training deferred until more statements uploaded |
| Class audit shows only 2 trainable classes (other + lunch) | High | Medium | Accept it; train binary classifier first; expand as data grows |
| Hurdle model Stage 2 has < 30 non-zero spend days in training | Medium | High | Use Ridge or HuberRegressor with strong regularization; widen confidence band |
| Quantile regressor produces inverted bounds (lower > upper) | Low | Medium | Clamp at inference: `lower = min(lower, median)`, `upper = max(upper, median)` |
| Synthetic 2099 data is not all test data — some may be valid | Low | High | Manual review of quarantine file before permanent deletion |
| Macro F1 never exceeds 0.50 on current dataset size | Medium | Medium | Document as known limitation; rules remain primary; ML is fallback only |
| Forecast endpoint breaks if new regressor artifact schema differs | Medium | High | Version the artifact file names; keep backward-compatible unversioned aliases |

---

## 14. Source References

| Section | Source Documents |
|---|---|
| Dataset statistics (counts, distributions, metrics) | `Overview_dataset.md` |
| Current model architecture and artifacts | `ml_pipeline.md`, `machine_learning_application.md` |
| Regression feature plan and validation strategy | `regression_prediction_plan.md` |
| Transaction subtypes and category enum | `architecture.md`, `WORKFLOWS.md` |
| Forecast API contract | `api.md` (GET /forecast_daily_spend), `frontend_regression_forecast_plan.md` |
| ML integration status in FastAPI | `machine_learning_application.md` (Backend Integration Status) |
| Category source and confidence persistence | `overview_dashboard.md` (Section 3.3), `machine_learning_application.md` |
| Sanitization year threshold rationale | `Overview_dataset.md` (Section 3.1 — dates to 2099 are synthetic/test) |
