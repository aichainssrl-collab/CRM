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
  mode: "parser" | "llm" | "llm_error" | "fallback" | "none";
  reply: string;
  steps: AgentToolStep[];
  error?: string;
}

export function useAgentRun() {
  return useMutation({
    mutationFn: (message: string) =>
      apiFetch("/api/v1/agent/run", {
        method: "POST",
        body: JSON.stringify({ message }),
      }) as Promise<AgentRunResult>,
  });
}
