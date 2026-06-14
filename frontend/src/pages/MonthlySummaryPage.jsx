import MonthlySummaryView from "../features/summaries/MonthlySummaryView";

function MonthlySummaryPage() {
  return (
    <section className="page">
      <h1 className="page-title">Monthly Summary</h1>
      <p className="page-subtitle">View debit and credit totals by month.</p>
      <MonthlySummaryView />
    </section>
  );
}

export default MonthlySummaryPage;
