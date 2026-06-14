import { useQuery } from "@tanstack/react-query";
import { getFastApi } from "../../lib/apiClient";

async function fetchTransactions() {
  const response = await getFastApi("/get_transactions");
  return Array.isArray(response?.transactions) ? response.transactions : [];
}

export function useTransactions() {
  return useQuery({
    queryKey: ["transactions"],
    queryFn: fetchTransactions,
    refetchOnWindowFocus: false
  });
}
