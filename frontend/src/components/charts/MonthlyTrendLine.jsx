import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CATEGORY_COLORS } from "../../constants/categoryColors";
import { getMonthLabel } from "../../utils/dateHelpers";
import { formatCurrency } from "../../utils/formatCurrency";
import ChartEmptyState from "./ChartEmptyState";

const LINE_COLORS = {
  total_debit: "#EF4444",
  total_credit: "#22C55E",
  ...CATEGORY_COLORS
};

function MonthlyTrendLine({ data, activeLines, compact = false }) {
  if (!data?.length) {
    return <ChartEmptyState />;
  }

  const chartData = data.map((row) => ({
    ...row,
    label: getMonthLabel(row.year, row.month, compact)
  }));

  return (
    <div className="chart-card" aria-label="Monthly debit and credit trends">
      <ResponsiveContainer width="100%" height={compact ? 250 : 340}>
        <LineChart data={chartData}>
          <XAxis dataKey="label" />
          <YAxis tickFormatter={(value) => formatCurrency(value)} width={90} />
          <Tooltip formatter={(value) => formatCurrency(value)} />
          {(activeLines || ["total_debit", "total_credit"]).map((lineKey) => (
            <Line key={lineKey} type="monotone" dataKey={lineKey} stroke={LINE_COLORS[lineKey] || "#111827"} strokeWidth={2} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default MonthlyTrendLine;
