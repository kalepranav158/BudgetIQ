import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postUrlEncoded } from "../../lib/apiClient";

async function reparseMapping(payload) {
  return postUrlEncoded("/reparse-mapping", payload);
}

export function useReparseMapping() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: reparseMapping,
    onSuccess: async () => {
      // Refresh transactions and mappings after reparsing
      await qc.invalidateQueries({ queryKey: ["transactions"] });
      await qc.invalidateQueries({ queryKey: ["keyword-mappings"] });
      await qc.invalidateQueries({ queryKey: ["regex-mappings"] });
    },
  });
}
