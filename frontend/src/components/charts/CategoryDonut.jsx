import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { CATEGORY_COLORS, DEBIT_CATEGORIES } from "../../constants/categoryColors";
import { formatCurrency } from "../../utils/formatCurrency";
import ChartEmptyState from "./ChartEmptyState";

function CategoryDonut({ totals, onSliceClick, activeCategory, ariaLabel }) {
  const chartData = DEBIT_CATEGORIES
    .map((category) => ({ name: category, value: Number(totals?.[category] || 0) }))
    .filter((item) => item.value > 0);

  if (chartData.length === 0) {
    return <ChartEmptyState />;
  }

  return (
    <div className="chart-card" aria-label={ariaLabel || "Category spending breakdown"}>
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            outerRadius={110}
            onClick={(entry) => onSliceClick?.(entry?.name || null)}
          >
            {chartData.map((entry) => (
              <Cell
                key={entry.name}
                fill={CATEGORY_COLORS[entry.name] || "#9CA3AF"}
                fillOpacity={activeCategory && activeCategory !== entry.name ? 0.45 : 1}
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

export default CategoryDonut;
