# BrainIQ Frontend Feature Map

Last Updated: 2026-04-14
Document Type: Current implementation map

## Purpose

This document reflects the current frontend implementation status and route behavior after the dashboard consolidation and navigation updates.

## Current Frontend Routes

The frontend currently exposes these routes:
- / (redirects to /upload)
- /upload
- /dashboard
- /transactions
- /summaries/daily
- /summaries/monthly
- /mappings
- /health

Compatibility redirects in place:
- /trends -> /dashboard
- /daily -> /dashboard
- /breakdown -> /dashboard

## Navigation Theme

Current theme is Option 1:
- Sticky top navigation bar
- Utility links in the header (daily/monthly summary)
- Hero tab row for main modules (upload, dashboard, transactions, mappings, health)

Primary files:
- frontend/src/components/layout/Sidebar.jsx
- frontend/src/styles/global.css

## Dashboard Status

Current dashboard is a single-page analytics view in /dashboard.

Implemented sections:
- Summary cards: total spend, total credit, net, top category
- Monthly category donut
- Trend chart with line toggles (total debit/credit + categories)
- Daily stacked chart for selected month
- Top spending days table
- Category and subtype donut breakdown cards
- Regression forecast block with horizon selector (7/14/30), forecast summary cards, trend chart, and forecast table

Removed from dashboard:
- Transaction table listing
- Drilldown pagination controls

Primary files:
- frontend/src/pages/DashboardPage.jsx
- frontend/src/components/charts/*
- frontend/src/components/dashboard/*

## Upload-first Flow

Upload remains a standalone first page and is the default app entry point.

Implemented:
- PDF file input + optional password
- Upload to Django /upload-pdf
- Upload result card with saved transaction count and summary preview

Primary files:
- frontend/src/pages/UploadPage.jsx
- frontend/src/features/upload/UploadForm.jsx
- frontend/src/features/upload/UploadResultCard.jsx

## Data Hook Status

Monthly summary response-key handling is fixed in both monthly hooks:
- Supports monthly_summaries
- Also supports monthly/summaries/data fallback

Daily regression forecast hook is implemented:
- Fetches `/forecast_daily_spend?days=<horizon>`
- Normalizes `model_version`, `selected_model`, `last_observed_date`, and forecast rows
- Dashboard keeps forecast controls in URL query params so refreshed/shared links preserve horizon and layer visibility.

Files:
- frontend/src/features/summaries/useMonthlySummaries.js
- frontend/src/hooks/useMonthlySummaries.js
- frontend/src/hooks/useDailyForecast.js

## Remaining Gaps

- Dashboard currently remains feature-rich in one page and may need later decomposition if performance or readability degrades with future additions.
- Mapping management is implemented as keyword and regex tabs, but account mapping coverage still remains a future enhancement.

## Verification Snapshot

Latest verification done in this cycle:
- Frontend production build succeeds after restoring Option 1 navigation.
- Dashboard transaction table remains removed as requested.
