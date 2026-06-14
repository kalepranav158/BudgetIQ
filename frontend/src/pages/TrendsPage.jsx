import CategoryToggle from "../components/dashboard/CategoryToggle";
import MonthSelector from "../components/dashboard/MonthSelector";
import MonthlyTrendLine from "../components/charts/MonthlyTrendLine";
import Skeleton from "../components/ui/Skeleton";
import { DEBIT_CATEGORIES } from "../constants/categoryColors";
import { useDailySummaries } from "../hooks/useDailySummaries";
import { useDashboardMonth } from "../hooks/useDashboardMonth";
import { useMonthlySummaries } from "../hooks/useMonthlySummaries";
import { aggregateByMonth } from "../utils/summaryAggregations";
import { useMemo, useState } from "react";

const LINE_OPTIONS = [
  { value: "total_debit", label: "Total Debit" },
  { value: "total_credit", label: "Total Credit" },
  ...DEBIT_CATEGORIES.map((item) => ({ value: item, label: item }))
];

function TrendsPage() {
  const monthlyQuery = useMonthlySummaries();
  const dailyQuery = useDailySummaries();
  const [activeLines, setActiveLines] = useState(["total_debit", "total_credit"]);
  const { selectedMonth, setSelectedMonth, monthOptions } = useDashboardMonth(monthlyQuery.data || []);

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

  if (monthlyQuery.isLoading || dailyQuery.isLoading) {
    return <Skeleton rows={5} />;
  }

  const toggleLine = (value) => {
    setActiveLines((current) => {
      if (current.includes(value)) {
        const next = current.filter((item) => item !== value);
        return next.length ? next : ["total_debit"];
      }
      return [...current, value];
    });
  };

  return (
    <section className="page stack">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Trends</h1>
          <p className="page-subtitle">Toggle lines to compare totals and category trends.</p>
        </div>
        <MonthSelector options={monthOptions} selected={selectedMonth} onChange={setSelectedMonth} />
      </div>
      <MonthlyTrendLine data={trendData} activeLines={activeLines} />
      <CategoryToggle options={LINE_OPTIONS} activeValues={activeLines} onToggle={toggleLine} />
    </section>
  );
}

export default TrendsPage;
