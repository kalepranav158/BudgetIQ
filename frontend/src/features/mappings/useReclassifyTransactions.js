import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postUrlEncoded } from "../../lib/apiClient";

async function runReclassify() {
  return postUrlEncoded("/reparse-mapping", { kind: "all" }, { timeout: 180000 });
}

export function useReclassifyTransactions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: runReclassify,
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["keyword-mappings"] });
      await queryClient.invalidateQueries({ queryKey: ["regex-mappings"] });
      await queryClient.invalidateQueries({ queryKey: ["account-mappings"] });
      await queryClient.invalidateQueries({ queryKey: ["transactions"] });
      await queryClient.invalidateQueries({ queryKey: ["dailySummaries"] });
      await queryClient.invalidateQueries({ queryKey: ["monthlySummaries"] });
      await queryClient.refetchQueries({ queryKey: ["transactions"], type: "active" });
      await queryClient.refetchQueries({ queryKey: ["dailySummaries"], type: "active" });
      await queryClient.refetchQueries({ queryKey: ["monthlySummaries"], type: "active" });
      return data;
    },
  });
}
