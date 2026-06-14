import { useMemo } from "react";
import ErrorState from "../../components/ui/ErrorState";
import Skeleton from "../../components/ui/Skeleton";
import MonthlySummaryTable from "./MonthlySummaryTable";
import { useMonthlySummaries } from "./useMonthlySummaries";

function toSortValue(row) {
  const year = Number(row.year || 0);
  const month = Number(row.month || 0);
  return year * 100 + month;
}

function MonthlySummaryView() {
  const { data, isLoading, error, refetch } = useMonthlySummaries();

  const rows = useMemo(() => {
    return [...(data || [])].sort((left, right) => toSortValue(right) - toSortValue(left));
  }, [data]);

  if (isLoading) {
    return <Skeleton rows={4} />;
  }

  if (error) {
    return <ErrorState message={error.message || "Unable to load monthly summaries."} onRetry={refetch} />;
  }

  if (rows.length === 0) {
    return <p>No monthly data yet.</p>;
  }

  return <MonthlySummaryTable rows={rows} />;
}

export default MonthlySummaryView;
