import { useQuery } from "@tanstack/react-query";
import { getFastApi } from "../lib/apiClient";

async function fetchDailyForecast(days = 7) {
  const response = await getFastApi(`/forecast_daily_spend?days=${days}`);
  return {
    days: Number(response?.days || days),
    modelVersion: response?.model_version || "unknown",
    selectedModel: response?.selected_model || "unknown",
    lastObservedDate: response?.last_observed_date || "",
    recentActuals: Array.isArray(response?.recent_actuals) ? response.recent_actuals : [],
    forecast: Array.isArray(response?.forecast) ? response.forecast : []
  };
}

export function useDailyForecast(days = 7) {
  return useQuery({
    queryKey: ["dailyForecast", days],
    queryFn: () => fetchDailyForecast(days),
    refetchOnWindowFocus: false,
    retry: false
  });
}