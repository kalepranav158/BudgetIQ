import DailySummaryView from "../features/summaries/DailySummaryView";

function DailySummaryPage() {
  return (
    <section className="page">
      <h1 className="page-title">Daily Summary</h1>
      <p className="page-subtitle">View category-level totals by day.</p>
      <DailySummaryView />
    </section>
  );
}

export default DailySummaryPage;
