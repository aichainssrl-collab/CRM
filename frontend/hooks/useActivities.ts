import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface Activity {
  id: string;
  leadId: string;
  type: string;
  title?: string;
  body?: string;
  metadata: Record<string, any>;
  userId?: string;
  createdAt: string;
}

export function useActivities(leadId: string) {
  return useQuery({
    queryKey: ["activities", leadId],
    queryFn: async () => {
      return apiFetch(`/api/v1/leads/${leadId}/activities`) as Promise<Activity[]>;
    },
    enabled: !!leadId,
  });
}

export function useCreateActivity(leadId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Activity>) => {
      return apiFetch(`/api/v1/leads/${leadId}/activities`, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["activities", leadId] });
      queryClient.invalidateQueries({ queryKey: ["leads", leadId] }); // Update lead detail too
    },
  });
}
