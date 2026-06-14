import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getDjango, postUrlEncoded } from "../../lib/apiClient";

async function fetchKeywordMappings() {
  const response = await getDjango("/category-mapping");
  return Array.isArray(response?.mappings) ? response.mappings : [];
}

async function createKeywordMapping(payload) {
  return postUrlEncoded("/category-mapping/create", payload);
}

export function useKeywordMappings() {
  return useQuery({
    queryKey: ["keyword-mappings"],
    queryFn: fetchKeywordMappings,
    refetchOnWindowFocus: false
  });
}

export function useCreateKeywordMapping() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createKeywordMapping,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["keyword-mappings"] });
    }
  });
}
