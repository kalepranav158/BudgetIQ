# BrainIQ Dashboard Status

Document Type: Current implementation status
Last Updated: 2026-04-06

## Current Direction

The dashboard has moved from a multi-route planned experience to a consolidated single-page implementation at /dashboard, while keeping upload as the first page at /upload.

## What Is Implemented

### Route behavior
- / redirects to /upload
- /dashboard is the only analytics page
- /trends, /daily, and /breakdown redirect to /dashboard for backward compatibility

### Dashboard sections in /dashboard
- Summary cards:
  - Total Spend
  - Total Credit
  - Net
  - Top Category
- Monthly category donut
- Trends line chart with toggle controls
- Daily stacked spending chart
- Top spending days table
- Category and subtype donut breakdown cards

### Navigation theme
- Option 1 is active:
  - Sticky top header
  - Utility links in header
  - Hero tabs for primary modules

## What Was Intentionally Removed

- Dashboard transaction table rendering
- Dashboard pagination/filter controls that were tied to transaction table rows

## Data Contracts Used

- Daily summaries: GET /get_all_daily_summaries
- Monthly summaries: GET /get_monthly_summaries
- Transactions (used for subtype donut aggregation only): GET /get_transactions

Monthly hooks now handle monthly_summaries as primary key with fallback keys.

## Current Risks / Follow-up

- Account mapping UI is not yet available in the mappings page.
- The single dashboard page is feature-dense; if scope grows further, sections should be progressively collapsible or split by tabs while preserving single route.

## Verification

