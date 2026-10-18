import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface AgentToolStep {
  type: "tool" | "assistant";
  name?: string;
  args?: Record<string, unknown>;
  result?: {
    ok?: boolean;
    message?: string;
    error?: string;
    approvalRequired?: boolean;
    approvalId?: string;
    [k: string]: unknown;
  };
  content?: string;
}

export interface AgentRunResult {
  ok: boolean;
  mode: "parser" | "llm" | "llm_error" | "fallback" | "invalid" | "error" | "none";
  reply: string;
  steps: AgentToolStep[];
  sessionId?: string;
  durationMs?: number;
  error?: string;
}

export interface AgentApproval {
  id: string;
  tool: string;
  reason: string;
  args?: Record<string, unknown>;
  createdAt?: string;
  userId?: string;
}

export interface AgentMemoryFact {
  id: string;
  text: string;
  kind: string;
  at?: string;
}

export interface AgentRunSummary {
  id: string;
  message?: string;
  mode?: string;
  ok?: boolean;
  durationMs?: number;
  tools?: string[];
  createdAt?: string;
}

export function useAgentRun() {
  return useMutation({
    mutationFn: (payload: { message: string; sessionId?: string }) =>
      apiFetch("/api/v1/agent/run", {
        method: "POST",
        body: JSON.stringify({
          message: payload.message,
          sessionId: payload.sessionId,
        }),
      }) as Promise<AgentRunResult>,
  });
}

export function useAgentApprovals(enabled = true) {
  return useQuery({
    queryKey: ["agent-approvals"],
    enabled,
    queryFn: () =>
      apiFetch("/api/v1/agent/approvals") as Promise<{ approvals: AgentApproval[] }>,
    refetchInterval: 15_000,
  });
}

export function useAgentApprovalDecision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { id: string; approve: boolean }) =>
      apiFetch(`/api/v1/agent/approvals/${payload.id}/decision`, {
        method: "POST",
        body: JSON.stringify({ approve: payload.approve }),
      }) as Promise<{ ok: boolean; status?: string; tool?: string; args?: Record<string, unknown> }>,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["agent-approvals"] });
      void qc.invalidateQueries({ queryKey: ["agent-runs"] });
    },
  });
}

export function useAgentMemory(enabled = true) {
  return useQuery({
    queryKey: ["agent-memory"],
    enabled,
    queryFn: () =>
      apiFetch("/api/v1/agent/memory") as Promise<{ facts: AgentMemoryFact[] }>,
  });
}

export function useAgentRuns(enabled = true, limit = 15) {
  return useQuery({
    queryKey: ["agent-runs", limit],
    enabled,
    queryFn: () =>
      apiFetch(`/api/v1/agent/runs?limit=${limit}`) as Promise<{ runs: AgentRunSummary[] }>,
    refetchInterval: 30_000,
  });
}
