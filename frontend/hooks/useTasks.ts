import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface Task {
  id: string;
  leadId: string;
  title: string;
  description?: string;
  type: string;
  priority: string;
  dueDate: string;
  reminderAt?: string;
  assignedTo: string;
  dealId?: string;
  createdBy: string;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export function useTasks(leadId?: string, status?: string, dueBefore?: string) {
  return useQuery({
    queryKey: leadId ? ["tasks", "lead", leadId] : ["tasks", { status, dueBefore }],
    queryFn: async () => {
      if (leadId) {
        return apiFetch(`/api/v1/leads/${leadId}/tasks`) as Promise<Task[]>;
      }
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      if (dueBefore) params.append("due_before", dueBefore);
      const qs = params.toString();
      const endpoint = qs ? `/api/v1/tasks?${qs}` : "/api/v1/tasks";
      return apiFetch(endpoint) as Promise<Task[]>;
    },
  });
}

export function useCreateTask(leadId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Task>) => {
      const endpoint = `/api/v1/leads/${leadId}/tasks`;
      return apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useUpdateTask(leadId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Task> }) => {
      return apiFetch(`/api/v1/leads/${leadId}/tasks/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useDeleteTask(leadId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return apiFetch(`/api/v1/leads/${leadId}/tasks/${id}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
