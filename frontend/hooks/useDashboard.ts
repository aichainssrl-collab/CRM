import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface DueTask {
  id: string;
  title?: string;
  dueDate?: string | null;
  priority?: string;
  leadId?: string;
  isOverdue?: boolean;
  isToday?: boolean;
}

export interface DashboardMetrics {
  totalLeads: number;
  newLeads: number;
  activeDeals: number;
  pipelineValue: number;
  conversionRate: number;
  overdueTasks?: number;
  dueTodayTasks?: number;
  dueSoonTasks?: number;
  dueTasks?: DueTask[];
}

export function useDashboardMetrics(timeRange: string = "30d") {
  return useQuery({
    queryKey: ["dashboard", "metrics", timeRange],
    queryFn: async () => {
      return apiFetch(`/api/v1/dashboard/metrics?timeRange=${timeRange}`) as Promise<DashboardMetrics>;
    },
    refetchInterval: 60_000,
  });
}
