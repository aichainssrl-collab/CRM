import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface EmailTemplate {
  id: string;
  key: string;
  name: string;
  subject: string;
  bodyHtml: string;
  category: string;
  createdAt: string;
}

export function useEmailTemplates(category?: string) {
  return useQuery({
    queryKey: ["email-templates", category ?? "all"],
    queryFn: async () =>
      apiFetch(
        `/api/v1/email-templates/${category ? `?category=${category}` : ""}`
      ) as Promise<EmailTemplate[]>,
  });
}

export function useCreateEmailTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<EmailTemplate>) =>
      apiFetch("/api/v1/email-templates/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-templates"] }),
  });
}

export function useUpdateEmailTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<EmailTemplate> }) =>
      apiFetch(`/api/v1/email-templates/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-templates"] }),
  });
}

export function useDeleteEmailTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      apiFetch(`/api/v1/email-templates/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-templates"] }),
  });
}

export function useProcessDueEnrollments() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () =>
      apiFetch("/api/v1/email-sequences/process-due", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["email-sequences"] }),
  });
}
