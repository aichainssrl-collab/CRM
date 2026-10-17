import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface AgentToolStep {
  type: "tool" | "assistant";
  name?: string;
  args?: Record<string, unknown>;
  result?: {
    ok?: boolean;
    message?: string;
    error?: string;
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
