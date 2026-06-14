import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { SUBTYPE_COLORS } from "../../constants/subtypeColors";
import { formatCurrency } from "../../utils/formatCurrency";
import ChartEmptyState from "./ChartEmptyState";

function SubtypeDonut({ totals, activeSubtype, onSliceClick }) {
  const chartData = Object.entries(totals || {})
    .map(([name, value]) => ({ name, value: Number(value || 0) }))
    .filter((item) => item.value > 0);

  if (chartData.length === 0) {
    return <ChartEmptyState />;
  }

  return (
    <div className="chart-card" aria-label="Subtype breakdown">
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" outerRadius={110} onClick={(entry) => onSliceClick?.(entry?.name || null)}>
            {chartData.map((entry) => (
              <Cell
                key={entry.name}
                fill={SUBTYPE_COLORS[entry.name] || "#9CA3AF"}
                fillOpacity={activeSubtype && activeSubtype !== entry.name ? 0.45 : 1}
              />
            ))}
          </Pie>
          <Tooltip formatter={(value) => formatCurrency(value)} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default SubtypeDonut;
