import { useQuery } from "@tanstack/react-query";
import { getFastApi } from "../lib/apiClient";

async function fetchMonthlySummaries() {
  const response = await getFastApi("/get_monthly_summaries");
  const summaries = response?.monthly_summaries || response?.monthly || response?.summaries || response?.data || [];
  return Array.isArray(summaries) ? summaries : [];
}

export function useMonthlySummaries() {
  return useQuery({
    queryKey: ["monthlySummaries"],
    queryFn: fetchMonthlySummaries,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false
  });
}
