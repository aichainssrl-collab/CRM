import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface Competitor {
  id: string;
  name: string;
  website: string;
  description: string;
  tags: string[];
  status: "active" | "archived";
  lastCheckedAt?: string | null;
  lastChangeAt?: string | null;
  changeCount: number;
  createdAt: string;
}

export interface CompetitorSnapshot {
  id: string;
  competitorId: string;
  url: string;
  title: string;
  metaDescription: string;
  headings: string[];
  pricingMentions: string[];
  pricingKeywords: string[];
  bodyExcerpt: string;
  bodyHash: string;
  capturedAt: string;
}

export interface CompetitorChange {
  id: string;
  competitorId: string;
  field: string;
  from: string;
  to: string;
  detectedAt: string;
}

export interface CompetitorStats {
  totalCount: number;
  activeCount: number;
  changeCount: number;
  snapshotCount: number;
  lastMonitorRun?: {
    ranAt: string;
    competitorCount: number;
    okCount: number;
    failedCount: number;
    changeCount: number;
  } | null;
}

export function useCompetitors(status?: string) {
  return useQuery({
    queryKey: ["competitors", status ?? "all"],
    queryFn: async () =>
      apiFetch(
        `/api/v1/competitors/${status ? `?status=${status}` : ""}`
      ) as Promise<Competitor[]>,
  });
}

export function useCompetitorStats() {
  return useQuery({
    queryKey: ["competitors", "stats"],
    queryFn: async () => apiFetch("/api/v1/competitors/stats") as Promise<CompetitorStats>,
  });
}

export function useCompetitorChanges(competitorId?: string) {
  return useQuery({
    queryKey: ["competitors", "changes", competitorId ?? "all"],
    queryFn: async () =>
      apiFetch(
        competitorId
          ? `/api/v1/competitors/${competitorId}/changes`
          : "/api/v1/competitors/changes"
      ) as Promise<CompetitorChange[]>,
  });
}

export function useCompetitorSnapshots(competitorId: string | null) {
  return useQuery({
    queryKey: ["competitors", "snapshots", competitorId],
    enabled: !!competitorId,
    queryFn: async () =>
      apiFetch(`/api/v1/competitors/${competitorId}/snapshots`) as Promise<CompetitorSnapshot[]>,
  });
}

export function useCreateCompetitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Competitor>) =>
      apiFetch("/api/v1/competitors/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useUpdateCompetitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Competitor> }) =>
      apiFetch(`/api/v1/competitors/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useDeleteCompetitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiFetch(`/api/v1/competitors/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useScanCompetitor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      apiFetch(`/api/v1/competitors/${id}/scan`, { method: "POST", body: JSON.stringify({}) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["competitors"] }),
  });
}

export function useScanAll() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => apiFetch("/api/v1/competitors/scan-all", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["competitors"] }),
  });
}
