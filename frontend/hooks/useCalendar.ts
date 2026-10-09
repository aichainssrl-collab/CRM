import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface CalendarEvent {
  id: string;
  type: "task" | "booking" | "deal";
  title: string;
  date: string | null;
  status: string;
  assignedTo?: string;
  timeSlot?: string;
  value?: number;
}

export interface LeaderboardUser {
  userId: string;
  userName: string;
  dealsWon: number;
  revenue: number;
  tasksCompleted: number;
  leadsAssigned: number;
  score: number;
}

// ── Calendar ──────────────────────────────────────────────────
export function useCalendarEvents(year: number, month: number) {
  return useQuery({
    queryKey: ["calendar", year, month],
    queryFn: async () => {
      return apiFetch(`/api/v1/calendar/events?year=${year}&month=${month}`) as Promise<CalendarEvent[]>;
    },
  });
}

export function useUpcomingEvents(days: number = 7) {
  return useQuery({
    queryKey: ["calendar", "upcoming", days],
    queryFn: async () => {
      return apiFetch(`/api/v1/calendar/upcoming?days=${days}`) as Promise<CalendarEvent[]>;
    },
  });
}

// ── Bulk Operations ───────────────────────────────────────────
export function useBulkAssign() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ leadIds, assignedTo }: { leadIds: string[]; assignedTo: string }) => {
      return apiFetch("/api/v1/calendar/bulk/assign", {
        method: "POST",
        body: JSON.stringify({ leadIds, assignedTo }),
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

export function useBulkStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ leadIds, status }: { leadIds: string[]; status: string }) => {
      return apiFetch("/api/v1/calendar/bulk/status", {
        method: "POST",
        body: JSON.stringify({ leadIds, status }),
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

export function useBulkDelete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (leadIds: string[]) => {
      return apiFetch("/api/v1/calendar/bulk/delete", {
        method: "POST",
        body: JSON.stringify({ leadIds, assignedTo: "" }),
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });
}

// ── Team Leaderboard ──────────────────────────────────────────
export function useLeaderboard(days: number = 30) {
  return useQuery({
    queryKey: ["leaderboard", days],
    queryFn: async () => {
      return apiFetch(`/api/v1/calendar/leaderboard?days=${days}`) as Promise<LeaderboardUser[]>;
    },
  });
}