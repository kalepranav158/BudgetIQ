# 📌 Sprint: Backend Intelligence & Reliability Upgrade

**Start Date:** 2026-03-31
**Owner:** Pranav / Team
**Sprint Goal:**
Stabilize data correctness, introduce ML-assisted categorization, and prepare the system for scalable processing.

---

# 🎯 Sprint Objectives

1. Eliminate duplicate transaction risks
2. Introduce ML fallback into categorization pipeline
3. Add essential automated test coverage
4. Improve query performance and data retrieval
5. Prepare system for asynchronous processing

---

# 📊 Success Criteria

* No duplicate transactions on repeated uploads
* ML fallback working for uncategorized transactions
* ≥ 80% core API test coverage
* Sorted and optimized transaction queries
* Parser ready for async migration

---

# 🧩 Phase 1: Data Integrity & Core Fixes

### Tasks

* [x] Add transaction deduplication logic

  * ✅ Generate unique hash: `_build_transaction_hash()` → SHA256(`date|amount|normalized_description`)
  * ✅ Enforce uniqueness at DB level

* [x] Prevent duplicate inserts in `/upload-pdf`

  * ✅ Hash-based deduplication logic implemented in `save_transactions()`

* [x] Add default sorting to transactions API

  * ✅ `/get_transactions` orders by `-date, -id`

* [x] Add DB indexes

  * ✅ `date`, `category`, `type`, `subtype` indexes in Transaction model

---

# 🧠 Phase 2: ML Integration (Hybrid Categorization)

### Tasks

* [~] Integrate ML fallback in categorizer

  * ⚠️ ML parameter exists in `categorize_transaction()` signature
  * ⚠️ HybridTransactionCategorizer class exists in `ml/inference/predict.py`
  * ❌ NOT integrated into `/parse-pdf` flow yet (never called with ML predictions)

* [~] Load trained TF-IDF + Logistic Regression model

  * ✅ Model class `TransactionClassifier` exists
  * ❌ Not invoked during categorization pipeline

* [x] Add prediction confidence score

  * ✅ Confidence score returned from `categorize_transaction()` (0.6 for ML, 1.0 for rules)
  * ✅ Source metadata tracked: `"category_source"` field in response

* [ ] Store prediction metadata in DB (optional fields)

  * ❌ Not implemented - `category_source` and `confidence` not stored in Transaction model

---

# 🧪 Phase 3: Testing & QA

### Tasks

* [x] Add unit tests for:

  * ✅ PDF parsing output → `test_parser.py`
  * ✅ Categorization logic (regex + keyword, NO ML) → `test_categorizer.py`

* [x] Add API tests:

  * ✅ `/parse-pdf` → `test_api.py`
  * ✅ `/get_transactions` → `test_api.py`
  * ⚠️ `/upload-pdf` (Django endpoint) - exists but coverage unclear

* [x] Add aggregation validation tests:

  * ✅ Daily summary correctness → `test_aggregator.py`
  * ✅ Monthly rollup correctness → `test_rollup_and_dedup.py`

* [x] Add migration integrity test

  * ✅ Deduplication test → `test_rollup_and_dedup.py`

---

# ⚙️ Phase 4: Performance & Optimization

###x] Optimize ORM queries

  * ✅ `.values()` used to fetch only required fields
  * ✅ `.order_by()` applied for efficient sorting
  * ✅ Aggregation functions optimized in `_sum_transactions()`

* [~] Add pagination to `/get_transactions`

  * ❌ Not implemented - returns ALL transactions (no limit/offset)

* [x] Reduce redundant DB writes during summary updates

  * ✅ `_recalculate_monthly_totals()` uses atomic transaction

* [ ] Reduce redundant DB writes during summary updates

---

# 🚀❌ Not done - parsing still inline with request cycle

* [ ] Introduce background job structure (no execution yet)

  * ❌ No Celery / RQ integration prepared yet

* [ ] Add status tracking model:

  * ❌ No job status tracking model created
  ```json
  {
    "job_id": "...",
    "status": "processing | completed"
  }
  ```

