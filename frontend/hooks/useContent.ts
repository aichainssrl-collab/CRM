import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface ContentItem {
  id: string;
  title: string;
  type: "email" | "ad_copy" | "social" | "landing" | "blog" | "other" | string;
  body: string;
  description: string;
  tags: string[];
  language: string;
  source: string;
  createdAt: string;
  updatedAt: string;
}

export interface ContentStats {
  totalCount: number;
  byType: Record<string, number>;
}

export function useContent(filters?: { type?: string; tag?: string; q?: string }) {
  const params = new URLSearchParams();
  if (filters?.type) params.set("type", filters.type);
  if (filters?.tag) params.set("tag", filters.tag);
  if (filters?.q) params.set("q", filters.q);
  const qs = params.toString();
  return useQuery({
    queryKey: ["content", filters ?? {}],
    queryFn: async () =>
      apiFetch(`/api/v1/content/${qs ? `?${qs}` : ""}`) as Promise<ContentItem[]>,
  });
}

export function useContentStats() {
  return useQuery({
    queryKey: ["content", "stats"],
    queryFn: async () => apiFetch("/api/v1/content/stats") as Promise<ContentStats>,
  });
}

export function useContentTags() {
  return useQuery({
    queryKey: ["content", "tags"],
    queryFn: async () => apiFetch("/api/v1/content/tags") as Promise<string[]>,
  });
}

export function useCreateContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<ContentItem>) =>
      apiFetch("/api/v1/content/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["content"] }),
  });
}

export function useUpdateContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<ContentItem> }) =>
      apiFetch(`/api/v1/content/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["content"] }),
  });
}

export function useDeleteContent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiFetch(`/api/v1/content/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["content"] }),
  });
}
