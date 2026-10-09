import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface InvoiceItem {
  productId?: string;
  name: string;
  description?: string;
  quantity: number;
  unitPrice: number;
  total?: number;
}

export interface Invoice {
  id: string;
  number: string;
  title: string;
  clientName: string;
  clientEmail: string;
  leadId?: string;
  dealId?: string;
  proposalId?: string;
  status: "draft" | "sent" | "paid" | "overdue" | "cancelled";
  items: InvoiceItem[];
  subtotal: number;
  taxRate: number;
  taxAmount: number;
  total: number;
  currency: string;
  issueDate?: string;
  dueDate?: string | null;
  notes?: string;
  sentAt?: string | null;
  paidAt?: string | null;
  createdAt: string;
}

export interface InvoiceStats {
  totalCount: number;
  totalValue: number;
  paidValue: number;
  outstandingValue: number;
  byStatus: Record<string, { count: number; totalValue: number }>;
}

export function useInvoices(status?: string) {
  return useQuery({
    queryKey: ["invoices", status ?? "all"],
    queryFn: async () =>
      apiFetch(`/api/v1/invoices/${status ? `?status=${status}` : ""}`) as Promise<Invoice[]>,
  });
}

export function useInvoiceStats() {
  return useQuery({
    queryKey: ["invoices", "stats"],
    queryFn: async () => apiFetch("/api/v1/invoices/stats") as Promise<InvoiceStats>,
  });
}

export function useCreateInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Invoice>) =>
      apiFetch("/api/v1/invoices/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices"] }),
  });
}

export function useInvoiceFromProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (proposalId: string) =>
      apiFetch(`/api/v1/invoices/from-proposal/${proposalId}`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices"] }),
  });
}

export function useUpdateInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Invoice> }) =>
      apiFetch(`/api/v1/invoices/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices"] }),
  });
}

export function useDeleteInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiFetch(`/api/v1/invoices/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices"] }),
  });
}

function action(id: string, verb: "send" | "mark-paid" | "cancel") {
  return apiFetch(`/api/v1/invoices/${id}/${verb}`, { method: "POST" });
}

export function useSendInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => action(id, "send"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices"] }),
  });
}

export function usePayInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => action(id, "mark-paid"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices"] }),
  });
}

export function useCancelInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => action(id, "cancel"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["invoices"] }),
  });
}
