import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface SequenceStep {
  subject: string;
  bodyHtml: string;
  delayDays: number;
}

export interface Enrollment {
  id: string;
  leadId: string;
  leadEmail: string;
  leadName: string;
  currentStep: number;
  status: "active" | "paused" | "completed" | "unsubscribed";
  startedAt: string;
  nextSendAt: string | null;
  completedAt: string | null;
}

export interface SequenceStats {
  total: number;
  active: number;
  completed: number;
  paused: number;
  unsubscribed: number;
  completionRate: number;
}

export interface EmailSequence {
  id: string;
  name: string;
  description: string;
  steps: SequenceStep[];
  isActive: boolean;
  enrollments: Enrollment[];
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  stats?: SequenceStats;
}

// ── List ──────────────────────────────────────────────────────
export function useEmailSequences() {
  return useQuery({
    queryKey: ["email-sequences"],
    queryFn: async () => {
      return apiFetch("/api/v1/email-sequences/") as Promise<EmailSequence[]>;
    },
  });
}

// ── Get one ───────────────────────────────────────────────────
export function useEmailSequence(id: string | null) {
  return useQuery({
    queryKey: ["email-sequences", id],
    queryFn: async () => {
      return apiFetch(`/api/v1/email-sequences/${id}`) as Promise<EmailSequence>;
    },
    enabled: !!id,
  });
}

// ── Create ────────────────────────────────────────────────────
export function useCreateEmailSequence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string; description?: string; steps: SequenceStep[] }) => {
      return apiFetch("/api/v1/email-sequences/", { method: "POST", body: JSON.stringify(data) });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-sequences"] }),
  });
}

// ── Update ────────────────────────────────────────────────────
export function useUpdateEmailSequence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<{ name: string; description: string; steps: SequenceStep[] }> }) => {
      return apiFetch(`/api/v1/email-sequences/${id}`, { method: "PATCH", body: JSON.stringify(data) });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-sequences"] }),
  });
}

// ── Delete ────────────────────────────────────────────────────
export function useDeleteEmailSequence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return apiFetch(`/api/v1/email-sequences/${id}`, { method: "DELETE" });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-sequences"] }),
  });
}

// ── Activate / Deactivate ─────────────────────────────────────
export function useToggleEmailSequence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, active }: { id: string; active: boolean }) => {
      const action = active ? "activate" : "deactivate";
      return apiFetch(`/api/v1/email-sequences/${id}/${action}`, { method: "POST" });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-sequences"] }),
  });
}

// ── Enroll lead ───────────────────────────────────────────────
export function useEnrollLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ sequenceId, leadId }: { sequenceId: string; leadId: string }) => {
      return apiFetch(`/api/v1/email-sequences/${sequenceId}/enroll`, {
        method: "POST",
        body: JSON.stringify({ leadId }),
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-sequences"] }),
  });
}

// ── Enrollment actions ────────────────────────────────────────
export function useEnrollmentAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      sequenceId, enrollmentId, action,
    }: {
      sequenceId: string;
      enrollmentId: string;
      action: "advance" | "pause" | "resume" | "unsubscribe";
    }) => {
      return apiFetch(
        `/api/v1/email-sequences/${sequenceId}/enrollments/${enrollmentId}/${action}`,
        { method: "POST" }
      );
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-sequences"] }),
  });
}