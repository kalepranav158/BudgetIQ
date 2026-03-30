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

## How to Maintain
1. Update only this file for sprint state changes.
2. Change one step mark at a time as work completes.
3. Add date and initials at sprint closure.
