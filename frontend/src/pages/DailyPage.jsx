import DailyStackedBar from "../components/charts/DailyStackedBar";
import MonthSelector from "../components/dashboard/MonthSelector";
import TopSpendingDaysTable from "../components/dashboard/TopSpendingDaysTable";
import Skeleton from "../components/ui/Skeleton";
import { useDailySummaries } from "../hooks/useDailySummaries";
import { useDashboardMonth } from "../hooks/useDashboardMonth";
import { useMonthlySummaries } from "../hooks/useMonthlySummaries";
import { sameYearMonth } from "../utils/dateHelpers";
import { topSpendingDays } from "../utils/summaryAggregations";

function DailyPage() {
  const monthlyQuery = useMonthlySummaries();
  const dailyQuery = useDailySummaries();
  const { selectedMonth, setSelectedMonth, monthOptions } = useDashboardMonth(monthlyQuery.data || []);

  if (monthlyQuery.isLoading || dailyQuery.isLoading) {
    return <Skeleton rows={5} />;
  }

  const monthRows = (dailyQuery.data || []).filter((row) => selectedMonth && sameYearMonth(row.date, selectedMonth.year, selectedMonth.month));
  const topRows = topSpendingDays(monthRows, 5);

  return (
    <section className="page stack">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Daily View</h1>
          <p className="page-subtitle">Daily category-wise debit spread for the selected month.</p>
        </div>
        <MonthSelector options={monthOptions} selected={selectedMonth} onChange={setSelectedMonth} />
      </div>
      <DailyStackedBar rows={monthRows} />
      <h2>Top Spending Days</h2>
      <TopSpendingDaysTable rows={topRows} />
    </section>
  );
}

export default DailyPage;
