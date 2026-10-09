import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface ProposalItem {
  productId?: string;
  name: string;
  description?: string;
  quantity: number;
  unitPrice: number;
  total?: number;
}

export interface Proposal {
  id: string;
  number: string;
  title: string;
  clientName: string;
  clientEmail: string;
  leadId?: string;
  dealId?: string;
  status: "draft" | "sent" | "accepted" | "rejected" | "expired";
  items: ProposalItem[];
  subtotal: number;
  taxRate: number;
  taxAmount: number;
  total: number;
  currency: string;
  validUntil?: string | null;
  notes?: string;
  sentAt?: string | null;
  acceptedAt?: string | null;
  rejectedAt?: string | null;
  createdAt: string;
}

export interface ProposalStats {
  totalCount: number;
  totalValue: number;
  byStatus: Record<string, { count: number; totalValue: number }>;
}

export function useProposals(status?: string) {
  return useQuery({
    queryKey: ["proposals", status ?? "all"],
    queryFn: async () =>
      apiFetch(`/api/v1/proposals/${status ? `?status=${status}` : ""}`) as Promise<Proposal[]>,
  });
}

export function useProposalStats() {
  return useQuery({
    queryKey: ["proposals", "stats"],
    queryFn: async () => apiFetch("/api/v1/proposals/stats") as Promise<ProposalStats>,
  });
}

export function useCreateProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Proposal>) =>
      apiFetch("/api/v1/proposals/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["proposals"] });
    },
  });
}

export function useUpdateProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Proposal> }) =>
      apiFetch(`/api/v1/proposals/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["proposals"] });
    },
  });
}

export function useDeleteProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiFetch(`/api/v1/proposals/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["proposals"] });
    },
  });
}

function statusAction(id: string, action: "send" | "accept" | "reject") {
  return apiFetch(`/api/v1/proposals/${id}/${action}`, { method: "POST" });
}

export function useSendProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => statusAction(id, "send"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["proposals"] }),
  });
}

export function useAcceptProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => statusAction(id, "accept"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["proposals"] }),
  });
}

export function useRejectProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => statusAction(id, "reject"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["proposals"] }),
  });
}
