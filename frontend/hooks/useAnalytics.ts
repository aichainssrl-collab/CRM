import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────
export interface FunnelStage {
  stage: string;
  count: number;
}

export interface VelocityItem {
  stage: string;
  avgDays: number;
  count: number;
}

export interface PerformanceUser {
  userId: string;
  userName: string;
  leads: number;
  dealsWon: number;
  dealsActive: number;
  dealsLost: number;
  revenue: number;
  pipelineValue: number;
  winRate: number;
}

export interface TrendPoint {
  period: string;
  leads: number;
  dealsWon: number;
  dealsWonValue: number;
  dealsLost: number;
  newDeals: number;
}

export interface ForecastItem {
  stage: string;
  count: number;
  totalValue: number;
  weightedValue: number;
  avgProbability: number;
}

export interface CohortRow {
  month: string;
  total: number;
  contacted: number;
  qualified: number;
  converted: number;
  contactRate: number;
  qualifyRate: number;
  convertRate: number;
}

// ── Hooks ─────────────────────────────────────────────────────
export function useFunnel(timeRange: string = "90d") {
  return useQuery({
    queryKey: ["analytics", "funnel", timeRange],
    queryFn: async () => {
      const data = await apiFetch(`/api/v1/analytics/funnel?time_range=${timeRange}`);
      return data.funnel as FunnelStage[];
    },
  });
}

export function useVelocity() {
  return useQuery({
    queryKey: ["analytics", "velocity"],
    queryFn: async () => {
      const data = await apiFetch("/api/v1/analytics/velocity");
      return data.velocity as VelocityItem[];
    },
  });
}

export function usePerformance(timeRange: string = "90d") {
  return useQuery({
    queryKey: ["analytics", "performance", timeRange],
    queryFn: async () => {
      const data = await apiFetch(`/api/v1/analytics/performance?time_range=${timeRange}`);
      return data.performance as PerformanceUser[];
    },
  });
}

export function useTrends(period: string = "week", timeRange: string = "90d") {
  return useQuery({
    queryKey: ["analytics", "trends", period, timeRange],
    queryFn: async () => {
      const data = await apiFetch(`/api/v1/analytics/trends?period=${period}&time_range=${timeRange}`);
      return data.series as TrendPoint[];
    },
  });
}

export function useForecast() {
  return useQuery({
    queryKey: ["analytics", "forecast"],
    queryFn: async () => {
      const data = await apiFetch("/api/v1/analytics/forecast");
      return {
        forecast: data.forecast as ForecastItem[],
        totalWeighted: data.totalWeighted as number,
        totalPipeline: data.totalPipeline as number,
      };
    },
  });
}

export function useCohorts(months: number = 6) {
  return useQuery({
    queryKey: ["analytics", "cohorts", months],
    queryFn: async () => {
      const data = await apiFetch(`/api/v1/analytics/cohorts?months=${months}`);
      return data.cohorts as CohortRow[];
    },
  });
}