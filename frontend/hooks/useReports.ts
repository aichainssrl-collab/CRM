import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface ReportSummary {
  id: string;
  title: string;
  timeRange: string;
  generatedBy: string;
  generatedByName: string;
  createdAt: string;
}

export interface ReportFull extends ReportSummary {
  data: {
    kpis: {
      totalLeads: number;
      newLeads: number;
      wonDeals: number;
      lostDeals: number;
      activeDeals: number;
      pipelineValue: number;
      revenue: number;
      conversionRate: number;
      topSources: { source: string; count: number }[];
    };
    funnel?: { stage: string; count: number }[];
    velocity?: { stage: string; avgDays: number; count: number }[];
    performance?: {
      userId: string;
      userName: string;
      leads: number;
      dealsWon: number;
      revenue: number;
      winRate: number;
    }[];
    forecast?: { stage: string; totalValue: number; weightedValue: number; count: number }[];
    forecastTotal?: { weighted: number; pipeline: number };
  };
}

interface GenerateParams {
  title?: string;
  timeRange?: string;
  includeFunnel?: boolean;
  includeVelocity?: boolean;
  includePerformance?: boolean;
  includeForecast?: boolean;
}

// ── List reports ──────────────────────────────────────────────
export function useReports(limit: number = 20) {
  return useQuery({
    queryKey: ["reports", limit],
    queryFn: async () => {
      return apiFetch(`/api/v1/reports?limit=${limit}`) as Promise<ReportSummary[]>;
    },
  });
}

// ── Get single report ─────────────────────────────────────────
export function useReport(id: string | null) {
  return useQuery({
    queryKey: ["reports", id],
    queryFn: async () => {
      return apiFetch(`/api/v1/reports/${id}`) as Promise<ReportFull>;
    },
    enabled: !!id,
  });
}

// ── Generate report ───────────────────────────────────────────
export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: GenerateParams) => {
      return apiFetch("/api/v1/reports/generate", {
        method: "POST",
        body: JSON.stringify(params),
      }) as Promise<ReportFull>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });
}

// ── Delete report ─────────────────────────────────────────────
export function useDeleteReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return apiFetch(`/api/v1/reports/${id}`, { method: "DELETE" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });
}

// ── Send report email ─────────────────────────────────────────
export function useSendReport() {
  return useMutation({
    mutationFn: async ({ id, to, message }: { id: string; to: string; message?: string }) => {
      return apiFetch(`/api/v1/reports/${id}/send`, {
        method: "POST",
        body: JSON.stringify({ to, message }),
      });
    },
  });
}