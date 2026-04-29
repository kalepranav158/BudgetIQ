# Sprint Tracker

This file is the single checklist for execution tracking.

## Status Legend
- `[ ]` Not started
- `[-]` In progress
- `[x]` Completed
- `[!]` Blocked

## Sprint: Backend Dataflow Stabilization
Start Date: 2026-03-29
Owner: Team

### Phase 1: Core Service Stability
- [x] Fix FastAPI startup settings module (`backend.settings`)
- [x] Fix `/get_transactions` async/sync ORM usage
- [x] Fix `/get_transactions` JSON serialization for `date` and `Decimal`
- [x] Add/complete missing endpoint implementation for `/get_transactions`

### Phase 2: Monthly Summary Integration
- [x] Add `MonthlySummary` model
- [x] Add `DailyExpenseSummary.month` foreign key
- [x] Integrate monthly linking in `upsert_daily_summaries`
- [x] Recalculate monthly totals from daily rows
- [x] Add migration with data backfill for existing daily rows
- [x] Apply migration successfully

### Phase 3: Documentation Maintenance
- [x] Update architecture documentation for monthly rollup flow
- [x] Update API docs with current endpoints
- [x] Update README tables/endpoints/documentation index
- [x] Create sprint tracker with mark-based completion
- [ ] Add sprint close summary after QA verification

### Phase 4: QA and Hardening
- [ ] Add automated tests for monthly rollup recalculation
- [ ] Add test for migration backfill integrity
- [ ] Add endpoint tests for `/get_transactions`
- [ ] Resolve static typing warnings in FastAPI schema conversion

## Sprint: Classification Quality Improvements
Start Date: 2026-04-16
Owner: Team

### Phase 1: Precision and Matching Logic
- [x] Add safe short-keyword token-boundary matching to reduce false positives
- [x] Prioritize longer keyword matches before generic keyword matches
- [x] Add tolerant account-name matching when UPI ID is exact
- [x] Add safe integer parsing for regex/account priority fields

### Phase 2: Validation
- [x] Add tests for short-keyword false-positive prevention
- [x] Add tests for fuzzy UPI account-name matching
- [x] Run targeted categorizer test suite and verify pass status

## How to Maintain
1. Update only this file for sprint state changes.
2. Change one step mark at a time as work completes.
3. Add date and initials at sprint closure.

## Sprint: Parser Reliability + Reclassification UX
Start Date: 2026-04-29
Owner: Team

### Phase 1: Parser Reliability Hardening
- [x] Support numeric statement date formats in parser start-line detection
- [x] Support optional post-date column variants for SBI-style rows
- [x] Tolerate missing `Ref` amount-column variants
- [x] Improve encrypted PDF parse error handling with clear API responses

### Phase 2: Dynamic Category Pipeline
- [x] Allow custom category creation in mapping UI
- [x] Accept dynamic category strings in backend schemas and categorizer path
- [x] Preserve `other` as fallback category

### Phase 3: Reclassification Flow
- [x] Add background reparse job model and worker command
- [x] Add enqueue/status API endpoints for reparse jobs
- [x] Add dashboard reclassify action and status cards
- [x] Switch dashboard reclassify to immediate synchronous execution path
- [x] Auto-refresh active dashboard datasets after reclassify run
- [x] Increase reclassify request timeout to prevent 5s client abort

### Phase 4: Remaining Work / Next Phase
- [ ] Integrate production-grade async queue (Celery/RQ + retry policy)
- [ ] Add explicit category management API (authoritative category table)
- [ ] Add model-level evaluation reporting for ML fallback quality (macro-F1/per-class recall)
- [ ] Add end-to-end regression tests for reclassification dashboard flow

### Status Summary (2026-04-29)
- Parser Reliability: `[x]`
- Dynamic Categories: `[x]`
- Reclassification UX: `[x]`
- Queue Orchestration: `[-]`
- ML Operationalization: `[-]`
