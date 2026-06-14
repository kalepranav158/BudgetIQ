import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import CategoryDonut from "../components/charts/CategoryDonut";
import DailyStackedBar from "../components/charts/DailyStackedBar";
import MonthlyTrendLine from "../components/charts/MonthlyTrendLine";
import SubtypeDonut from "../components/charts/SubtypeDonut";
import ForecastTrendChart from "../components/charts/ForecastTrendChart";
import CategoryToggle from "../components/dashboard/CategoryToggle";
import MonthSelector from "../components/dashboard/MonthSelector";
import SummaryCard from "../components/dashboard/SummaryCard";
import SummaryCardGrid from "../components/dashboard/SummaryCardGrid";
import TopSpendingDaysTable from "../components/dashboard/TopSpendingDaysTable";
import ForecastTable from "../components/dashboard/ForecastTable";
import Skeleton from "../components/ui/Skeleton";
import Button from "../components/ui/Button";
import { DEBIT_CATEGORIES } from "../constants/categoryColors";
import { useTransactions } from "../features/transactions/useTransactions";
import { useDailyForecast } from "../hooks/useDailyForecast";
import { useDailySummaries } from "../hooks/useDailySummaries";
import { useDashboardMonth } from "../hooks/useDashboardMonth";
import { useMonthlySummaries } from "../hooks/useMonthlySummaries";
import { sameYearMonth } from "../utils/dateHelpers";
import { formatCurrency } from "../utils/formatCurrency";
import { aggregateByMonth, computeCategoryTotals, computeMonthSummary, computeSubtypeTotals, topSpendingDays } from "../utils/summaryAggregations";
import { useReclassifyTransactions } from "../features/mappings/useReclassifyTransactions";

const LINE_OPTIONS = [
  { value: "total_debit", label: "Total Debit" },
  { value: "total_credit", label: "Total Credit" },
  ...DEBIT_CATEGORIES.map((item) => ({ value: item, label: item }))
];

const FORECAST_OPTIONS = [7, 14, 30].map((days) => ({
  value: String(days),
  label: `${days} Days`
}));

function DashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const monthlyQuery = useMonthlySummaries();
  const dailyQuery = useDailySummaries();
  const transactionsQuery = useTransactions();
  const [forecastDays, setForecastDays] = useState(() => {
    const parsed = Number(searchParams.get("forecastDays") || "7");
    return [7, 14, 30].includes(parsed) ? parsed : 7;
  });
  const [forecastLayers, setForecastLayers] = useState({
    showForecast: searchParams.get("showForecast") !== "0",
    showBand: searchParams.get("showBand") !== "0",
    showActualOverlay: searchParams.get("showActualOverlay") !== "0",
  });
  const forecastQuery = useDailyForecast(forecastDays);
  const { selectedMonth, setSelectedMonth, monthOptions } = useDashboardMonth(monthlyQuery.data || []);
  const [activeLines, setActiveLines] = useState(["total_debit", "total_credit"]);
  const reclassifyMutation = useReclassifyTransactions();

  const isLoading = monthlyQuery.isLoading || dailyQuery.isLoading || transactionsQuery.isLoading;

  const monthRows = (dailyQuery.data || []).filter((row) => selectedMonth && sameYearMonth(row.date, selectedMonth.year, selectedMonth.month));
  const summary = computeMonthSummary(monthRows);
  const topRows = topSpendingDays(monthRows, 5);

  const trendData = useMemo(() => {
    const dailyAgg = aggregateByMonth(dailyQuery.data || []);
    const map = new Map(dailyAgg.map((row) => [`${row.year}-${row.month}`, row]));

    return (monthlyQuery.data || []).map((row) => {
      const key = `${row.year}-${row.month}`;
      const fromDaily = map.get(key) || {};
      return {
        ...fromDaily,
        year: Number(row.year),
        month: Number(row.month),
        total_debit: Number(row.total_debit || fromDaily.total_debit || 0),
        total_credit: Number(row.total_credit || fromDaily.total_credit || 0)
      };
    });
  }, [dailyQuery.data, monthlyQuery.data]);

  const monthTransactions = useMemo(() => {
    return (transactionsQuery.data || []).filter((tx) => selectedMonth && sameYearMonth(tx.date, selectedMonth.year, selectedMonth.month));
  }, [selectedMonth, transactionsQuery.data]);

  const categoryTotals = computeCategoryTotals(monthRows);
  const subtypeTotals = computeSubtypeTotals(monthTransactions);

  const toggleLine = (value) => {
    setActiveLines((current) => {
      if (current.includes(value)) {
        const next = current.filter((item) => item !== value);
        return next.length ? next : ["total_debit"];
      }
      return [...current, value];
    });
  };

  const netTone = summary.net > 0 ? "success" : summary.net < 0 ? "danger" : "default";
  const reclassifyStatusTone = reclassifyMutation.status === "error" ? "danger" : reclassifyMutation.isSuccess ? "success" : "default";
  const lastRunLabel = reclassifyMutation.data?.updated_at
    ? new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(reclassifyMutation.data.updated_at))
    : "No completed run yet";

  const forecastRows = forecastQuery.data?.forecast || [];
  const recentActualRows = forecastQuery.data?.recentActuals || [];
  const nextDayForecast = forecastRows[0]?.predicted_total_debit || 0;
  const weekForecastTotal = forecastRows.reduce((sum, row) => sum + Number(row.predicted_total_debit || 0), 0);

  const toggleForecastDays = (value) => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || ![7, 14, 30].includes(parsed)) {
      return;
    }
    setForecastDays(parsed);

    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("forecastDays", String(parsed));
    setSearchParams(nextParams);
  };

  const toggleLayer = (layerKey) => {
    setForecastLayers((current) => {
      const next = {
        ...current,
        [layerKey]: !current[layerKey],
      };
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set(layerKey, next[layerKey] ? "1" : "0");
      setSearchParams(nextParams);
      return next;
    });
  };

  if (isLoading) {
    return <Skeleton rows={8} />;
  }

  return (
    <section className="page stack">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Single-page analytics view with overview, trends, daily and breakdown insights.</p>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", justifyContent: "flex-end" }}>
          <Button type="button" variant="secondary" loading={reclassifyMutation.isPending} onClick={() => reclassifyMutation.mutate()}>
            Reclassify transactions
          </Button>
          <MonthSelector options={monthOptions} selected={selectedMonth} onChange={setSelectedMonth} />
        </div>
      </div>

      <div className="stack">
        <h2>Reclassification</h2>
        <SummaryCardGrid>
          <SummaryCard
            label="Status"
            value={reclassifyMutation.isPending ? "running" : reclassifyMutation.isSuccess ? "done" : reclassifyMutation.isError ? "failed" : "idle"}
            tone={reclassifyStatusTone}
            subtitle={reclassifyMutation.isPending ? "Reclassifying now" : reclassifyMutation.isSuccess ? "Latest completed run" : "No reclassify run queued"}
          />
          <SummaryCard
            label="Rows Updated"
            value={String(reclassifyMutation.data?.updated ?? 0)}
            subtitle={reclassifyMutation.isSuccess ? "Latest completed run" : "Updated after the last completed run"}
          />
          <SummaryCard
            label="Last Run"
            value={lastRunLabel}
            subtitle={reclassifyMutation.data?.updated ? `${reclassifyMutation.data.updated} rows reclassified` : "Waiting for the first completed run"}
          />
          <SummaryCard
            label="Progress"
            value={reclassifyMutation.isPending ? "running" : reclassifyMutation.isSuccess ? "100%" : "0%"}
            subtitle={reclassifyMutation.isError ? reclassifyMutation.error?.message || "Reclassify failed" : "Runs immediately when clicked"}
          />
        </SummaryCardGrid>
        <div style={{ height: 8, borderRadius: 999, overflow: "hidden", background: "var(--surface-variant, rgba(255,255,255,0.08))" }}>
          <div
            style={{
              width: reclassifyMutation.isSuccess ? "100%" : reclassifyMutation.isPending ? "70%" : "0%",
              height: "100%",
              background: "linear-gradient(90deg, var(--primary-500, #5b9cff), var(--accent-500, #43d9a3))",
              transition: "width 200ms ease"
            }}
          />
        </div>
      </div>

      <SummaryCardGrid>
        <SummaryCard label="Total Spend" value={formatCurrency(summary.debit)} />
        <SummaryCard label="Total Credit" value={formatCurrency(summary.credit)} />
        <SummaryCard label="Net" value={formatCurrency(summary.net)} tone={netTone} />
        <SummaryCard label="Top Category" value={summary.topCategory.name} subtitle={formatCurrency(summary.topCategory.amount)} />
      </SummaryCardGrid>

      <div className="stack">
        <h2>Spend Forecast (Regression)</h2>
        {forecastQuery.isLoading ? (
          <Skeleton rows={4} />
        ) : forecastQuery.isError ? (
          <p className="page-subtitle">Forecast is unavailable right now. Train or load the daily regressor artifact to enable it.</p>
        ) : (
          <>
            <CategoryToggle
              options={FORECAST_OPTIONS}
              activeValues={[String(forecastDays)]}
              onToggle={toggleForecastDays}
            />
            <SummaryCardGrid>
              <SummaryCard label="Next Day Forecast" value={formatCurrency(nextDayForecast)} />
              <SummaryCard label={`${forecastDays} Day Forecast Total`} value={formatCurrency(weekForecastTotal)} />
              <SummaryCard label="Model Version" value={forecastQuery.data?.modelVersion || "unknown"} />
              <SummaryCard label="Selected Model" value={forecastQuery.data?.selectedModel || "unknown"} subtitle={forecastQuery.data?.lastObservedDate || ""} />
            </SummaryCardGrid>
            <ForecastTrendChart
              rows={forecastRows}
              recentActualRows={recentActualRows}
              showForecast={forecastLayers.showForecast}
              showBand={forecastLayers.showBand}
              showActualOverlay={forecastLayers.showActualOverlay}
              onToggleForecast={() => toggleLayer("showForecast")}
              onToggleBand={() => toggleLayer("showBand")}
              onToggleActualOverlay={() => toggleLayer("showActualOverlay")}
            />
            <ForecastTable rows={forecastRows} />
          </>
        )}
      </div>

      <div className="dashboard-two-col">
        <div>
          <h2>Monthly Category Breakdown</h2>
          <CategoryDonut totals={summary.categoryTotals} />
        </div>
        <div>
          <h2>Trends</h2>
          <MonthlyTrendLine data={trendData} activeLines={activeLines} />
          <CategoryToggle options={LINE_OPTIONS} activeValues={activeLines} onToggle={toggleLine} />
        </div>
      </div>

      <div className="dashboard-two-col">
        <div>
          <h2>Daily Spend</h2>
          <DailyStackedBar rows={monthRows} />
        </div>
        <div>
          <h2>Top Spending Days</h2>
          <TopSpendingDaysTable rows={topRows} />
        </div>
      </div>

      <div className="dashboard-two-col">
        <div>
          <h2>Category Drilldown</h2>
          <CategoryDonut totals={categoryTotals} />
        </div>
        <div>
          <h2>Subtype Drilldown</h2>
          <SubtypeDonut totals={subtypeTotals} />
        </div>
      </div>
    </section>
  );
}

export default DashboardPage;
