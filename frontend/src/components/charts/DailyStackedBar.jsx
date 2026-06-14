import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CATEGORY_COLORS, DEBIT_CATEGORIES } from "../../constants/categoryColors";
import { formatCurrency } from "../../utils/formatCurrency";
import ChartEmptyState from "./ChartEmptyState";

function DailyStackedBar({ rows }) {
  if (!rows?.length) {
    return <ChartEmptyState />;
  }

  const chartData = rows.map((row) => {
    const date = new Date(row.date);
    return {
      ...row,
      day: Number.isNaN(date.getTime()) ? row.date : date.getDate()
    };
  });

  return (
    <div className="chart-card" aria-label="Daily debit category chart">
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="day" />
          <YAxis tickFormatter={(value) => formatCurrency(value)} width={90} />
          <Tooltip formatter={(value) => formatCurrency(value)} />
          <Legend />
          {DEBIT_CATEGORIES.map((category) => (
            <Bar key={category} dataKey={category} stackId="debit" fill={CATEGORY_COLORS[category]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default DailyStackedBar;
