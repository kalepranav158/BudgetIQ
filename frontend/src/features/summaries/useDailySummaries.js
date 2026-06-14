import { useQuery } from "@tanstack/react-query";
import { getFastApi } from "../../lib/apiClient";

async function fetchDailySummaries() {
  const response = await getFastApi("/get_all_daily_summaries");
  const summaries = response?.summaries || response?.daily_summaries || response?.data || response;
  return Array.isArray(summaries) ? summaries : [];
}

export function useDailySummaries() {
  return useQuery({
    queryKey: ["daily-summaries"],
    queryFn: fetchDailySummaries,
    refetchOnWindowFocus: false
  });
}