- Frontend build passes after latest navigation restore and dashboard cleanup.

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Product Context](#2-product-context)
3. [Backend Data Available for Visualization](#3-backend-data-available-for-visualization)
4. [Dashboard Scope](#4-dashboard-scope)
5. [Out-of-Scope](#5-out-of-scope)
6. [User Journeys](#6-user-journeys)
7. [Information Architecture and Route Map](#7-information-architecture-and-route-map)
8. [Page-Level Specifications](#8-page-level-specifications)
9. [Chart and Visualization Inventory](#9-chart-and-visualization-inventory)
10. [API Integration Matrix](#10-api-integration-matrix)
11. [Frontend State Model](#11-frontend-state-model)
12. [Component Architecture](#12-component-architecture)
13. [Non-Functional Requirements](#13-non-functional-requirements)
14. [Testing Strategy](#14-testing-strategy)
15. [Delivery Plan](#15-delivery-plan)
16. [Open Questions](#16-open-questions)
17. [Source References](#17-source-references)

---

## 1. Purpose

This document specifies the data visualization layer for BudgetIQ. It defines a spending analytics dashboard built entirely on top of the existing backend APIs — no new endpoints are introduced for MVP. The dashboard consumes daily and monthly summary data, per-transaction data, and category/subtype enumerations already returned by the backend, and renders them as interactive charts and summary cards.

---

## 2. Product Context

Phase 1 exposes raw tables and forms. The user can upload a statement and read back rows. What it does not provide is any sense of spending pattern, trend, or category breakdown at a glance. The dashboard fixes this.

**Core problem**: a user with six months of uploaded statements has no way to answer questions like:
- Where did most of my money go this month?
- Is my lunch spend increasing month-over-month?
- Which day had the highest total debit this week?
- How much do ATM withdrawals account for vs. UPI transfers?

**Dashboard goal**: make all of the above answerable in under three clicks, using only data the backend already returns.

---

## 3. Backend Data Available for Visualization

All visualization is derived from these three API responses. No new endpoints are needed for the MVP dashboard.

### 3.1 Daily Expense Summary — `GET /get_all_daily_summaries` (FastAPI :8001)

Each row has:

| Field | Type | Notes |
|---|---|---|
| `date` | string (ISO) | e.g. `"2024-07-01"` |
| `cash_withdrawal` | decimal string | |
| `extra` | decimal string | |
| `lunch` | decimal string | |
| `other` | decimal string | |
| `recharge` | decimal string | |
| `tea` | decimal string | |
| `credit` | decimal string | Inflows |
| `total_debit` | decimal string | Sum of all debit categories |
| `total_credit` | decimal string | |

**Assumption**: response shape is `{ "summaries": [...] }`. **Validation needed** — the actual response key is not confirmed in `api.md` for the FastAPI `GET /get_all_daily_summaries` endpoint.

### 3.2 Monthly Summary — `GET /get_monthly_summaries` (FastAPI :8001)

Each row has:

| Field | Type | Notes |
|---|---|---|
| `year` | integer | |
| `month` | integer | 1–12 |
| `total_debit` | decimal | |
| `total_credit` | decimal | |

**Assumption**: response shape is `{ "summaries": [...] }`. **Validation needed** — exact response shape unconfirmed in `api.md`.

### 3.3 Transactions — `GET /get_transactions` (FastAPI :8001)

Each row has: `id`, `date`, `description`, `amount`, `type`, `subtype`, `category`.

Used for: subtype-level breakdown charts, per-category transaction count, and outlier surfacing.

### 3.4 Category Enum (fixed, from WORKFLOWS.md)

```
cash_withdrawal | extra | lunch | other | recharge | tea | credit
```

`credit` is an inflow. All others are debit categories. The dashboard treats `credit` separately in any spend-side chart.

### 3.5 Subtype Enum (fixed, from architecture.md)

```
expense | transfer_out | transfer_in | atm_withdrawal | salary | refund
```

Used for subtype breakdown donut on the dashboard.

---

## 4. Dashboard Scope

### In-Scope for MVP

| Feature | Data source |
|---|---|
| Overview summary cards (month-to-date totals) | Monthly summary + daily summary |
| Category spend breakdown — current month (donut or bar) | Daily summary, aggregated |
| Monthly trend — total debit/credit over time (line chart) | Monthly summary |
| Daily spend heatmap or bar chart for selected month | Daily summary filtered by month |
| Per-category monthly trend (multi-line or grouped bar) | Daily summary grouped by month |
| Subtype breakdown for selected period (donut) | Transactions, grouped by subtype |
| Top spending days table | Daily summary sorted by total_debit |
| Month selector to scope all charts | Client-side state |

### Technology Choice

**Recharts** — already listed as an available library in the artifact stack. No additional library install needed.

---

## 5. Out-of-Scope

| Item | Reason |
|---|---|
| Budget target / goal tracking | No budget goal entity exists on backend |
| Per-merchant breakdown | Transaction descriptions are raw strings; merchant normalization not exposed as structured data |
| Balance-over-time chart | `balance` field only present in parse-time response, not in `GET /get_transactions` |
| ML-predicted category confidence visualization | ML inference not connected to any API response field |
| Date range picker beyond month granularity | Monthly summary is the finest rollup; daily is available but a full arbitrary date range selector is Phase 3 |
| Real-time / streaming updates | No WebSocket or push endpoint |
| Export chart as image or PDF | Phase 3 |
| Comparative multi-account views | Single account only |

---

## 6. User Journeys

### Journey 1: Monthly Spending Overview

```
User navigates to Dashboard
→ Month selector defaults to the most recent month with data
→ Summary cards show: total debit, total credit, net, top category
→ Category donut shows spend split for selected month
→ User changes month selector
→ All charts update to reflect selected month
```

**Acceptance criteria:**
- Month selector is a dropdown populated from `GET /get_monthly_summaries` (distinct year+month pairs).
- Summary cards recompute from daily summaries filtered to selected month.
- Donut chart renders all 6 debit categories; zero-value categories are shown as greyed-out slices or excluded — configurable.
- Net = total_credit − total_debit, shown with sign (+/−) and color (green/red).

### Journey 2: Spending Trend Over Time

```
User navigates to Trends page
→ Line chart shows total_debit and total_credit across all available months
→ User clicks a category (e.g., "lunch") in the legend
→ A per-category line appears or a filtered view loads
→ User can identify months with unusual spend spikes
```

**Acceptance criteria:**
- X-axis: month labels (`Jul 2024`, `Aug 2024`, …), sorted chronologically.
- Y-axis: rupee amounts (₹), formatted with comma separators.
- Two default lines: `total_debit` (red), `total_credit` (green).
- Tooltip on hover shows exact values for all active lines at that month.
- Line chart handles months with zero data without breaking the axis.

### Journey 3: Daily Spend Drill-Down

```
User navigates to Daily view for selected month
→ Bar chart shows total_debit per day for the selected month
→ User hovers a bar to see category-level breakdown in a tooltip
→ Top spending days table below the chart lists date, total_debit, dominant category
```

**Acceptance criteria:**
- Bar chart X-axis: day number (1–31), only days with data rendered.
- Tooltip shows all non-zero category amounts for that day.
- Top spending days table: up to 5 rows, sorted by total_debit desc.
- Table columns: Date, Total Debit, Lunch, Tea, Recharge, Cash Withdrawal, Extra, Other.

### Journey 4: Category and Subtype Breakdown

```
User navigates to Breakdown page
→ Category donut shows % share of each debit category for selected month
→ Subtype donut (from transactions) shows % share of expense, transfer_out, atm_withdrawal, etc.
→ User clicks a category slice
→ Transaction table below filters to that category
```

**Acceptance criteria:**
- Category donut uses the 6 debit category fields from daily summaries.
- Subtype donut derived from `GET /get_transactions` — group by `subtype`, sum `amount`.
- Clicking a donut slice sets a category/subtype filter on the transaction table below.
- Transaction table on this page is read-only, consistent with Phase 1 spec.
- If no transactions exist for a subtype, that slice is omitted from the donut.

---

## 7. Information Architecture and Route Map

The dashboard adds new routes alongside (not replacing) the Phase 1 routes.

```
/                         → redirect to /dashboard
/dashboard                → Monthly overview: summary cards + category donut + monthly trend line
/trends                   → Full monthly trend chart (multi-line, all categories)
/daily                    → Daily bar chart + top spending days for selected month
/breakdown                → Category donut + subtype donut + filtered transaction table
```

Phase 1 routes (`/upload`, `/transactions`, `/summaries/daily`, `/summaries/monthly`, `/mappings`, `/health`) remain unchanged.

### Navigation update

Add a "Dashboard" section grouping in the existing sidebar (from Phase 1 AppShell):

```
── Dashboard
   ├── Overview          /dashboard
   ├── Trends            /trends
   ├── Daily             /daily
   └── Breakdown         /breakdown
── Management (existing Phase 1 routes)
```

---

## 8. Page-Level Specifications

### 8.1 `/dashboard` — Monthly Overview

**Layout**: 4-column summary cards row → 2-column grid (category donut left, monthly trend right)

#### Summary Cards (4 cards)

| Card | Value | Source |
|---|---|---|
| Total Spend | Sum of all debit category fields for selected month from daily summaries | Daily summary, month-filtered |
| Total Credit | Sum of `credit` field for selected month | Daily summary, month-filtered |
| Net | credit − debit, with sign | Derived |
| Top Category | Category with highest total for selected month | Derived from daily summary |

- Cards show a loading skeleton while data fetches.
- Net card background: green if positive, red if negative, neutral if zero.
- Top Category card shows category name and amount, no icon required.

#### Category Donut

- Library: `Recharts PieChart`
- Data: aggregate each of the 6 debit category columns from daily summary rows for selected month
- Slices: `cash_withdrawal`, `extra`, `lunch`, `other`, `recharge`, `tea`
- Color map (fixed):

| Category | Color |
|---|---|
| lunch | `#F97316` (orange) |
| tea | `#84CC16` (lime) |
| recharge | `#3B82F6` (blue) |
| cash_withdrawal | `#EF4444` (red) |
| extra | `#A855F7` (purple) |
| other | `#9CA3AF` (grey) |

- Legend below chart: category name + amount + percentage.
- Zero-value categories: render as greyed-out legend entry, excluded from pie slice.
- `credit` is never shown in the spend donut. It appears only in summary cards.

#### Monthly Trend Line (mini, right column)

- Shows last 6 months of `total_debit` and `total_credit` from `GET /get_monthly_summaries`.
- Two lines only: debit (red), credit (green).
- No interactive filtering on this version — it is a summary sparkline.
- Full interactive version is on `/trends`.
- X-axis: abbreviated month labels (`Jul`, `Aug`).
- Clicking the chart navigates to `/trends`.

#### Month Selector

- Dropdown component, options derived from `GET /get_monthly_summaries`.
- Option format: `July 2024`.
- Default: most recent month (last item after sorting by year desc, month desc).
- Changing month re-derives all summary card values and category donut from already-fetched daily summary data (client-side filter — no re-fetch needed if data is cached).

---

### 8.2 `/trends` — Monthly Trend Chart

**Layout**: full-width chart + category toggle controls below

#### Multi-Line Trend Chart

- Library: `Recharts LineChart`
- X-axis: all available months from monthly summary, sorted chronologically. Format: `MMM YYYY`.
- Y-axis: amount in ₹, formatted `₹1,23,456`.
- Default active lines: `total_debit`, `total_credit`.
- Additional lines (toggleable): one line per debit category — requires aggregating daily summaries by month client-side, since `GET /get_monthly_summaries` only returns total_debit/total_credit.
- Category lines are derived by grouping `GET /get_all_daily_summaries` rows by `(year, month)` and summing each category column.

**Assumption**: Date field in daily summary is parseable as ISO string. Month extraction via `new Date(date).getFullYear()` and `.getMonth()`. **Validation needed**.

#### Category Toggle Controls

- A row of toggle buttons, one per category + total_debit + total_credit.
- Active toggles determine which lines are visible on the chart.
- Default: `total_debit` and `total_credit` only. All category lines off.
- Toggling a category line adds it to the chart with the fixed color from the color map above.
- Max simultaneous lines: 8 (all categories + 2 totals). No restriction needed — all are toggleable.

#### Tooltip

- On hover over a month point: show all active line values.
- Format: `Lunch: ₹4,230` per line.

---

### 8.3 `/daily` — Daily Spend Bar Chart

**Layout**: month selector → bar chart → top spending days table

#### Daily Bar Chart

- Library: `Recharts BarChart` (stacked)
- X-axis: day of month (1–31), only days with data shown.
- Y-axis: ₹ amount.
- Stacked bars: one stack segment per debit category, using the fixed color map.
- Segments stacked in order: lunch, tea, recharge, cash_withdrawal, extra, other.
- `credit` is not stacked into debit bars. It can be overlaid as a line on the same chart.
- Data: daily summary rows filtered to selected month.

#### Tooltip on Bar Hover

Shows all non-zero category amounts for that day:
```
2024-07-05
  Lunch:    ₹249
  Tea:      ₹40
  Total:    ₹289
```

#### Top Spending Days Table

- Columns: Date, Total Debit, Lunch, Tea, Recharge, Cash Withdrawal, Extra, Other
- Rows: top 5 days sorted by `total_debit` desc, for the selected month.
- Amounts formatted as `₹X,XXX`.
- No pagination — fixed at 5 rows.

---

### 8.4 `/breakdown` — Category and Subtype Breakdown

**Layout**: two donuts side by side → filtered transaction table below

#### Category Donut (left)

Same as the one on `/dashboard` but with click interaction:
- Clicking a slice sets `selectedCategory` state.
- The transaction table below filters to that category.
- Selected slice is visually highlighted (opacity 1.0 vs 0.6 for others).

#### Subtype Donut (right)

- Data source: `GET /get_transactions`, grouped by `subtype`, summing `amount`.
- Subtypes: `expense`, `transfer_out`, `transfer_in`, `atm_withdrawal`, `salary`, `refund`.
- Color map (fixed):

| Subtype | Color |
|---|---|
| expense | `#F97316` |
| transfer_out | `#EF4444` |
| transfer_in | `#22C55E` |
| atm_withdrawal | `#EAB308` |
| salary | `#3B82F6` |
| refund | `#84CC16` |

- Clicking a slice sets `selectedSubtype` state.
- Filters the transaction table by subtype.
- If both category and subtype are selected, the table applies both filters (AND logic).

#### Filtered Transaction Table

- Columns: Date, Description, Amount (₹), Category, Subtype.
- Filters applied: `selectedCategory` and/or `selectedSubtype` from donut clicks.
- Client-side pagination: 25 rows per page.
- Reset button: clears both filters and returns donuts to unselected state.
- Empty state: "No transactions match the selected filters."
- Table is read-only. No edit or delete action.

---

## 9. Chart and Visualization Inventory

| Chart ID | Type | Page | Data Source | Library component |
|---|---|---|---|---|
| DASH-01 | Donut / Pie | `/dashboard` | Daily summary, month-filtered | `Recharts PieChart` |
| DASH-02 | Line (mini) | `/dashboard` | Monthly summary | `Recharts LineChart` |
| TREND-01 | Multi-line | `/trends` | Monthly summary + daily summary (aggregated) | `Recharts LineChart` |
| DAILY-01 | Stacked bar | `/daily` | Daily summary, month-filtered | `Recharts BarChart` |
| BRK-01 | Donut | `/breakdown` | Daily summary, month-filtered | `Recharts PieChart` |
| BRK-02 | Donut | `/breakdown` | Transactions grouped by subtype | `Recharts PieChart` |

All charts must:
- Show a Skeleton placeholder while data is loading.
- Show an "No data available for this period" empty state when the filtered dataset is empty.
- Be responsive — minimum usable width 320px, ideal 600px+.
- Not use animations that loop indefinitely (accessibility).

---

## 10. API Integration Matrix

| Endpoint | Service | Method | Request | Response shape (assumed) | Dashboard consumers |
|---|---|---|---|---|---|
| `/get_all_daily_summaries` | FastAPI :8001 | GET | None | `{ summaries: DailySummary[] }` | DASH-01, DAILY-01, BRK-01, TREND-01 (aggregated), summary cards |
| `/get_monthly_summaries` | FastAPI :8001 | GET | None | `{ summaries: MonthlySummary[] }` | DASH-02, TREND-01 (total lines), month selector options |
| `/get_transactions` | FastAPI :8001 | GET | None | `{ transactions: Transaction[] }` | BRK-02, breakdown transaction table |

### Error Handling per Endpoint

| Scenario | Behavior |
|---|---|
| Network timeout or service down | Show error banner: "Could not load summary data. Is the FastAPI service running?" with retry button. |
| 200 response with empty array | Render empty state per chart — no error shown. |
| Malformed / missing fields in a row | Skip that row silently, log to console in dev mode. Do not crash the chart. |
| Decimal string amounts | Parse with `parseFloat()` before summing. Treat null/undefined as 0. |

---

## 11. Frontend State Model

### Server State (React Query)

| Query key | Endpoint | Stale time | Notes |
|---|---|---|---|
| `['dailySummaries']` | `/get_all_daily_summaries` | 5 minutes | Shared across all dashboard pages; fetched once on first dashboard route entry |
| `['monthlySummaries']` | `/get_monthly_summaries` | 5 minutes | Shared; fetched once |
| `['transactions']` | `/get_transactions` | 5 minutes | Fetched on first entry to `/breakdown` |

All three queries are fetched lazily (on route entry), not at app startup.

All three queries are shared via the React Query cache — navigating between dashboard pages does not re-fetch if data is fresh.

### Client State

| State | Location | Type | Default |
|---|---|---|---|
| `selectedMonth` | Dashboard context or URL query param | `{ year: number, month: number }` | Most recent month in monthly summary |
| `selectedCategory` | `/breakdown` local state | `string \| null` | `null` |
| `selectedSubtype` | `/breakdown` local state | `string \| null` | `null` |
| `activeTrendLines` | `/trends` local state | `string[]` | `['total_debit', 'total_credit']` |
| `breakdownPage` | `/breakdown` local state | `number` | `1` |

**`selectedMonth` persistence**: store in URL query param (`?year=2024&month=7`) so the browser back button and direct links work correctly.

### Derived / Computed State

These are not stored — computed on every render from server state:

- `monthlyDailySummaries`: `dailySummaries` filtered to `selectedMonth`
- `categoryTotals`: sum of each category column across `monthlyDailySummaries`
- `monthlyAggregatedByCategory`: `dailySummaries` grouped by `(year, month)`, each category summed — used for per-category trend lines on `/trends`
- `subtypeTotals`: `transactions` grouped by `subtype`, amounts summed — used for BRK-02 donut
- `filteredTransactions`: `transactions` filtered by `selectedCategory` and `selectedSubtype`

Do not memoize unless profiling reveals a render performance problem. React Query caching handles the expensive part (network fetch).

---

## 12. Component Architecture

### New Shared Components (Dashboard-specific)

```
src/
├── components/
│   ├── charts/
│   │   ├── CategoryDonut.jsx        — Recharts PieChart, fixed color map, click handler prop
│   │   ├── SubtypeDonut.jsx         — Same base as CategoryDonut, different color map
│   │   ├── MonthlyTrendLine.jsx     — Recharts LineChart, configurable active lines
│   │   ├── DailyStackedBar.jsx      — Recharts BarChart stacked, category segments
│   │   └── ChartEmptyState.jsx      — "No data for this period" placeholder
│   ├── dashboard/
│   │   ├── SummaryCard.jsx          — Single stat card: label, value, optional color modifier
│   │   ├── SummaryCardGrid.jsx      — 4-column layout of SummaryCard instances
│   │   ├── MonthSelector.jsx        — Dropdown populated from monthly summary data
│   │   ├── CategoryToggle.jsx       — Row of toggle buttons for trend line control
│   │   └── TopSpendingDaysTable.jsx — Top 5 days table for /daily
│   └── ... (Phase 1 shared components unchanged)
├── pages/
│   ├── DashboardPage.jsx
│   ├── TrendsPage.jsx
│   ├── DailyPage.jsx
│   └── BreakdownPage.jsx
├── hooks/
│   ├── useDailySummaries.js         — React Query wrapper for /get_all_daily_summaries
│   ├── useMonthlySummaries.js       — React Query wrapper for /get_monthly_summaries
│   ├── useTransactions.js           — Already exists from Phase 1; reused here
│   └── useDashboardMonth.js         — Reads/writes selectedMonth from URL query param
├── utils/
│   ├── summaryAggregations.js       — computeCategoryTotals, aggregateByMonth, computeSubtypeTotals
│   ├── formatCurrency.js            — ₹ formatting with Indian comma grouping
│   └── dateHelpers.js               — parseISODate, getMonthLabel, sortByYearMonth
└── constants/
    ├── categoryColors.js            — Fixed color map for 6 debit categories
    └── subtypeColors.js             — Fixed color map for 6 subtypes
```

### Aggregation Logic (summaryAggregations.js)

All aggregation happens client-side from raw API responses. No new backend endpoints.

```js
// Compute per-category totals for a set of daily summary rows
computeCategoryTotals(rows) → { lunch: number, tea: number, ... }

// Group daily rows by (year, month), sum each category column
aggregateByMonth(rows) → [{ year, month, lunch, tea, recharge, cash_withdrawal, extra, other, total_debit, total_credit }]

// Group transactions by subtype, sum amounts
computeSubtypeTotals(transactions) → { expense: number, transfer_out: number, ... }
```

These functions must handle:
- `null` or `undefined` field values → treat as 0
- decimal string amounts → `parseFloat()`
- empty input arrays → return zero-valued objects, not errors

### Reuse from Phase 1

- `apiClient.js` — unchanged, all chart data fetched through same client
- `Table`, `Badge`, `Skeleton`, `ErrorState`, `Toast` — reused directly
- `useTransactions` hook — already implemented in Phase 1, reused in breakdown page
- `AppShell` with sidebar — add dashboard nav section, do not rebuild

---

## 13. Non-Functional Requirements

### Performance

- All three API responses are fetched once and cached in React Query for 5 minutes. Navigating between `/dashboard`, `/trends`, `/daily`, and `/breakdown` must not trigger redundant network requests.
- `aggregateByMonth` and `computeCategoryTotals` run on cached data in-memory. If the transaction count exceeds 2,000 rows, memoize these with `useMemo`.
- Charts must render within 300ms of data being available (React Query cache hit scenario).
- Recharts renders are synchronous — if chart data exceeds ~500 points, downsample daily data to weekly aggregates. This threshold is unlikely given typical personal bank statement volume (30–100 transactions/month), but must be handled.

### Accessibility

- All chart containers must have an `aria-label` describing the chart: e.g., `aria-label="Category spending breakdown for July 2024"`.
- Donut charts convey information via color — a text legend with category name + value must accompany every donut.
- Line chart tooltips must be keyboard-accessible: tab to chart, arrow keys to navigate data points.
- Color choices must pass WCAG AA contrast against white background. Verify the fixed color map.
- `MonthSelector` dropdown must be a native `<select>` or a ARIA-compliant custom select with role="listbox".

### Security

- No new attack surface introduced — all endpoints are read-only GET requests.
- API base URL via environment variable (`VITE_FASTAPI_URL`) — same as Phase 1.
- No user-provided data is sent to the backend from any dashboard page.

### Indian Currency Formatting

All amounts must display in Indian numbering system: `₹1,23,456.00` (not `₹123,456.00`).

```js
// formatCurrency.js
const formatCurrency = (amount) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 0 }).format(amount);
```

---

## 14. Testing Strategy

### Unit Tests

Target: aggregation utilities and pure chart data transforms.

- `computeCategoryTotals` — test with array of daily rows, zero values, null fields.
- `aggregateByMonth` — test correct grouping across month boundaries.
- `computeSubtypeTotals` — test with mixed subtype transactions.
- `formatCurrency` — test Indian comma formatting for values above 1 lakh.
- `MonthSelector` — test options derived from monthly summary data, default selection logic.

Tools: Vitest.

### Integration Tests

Target: full page renders with mocked API data.

- `/dashboard` with mocked daily + monthly summaries: verify 4 summary cards render, donut renders with correct slice count, month selector defaults to most recent month.
- `/dashboard` with empty daily summaries: verify empty state renders on donut, zero values in cards.
- `/trends` category toggle: verify toggling a category adds a line to the chart.
- `/breakdown` donut click: verify clicking "lunch" slice filters transaction table to `category === "lunch"`.
- `/daily` month change: verify bar chart updates to show days for the new month.

Tools: Vitest + MSW.

### E2E Tests

- Upload a PDF via Phase 1 upload page, then navigate to `/dashboard` — verify non-zero summary cards.
- Navigate through all 4 dashboard routes — verify no console errors.
- Click a donut slice on `/breakdown` — verify transaction table filters.

Tools: Playwright.

---

## 15. Delivery Plan

### Milestone 1: Foundation (Days 1–2)

- [ ] Add dashboard routes to router (`/dashboard`, `/trends`, `/daily`, `/breakdown`)
- [ ] Update sidebar in AppShell with Dashboard navigation section
- [ ] Implement `useDailySummaries`, `useMonthlySummaries` React Query hooks
- [ ] Implement `summaryAggregations.js` utility functions with full unit test coverage
- [ ] Implement `formatCurrency.js` and `dateHelpers.js`
- [ ] Define `categoryColors.js` and `subtypeColors.js` constants

**Done criteria**: hooks fetch data correctly from running backend; aggregation utilities pass unit tests.

### Milestone 2: Overview Dashboard (Days 3–4)

- [ ] `MonthSelector` component — populated from monthly summaries, URL query param sync
- [ ] `SummaryCard` + `SummaryCardGrid` — 4 cards with skeleton and live values
- [ ] `CategoryDonut` (DASH-01) — renders slices, legend, empty state
- [ ] `MonthlyTrendLine` mini version (DASH-02) — last 6 months, click navigates to /trends
- [ ] `DashboardPage` assembled from above components

**Done criteria**: `/dashboard` renders all 4 cards + donut + mini trend line. Month selector updates all components. Empty and loading states work.

### Milestone 3: Trends and Daily Pages (Days 5–6)

- [ ] `CategoryToggle` — toggle buttons for trend line visibility
- [ ] `MonthlyTrendLine` full version (TREND-01) — multi-line, all toggleable categories
- [ ] `TrendsPage` assembled
- [ ] `DailyStackedBar` (DAILY-01) — stacked by category, tooltip with breakdown
- [ ] `TopSpendingDaysTable` — top 5 days for selected month
- [ ] `DailyPage` assembled

**Done criteria**: `/trends` shows total debit/credit lines; toggling a category adds its line. `/daily` shows stacked bar chart and top 5 table for selected month.

### Milestone 4: Breakdown Page (Days 7–8)

- [ ] `SubtypeDonut` (BRK-02) — from transactions grouped by subtype
- [ ] `CategoryDonut` with click interaction (BRK-01) — sets selectedCategory
- [ ] `SubtypeDonut` click — sets selectedSubtype
- [ ] Filtered transaction table (client-side filter + pagination)
- [ ] Reset filter button
- [ ] `BreakdownPage` assembled

**Done criteria**: Both donuts render. Clicking a slice filters the transaction table. Reset clears selection. Both filters work together (AND logic).

### Milestone 5: QA and Polish (Day 9–10)

- [ ] Verify Indian currency formatting on all charts and cards
- [ ] Accessibility audit: aria-labels on charts, keyboard navigation, color-blind legend check
- [ ] Verify empty states on all 4 pages (use empty mock data in tests)
- [ ] Verify loading skeletons on all 4 pages
- [ ] Verify no redundant API calls on route navigation (React Query DevTools check)
- [ ] Integration test suite passing
- [ ] Manual E2E run against local backend with real uploaded PDF

**Done criteria**: All acceptance criteria from Section 6 verified. Test suite passes. No redundant fetches detected in React Query DevTools.

### Backend Dependencies

| Dashboard feature | Backend requirement | Status |
|---|---|---|
| All chart data | `GET /get_all_daily_summaries` stable | ✅ Done |
| Monthly trend | `GET /get_monthly_summaries` stable | ✅ Done |
| Subtype donut | `GET /get_transactions` stable | ✅ Done |
| Month selector options | `GET /get_monthly_summaries` returns year + month fields | ✅ Assumed |
| Per-category monthly trend | Aggregated client-side from daily summaries | ✅ No backend change needed |

No new backend endpoints are required for the MVP dashboard.

---

## 16. Open Questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| 1 | What is the exact response envelope key for `GET /get_all_daily_summaries`? Assumed `{ summaries: [...] }` — unconfirmed in `api.md`. | Backend | Yes — blocks `useDailySummaries` hook |
| 2 | What is the exact response envelope key for `GET /get_monthly_summaries`? Same concern. | Backend | Yes — blocks `useMonthlySummaries` hook |
| 3 | Are decimal amounts in daily summaries always strings (e.g. `"249.00"`) or sometimes numbers? | Backend | No — affects `parseFloat()` guard logic |
| 4 | Does `GET /get_all_daily_summaries` return rows sorted by date, or in insertion order? | Backend | No — `dateHelpers.js` will sort client-side regardless |
| 5 | Is `credit` in the daily summary always an inflow (positive)? Or can it be negative (reversal)? | Backend / Product | No — affects sign rendering in summary cards |
| 6 | For the monthly trend page, should category lines aggregate from daily summaries only, or should `GET /get_monthly_summaries` be extended to include per-category monthly totals? Current plan: client-side aggregation from daily data. | Product / Backend | No — client-side aggregation is the MVP approach; backend extension is a future optimization |

---

## 17. Source References

| Section | Source Documents |
|---|---|
| Available data fields (daily summary, monthly summary, transactions) | `api.md` (FastAPI endpoints), `api_docs.md` |
| Category enum values | `WORKFLOWS.md` (Managing Seeded Mappings section) |
| Subtype enum values | `architecture.md` (Pipeline step 6), `progress_log.md` (2026-03-30) |
| Monthly summary dataflow and recalculation logic | `architecture.md` (Dataflow: Daily to Monthly) |
| Service ports (Django :8000, FastAPI :8001) | `api_docs.md`, `setup.md` |
| ML out-of-scope justification | `ml_pipeline.md` (scaffolded, not connected to API) |
| Backend stability status of read endpoints | `sprint_tracker.md` (Phase 1 and Phase 2 complete) |
| React Query and Recharts availability | `overview_frontend.md` (Phase 1 spec, technology constraints) |
