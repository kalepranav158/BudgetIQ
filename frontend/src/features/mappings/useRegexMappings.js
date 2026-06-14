import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getDjango, postUrlEncoded } from "../../lib/apiClient";

async function fetchRegexMappings() {
  const response = await getDjango("/regex-mapping");
  return Array.isArray(response?.mappings) ? response.mappings : [];
}

async function createRegexMapping(payload) {
  return postUrlEncoded("/regex-mapping/create", payload);
}

export function useRegexMappings() {
  return useQuery({
    queryKey: ["regex-mappings"],
    queryFn: fetchRegexMappings,
    refetchOnWindowFocus: false
  });
}

export function useCreateRegexMapping() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createRegexMapping,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["regex-mappings"] });
    }
  });
}
