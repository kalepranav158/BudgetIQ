import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { sortByYearMonthDesc } from "../utils/dateHelpers";

export function useDashboardMonth(monthlyRows) {
  const [searchParams, setSearchParams] = useSearchParams();

  const sorted = useMemo(() => sortByYearMonthDesc(monthlyRows || []), [monthlyRows]);

  const selected = useMemo(() => {
    const year = Number(searchParams.get("year"));
    const month = Number(searchParams.get("month"));

    if (year && month) {
      return { year, month };
    }

    if (sorted.length > 0) {
      return { year: Number(sorted[0].year), month: Number(sorted[0].month) };
    }

    return null;
  }, [searchParams, sorted]);

  const setSelectedMonth = (next) => {
    if (!next?.year || !next?.month) {
      return;
    }
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("year", String(next.year));
    nextParams.set("month", String(next.month));
    setSearchParams(nextParams);
  };

  return {
    selectedMonth: selected,
    setSelectedMonth,
    monthOptions: sorted
  };
}
