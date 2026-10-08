import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useEnrichLead(leadId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiFetch(`/api/v1/leads/${leadId}/enrich`, { method: "POST" }),
    onSuccess: () => {
      // Dopo 4 secondi ricarica il lead — l'enrichment è asincrono (Cloud Task)
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["lead", leadId] });
        queryClient.invalidateQueries({ queryKey: ["leads"] });
      }, 4000);
    },
  });
}
