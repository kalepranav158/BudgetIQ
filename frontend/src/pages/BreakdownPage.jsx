import { useMemo, useState } from "react";
import CategoryDonut from "../components/charts/CategoryDonut";
import SubtypeDonut from "../components/charts/SubtypeDonut";
import MonthSelector from "../components/dashboard/MonthSelector";
import Button from "../components/ui/Button";
import Skeleton from "../components/ui/Skeleton";
import Table from "../components/ui/Table";
import { useDailySummaries } from "../hooks/useDailySummaries";
import { useDashboardMonth } from "../hooks/useDashboardMonth";
import { useMonthlySummaries } from "../hooks/useMonthlySummaries";
import { useTransactions } from "../features/transactions/useTransactions";
import { sameYearMonth } from "../utils/dateHelpers";
import { formatCurrency } from "../utils/formatCurrency";
import { computeCategoryTotals, computeSubtypeTotals } from "../utils/summaryAggregations";

const PAGE_SIZE = 25;

function BreakdownPage() {
  const monthlyQuery = useMonthlySummaries();
  const dailyQuery = useDailySummaries();
  const transactionsQuery = useTransactions();
  const { selectedMonth, setSelectedMonth, monthOptions } = useDashboardMonth(monthlyQuery.data || []);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedSubtype, setSelectedSubtype] = useState(null);
  const [page, setPage] = useState(1);

  const monthRows = (dailyQuery.data || []).filter((row) => selectedMonth && sameYearMonth(row.date, selectedMonth.year, selectedMonth.month));

  const monthTransactions = useMemo(() => {
    return (transactionsQuery.data || []).filter((tx) => selectedMonth && sameYearMonth(tx.date, selectedMonth.year, selectedMonth.month));
  }, [selectedMonth, transactionsQuery.data]);

  const subtypeTotals = computeSubtypeTotals(monthTransactions);
  const categoryTotals = computeCategoryTotals(monthRows);

  const filteredTransactions = monthTransactions.filter((tx) => {
    const categoryMatch = !selectedCategory || tx.category === selectedCategory;
    const subtypeMatch = !selectedSubtype || tx.subtype === selectedSubtype;
    return categoryMatch && subtypeMatch;
  });

  const totalPages = Math.max(1, Math.ceil(filteredTransactions.length / PAGE_SIZE));
  const pageRows = filteredTransactions.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const formatConfidence = (value) => {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return "-";
    }
    return number.toFixed(2);
  };

  if (monthlyQuery.isLoading || dailyQuery.isLoading || transactionsQuery.isLoading) {
    return <Skeleton rows={7} />;
  }

  return (
    <section className="page stack">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Breakdown</h1>
          <p className="page-subtitle">Click category or subtype slices to filter transactions.</p>
        </div>
        <MonthSelector options={monthOptions} selected={selectedMonth} onChange={setSelectedMonth} />
      </div>

      <div className="dashboard-two-col">
        <div>
          <h2>Category Breakdown</h2>
          <CategoryDonut totals={categoryTotals} activeCategory={selectedCategory} onSliceClick={setSelectedCategory} />
        </div>
        <div>
          <h2>Subtype Breakdown</h2>
          <SubtypeDonut totals={subtypeTotals} activeSubtype={selectedSubtype} onSliceClick={setSelectedSubtype} />
        </div>
      </div>

      <div className="breakdown-controls">
        <Button variant="secondary" onClick={() => { setSelectedCategory(null); setSelectedSubtype(null); setPage(1); }}>
          Reset Filters
        </Button>
      </div>

      {pageRows.length === 0 ? (
        <p>No transactions match the selected filters.</p>
      ) : (
        <Table>
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Description</th>
              <th scope="col">Amount</th>
              <th scope="col">Category</th>
              <th scope="col">Subtype</th>
              <th scope="col">Category Source</th>
              <th scope="col">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((tx) => (
              <tr key={tx.id || `${tx.date}-${tx.description}-${tx.amount}`}>
                <td>{tx.date}</td>
                <td>{tx.description}</td>
                <td>{formatCurrency(tx.amount)}</td>
                <td>{tx.category}</td>
                <td>{tx.subtype}</td>
                <td>{tx.category_source || "-"}</td>
                <td>{formatConfidence(tx.confidence)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      <div className="pagination">
        <button className="button button--secondary" type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>
          Previous
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button className="button button--secondary" type="button" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page >= totalPages}>
          Next
        </button>
      </div>
    </section>
  );
}

export default BreakdownPage;
