import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface Notification {
  id: string;
  userId: string;
  title: string;
  body: string;
  kind: "info" | "warning" | "success" | "error";
  link?: string | null;
  readAt: string | null;
  createdAt: string;
}

export interface ActivityItem {
  id: string;
  userId: string;
  userName: string;
  action: string;
  entityType: string;
  entityId: string;
  description: string;
  metadata: Record<string, unknown>;
  createdAt: string;
}

export interface SearchResult {
  leads: { id: string; title: string; subtitle: string; status: string }[];
  deals: { id: string; title: string; subtitle: string; status: string }[];
  tasks: { id: string; title: string; subtitle: string; status: string }[];
}

// ── Notifications ─────────────────────────────────────────────
export function useNotifications(unreadOnly: boolean = false) {
  return useQuery({
    queryKey: ["notifications", unreadOnly],
    queryFn: async () => {
      return apiFetch(`/api/v1/notifications/?unread_only=${unreadOnly}`) as Promise<Notification[]>;
    },
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: async () => {
      const data = await apiFetch("/api/v1/notifications/unread-count");
      return data.count as number;
    },
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (notificationId: string) => {
      return apiFetch("/api/v1/notifications/mark-read", {
        method: "POST",
        body: JSON.stringify({ notificationId }),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return apiFetch("/api/v1/notifications/mark-all-read", { method: "POST" });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

// ── Activity Feed ─────────────────────────────────────────────
export function useActivityFeed(limit: number = 50) {
  return useQuery({
    queryKey: ["activity-feed", limit],
    queryFn: async () => {
      return apiFetch(`/api/v1/notifications/activity-feed?limit=${limit}`) as Promise<ActivityItem[]>;
    },
  });
}

// ── Global Search ─────────────────────────────────────────────
export function useGlobalSearch(query: string) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: async () => {
      return apiFetch(`/api/v1/notifications/search?q=${encodeURIComponent(query)}`) as Promise<SearchResult>;
    },
    enabled: query.length >= 2,
  });
}