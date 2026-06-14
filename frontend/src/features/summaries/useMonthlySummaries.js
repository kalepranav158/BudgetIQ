import { useQuery } from "@tanstack/react-query";
import { getFastApi } from "../../lib/apiClient";

async function fetchMonthlySummaries() {
  const response = await getFastApi("/get_monthly_summaries");
  const summaries = response?.monthly_summaries || response?.monthly || response?.summaries || response?.data || response;
  return Array.isArray(summaries) ? summaries : [];
}

export function useMonthlySummaries() {
  return useQuery({
    queryKey: ["monthly-summaries"],
    queryFn: fetchMonthlySummaries,
    refetchOnWindowFocus: false
  });
}
