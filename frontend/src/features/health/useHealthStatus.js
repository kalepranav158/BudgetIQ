import { useQuery } from "@tanstack/react-query";
import { getDjango, getFastApi } from "../../lib/apiClient";

async function fetchHealth(urlGetter) {
  try {
    await urlGetter("/health");
    return { online: true, checkedAt: new Date().toISOString() };
  } catch (error) {
    return { online: false, checkedAt: new Date().toISOString(), message: error.message };
  }
}

export function useHealthStatus() {
  const djangoQuery = useQuery({
    queryKey: ["health", "django"],
    queryFn: () => fetchHealth(getDjango),
    refetchInterval: 60000,
    staleTime: 0,
    retry: false,
    refetchOnWindowFocus: false
  });

  const fastapiQuery = useQuery({
    queryKey: ["health", "fastapi"],
    queryFn: () => fetchHealth(getFastApi),
    refetchInterval: 60000,
    staleTime: 0,
    retry: false,
    refetchOnWindowFocus: false
  });

  return {
    django: djangoQuery.data,
    fastapi: fastapiQuery.data,
    isLoading: djangoQuery.isLoading || fastapiQuery.isLoading,
    isError: djangoQuery.isError || fastapiQuery.isError,
    refetchAll: async () => {
      await Promise.all([djangoQuery.refetch(), fastapiQuery.refetch()]);
    }
  };
}
