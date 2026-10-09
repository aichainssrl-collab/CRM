import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export type WorkflowTrigger =
  | "lead_created"
  | "deal_stage_changed"
  | "proposal_accepted"
  | "task_completed"
  | "manual";

export type ActionType =
  | "create_task"
  | "add_tag"
  | "update_lead_status"
  | "send_notification"
  | "send_email";

export interface WorkflowCondition {
  field: string;
  op: "eq" | "ne" | "contains" | "gte" | "lte" | "in";
  value: unknown;
}

export interface WorkflowAction {
  type: ActionType | string;
  title?: string;
  description?: string;
  dueDate?: string;
  priority?: string;
  assignedTo?: string;
  tag?: string;
  status?: string;
  userId?: string;
  body?: string;
  to?: string;
  subject?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  trigger: WorkflowTrigger | string;
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
  isActive: boolean;
  runCount: number;
  lastRunAt?: string | null;
  createdAt: string;
}

export interface WorkflowStats {
  total: number;
  active: number;
  topRuns: { id: string; name: string; runCount: number }[];
}

export function useWorkflows() {
  return useQuery({
    queryKey: ["workflows"],
    queryFn: async () => apiFetch("/api/v1/workflows/") as Promise<Workflow[]>,
  });
}

export function useWorkflowStats() {
  return useQuery({
    queryKey: ["workflows", "stats"],
    queryFn: async () => apiFetch("/api/v1/workflows/stats") as Promise<WorkflowStats>,
  });
}

export function useCreateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Workflow>) =>
      apiFetch("/api/v1/workflows/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows"] }),
  });
}

export function useUpdateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Workflow> }) =>
      apiFetch(`/api/v1/workflows/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows"] }),
  });
}

export function useDeleteWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiFetch(`/api/v1/workflows/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows"] }),
  });
}

export function useToggleWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      apiFetch(`/api/v1/workflows/${id}/toggle`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows"] }),
  });
}