---

# 🧱 Phase 6: Parser Improvements

### Tasks
~] Abstract parser logic for multi-bank support

  * ⚠️ Partial - Parser functions exist but no formal BaseParser interface
  * ✅ Categorization abstraction with `build_*_rules()` pattern

* [x] Improve regex prioritization handling

  * ✅ Regex rules sorted by priority: `rules.sort(key=lambda row: row[3])`

* [x] Add fallback category: `"uncategorized"`

  * ✅ "other" used as fallback category
* [ ] Add fallback category: `"uncategorized"`

---

# 📈 Phase 7: Observability & Debugging

### Tasks

* [ ] Add structured logging:

  * Parsing logs
  * Categorization logs
~] Add structured logging:

  * ✅ Basic logging setup in `main.py` and `views.py`
  * ⚠️ Parsing logs minimal, categorization logs missing

* [ ] Log unmatched transactions for ML training dataset

  * ❌ No logging for unmatched/fallback categorizations

* [ ] Add debug endpoint:

  * ❌ No `/debug/unmatched-transactions` endpoint

| Risk                    | Mitigation                         |
| ----------------------- | ---------------------------------- |
| ML misclassification    | Keep rules as primary layer        |
| Duplicate logic failure | Add DB constraint                  |
| Async complexity        | Only prepare structure this sprint |
| Test overhead           | Focus on critical endpoints only   |

---

# 📦 Deliverables

* Updated categorizer with ML fallback
* Deduplication-enabled ingestion pipeline
* Test suite for core APIs and aggregation
* Optimized transaction retrieval APIs
* Async-ready architecture (non-blocking design prepared)

---
✅ All P0 tasks completed (deduplication + sorting + indexes + tests)
* ✅ No duplicate data on repeated uploads (hash-based)
* ✅ All APIs stable and tested
* ❌ ML fallback NOT YET producing categories (incomplete integration)
* No duplicate data on repeated uploads
* All APIs stable and tested
* ML fallback producing valid categories

---

# 🔄 Post-Sprint Direction

Next sprint will focus on:

* Full async processing (Celery integration)
* Frontend dashboard (visual analytics)
* Real-time transaction ingestion (UPI/SMS)

---

**Sprint Status:** `[-] In Progress`
---

# 📊 Progress Summary

| Phase | Status | Priority Tasks Blocked |
|-------|--------|------------------------|
| Phase 1 | ✅ Complete | None |
| Phase 2 | ⚠️ ~50% (no ML integration) | ML not invoked in pipeline |
| Phase 3 | ✅ Complete | None |
| Phase 4 | ⚠️ ~75% (missing pagination) | Pagination not implemented |
| Phase 5 | ❌ Not started | Async refactoring blocked |
| Phase 6 | ⚠️ ~75% (no formal interface) | BaseParser pattern not formalized |
| Phase 7 | ⚠️ ~30% (minimal logging) | Debug endpoints missing |

---

# 🚨 Critical Issues

1. **ML Integration Incomplete** - `HybridTransactionCategorizer` exists but never called in `/parse-pdf` flow
   - Impact: ML fallback not working despite infrastructure in place
   - Fix: Wire ML predictions into `categorize_transaction()` during `/parse-pdf`

2. **No Pagination** - `/get_transactions` returns ALL records (potential OOM risk)
   - Impact: Large datasets will cause performance/memory issues
   - Fix: Add `limit`/`offset` query parameters

3. **Missing DB Storage for Metadata** - `category_source` and `confidence` not persisted
   - Impact: Cannot analyze categorization accuracy or source distribution
   - Fix: Add optional fields to Transaction model

4. **Async Structure Not Prepared** - Still synchronous, blocks requests during PDF parsing
   - Impact: Long PDFs timeout/degraded UX
   - Impact: Next sprint (full async) will be harder without foundation

---

**Sprint Status:** `[~] 65% Complete - Blocked on ML Integration