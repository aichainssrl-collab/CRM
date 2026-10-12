import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface LlmSettings {
  provider: string;
  model: string;
  baseUrl: string;
  apiKeySet: boolean;
  apiKeyMasked: string | null;
  apiKey: null;
  localModel: string;
  localBaseUrl: string;
  source: "database" | "env";
}

export function useLlmSettings() {
  return useQuery({
    queryKey: ["admin", "llm-settings"],
    queryFn: () => apiFetch("/api/v1/admin/llm-settings") as Promise<LlmSettings>,
  });
}

export function useUpdateLlmSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      provider?: string;
      model?: string;
      baseUrl?: string;
      apiKey?: string;
      clearApiKey?: boolean;
      localModel?: string;
      localBaseUrl?: string;
    }) =>
      apiFetch("/api/v1/admin/llm-settings", {
        method: "PUT",
        body: JSON.stringify(payload),
      }) as Promise<LlmSettings>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "llm-settings"] });
    },
  });
}

export function useTestLlmSettings() {
  return useMutation({
    mutationFn: (payload?: {
      provider?: string;
      model?: string;
      baseUrl?: string;
      apiKey?: string;
      localModel?: string;
      localBaseUrl?: string;
    }) =>
      apiFetch("/api/v1/admin/llm-settings/test", {
        method: "POST",
        body: JSON.stringify(payload ?? {}),
      }) as Promise<{
        ok: boolean;
        model?: string;
        provider?: string;
        baseUrl?: string;
        error?: string;
      }>,
  });
}
