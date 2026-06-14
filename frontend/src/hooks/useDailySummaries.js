import { useQuery } from "@tanstack/react-query";
import { getFastApi } from "../lib/apiClient";

async function fetchDailySummaries() {
  const response = await getFastApi("/get_all_daily_summaries");
  if (Array.isArray(response)) {
    return response;
  }
  const summaries = response?.summaries || response?.daily_summaries || response?.data || [];
  return Array.isArray(summaries) ? summaries : [];
}

export function useDailySummaries() {
  return useQuery({
    queryKey: ["dailySummaries"],
    queryFn: fetchDailySummaries,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false
  });
}
