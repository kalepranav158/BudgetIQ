import { useMemo } from "react";
import ErrorState from "../../components/ui/ErrorState";
import Skeleton from "../../components/ui/Skeleton";
import DailySummaryTable from "./DailySummaryTable";
import { useDailySummaries } from "./useDailySummaries";

function DailySummaryView() {
  const { data, isLoading, error, refetch } = useDailySummaries();

  const rows = useMemo(() => {
    return [...(data || [])].sort((left, right) => String(right.date).localeCompare(String(left.date)));
  }, [data]);

  if (isLoading) {
    return <Skeleton rows={5} />;
  }

  if (error) {
    return <ErrorState message={error.message || "Unable to load daily summaries."} onRetry={refetch} />;
  }

  if (rows.length === 0) {
    return <p>No daily summaries yet. Upload a statement first.</p>;
  }

  return <DailySummaryTable rows={rows} />;
}

export default DailySummaryView;
