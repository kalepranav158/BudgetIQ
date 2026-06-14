import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatCurrency } from "../../utils/formatCurrency";
import ChartEmptyState from "./ChartEmptyState";

function ForecastTrendChart({
  rows,
  recentActualRows = [],
  showForecast = true,
  showBand = true,
  showActualOverlay = false,
  onToggleForecast,
  onToggleBand,
  onToggleActualOverlay,
}) {
  if (!rows?.length && !recentActualRows?.length) {
    return <ChartEmptyState message="No forecast data available." />;
  }

  const merged = new Map();

  for (const row of recentActualRows || []) {
    if (!row?.date) {
      continue;
    }
    merged.set(row.date, {
      date: row.date,
      actual_total_debit: Number(row.actual_total_debit || 0),
    });
  }

  for (const row of rows || []) {
    if (!row?.date) {
      continue;
    }
    const existing = merged.get(row.date) || { date: row.date };
    merged.set(row.date, {
      ...existing,
      predicted_total_debit: Number(row.predicted_total_debit || 0),
      lower_bound: Number(row.lower_bound || 0),
      upper_bound: Number(row.upper_bound || 0),
    });
  }

  const chartData = Array.from(merged.values()).sort((left, right) => left.date.localeCompare(right.date));

  return (
    <div className="chart-card" aria-label="Daily spend forecast trend">
      <div className="forecast-legend" aria-label="Forecast chart legend">
        <button
          type="button"
          className={`forecast-legend__item ${showForecast ? "forecast-legend__item--active" : "forecast-legend__item--inactive"}`}
          aria-pressed={showForecast}
          onClick={onToggleForecast}
        >
          <span className="forecast-legend__swatch forecast-legend__swatch--forecast" />
          Forecast
        </button>
        <button
          type="button"
          className={`forecast-legend__item ${showBand ? "forecast-legend__item--active" : "forecast-legend__item--inactive"}`}
          aria-pressed={showBand}
          onClick={onToggleBand}
        >
          <span className="forecast-legend__swatch forecast-legend__swatch--band" />
          Confidence Band
        </button>
        <button
          type="button"
          className={`forecast-legend__item ${showActualOverlay ? "forecast-legend__item--active" : "forecast-legend__item--inactive"}`}
          aria-pressed={showActualOverlay}
          onClick={onToggleActualOverlay}
          disabled={!recentActualRows?.length}
        >
          <span className="forecast-legend__swatch forecast-legend__swatch--actual" />
          Actual Overlay
        </button>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis tickFormatter={(value) => formatCurrency(value)} width={100} />
          <Tooltip formatter={(value) => formatCurrency(value)} />
          {showBand ? (
            <>
              <Area type="monotone" dataKey="upper_bound" stroke="#94a3b8" fill="#e2e8f0" fillOpacity={0.5} />
              <Area type="monotone" dataKey="lower_bound" stroke="#94a3b8" fill="#ffffff" fillOpacity={1} />
            </>
          ) : null}
          {showForecast ? (
            <Area type="monotone" dataKey="predicted_total_debit" stroke="#0d6e6e" fill="#99f6e4" fillOpacity={0.7} />
          ) : null}
          {showActualOverlay ? (
            <Line
              type="monotone"
              dataKey="actual_total_debit"
              stroke="#ef4444"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
            />
          ) : null}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ForecastTrendChart;