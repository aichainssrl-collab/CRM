import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface DashboardMetrics {
  totalLeads: number;
  newLeads: number;
  activeDeals: number;
  pipelineValue: number;
  conversionRate: number;
}

export function useDashboardMetrics(timeRange: string = "30d") {
  return useQuery({
    queryKey: ["dashboard", "metrics", timeRange],
    queryFn: async () => {
      return apiFetch(`/api/v1/dashboard/metrics?timeRange=${timeRange}`) as Promise<DashboardMetrics>;
    },
  });
}
