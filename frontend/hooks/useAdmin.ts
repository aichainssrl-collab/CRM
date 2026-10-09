import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface AuditEntry {
  id: string;
  userId: string;
  userName: string;
  action: string;
  entityType: string;
  entityId: string;
  description: string;
  changes: Record<string, unknown>;
  createdAt: string;
}

export interface AuditStats {
  total: number;
  byAction: Record<string, number>;
  byEntity: Record<string, number>;
  topUsers: { userId: string; count: number }[];
}

export interface SystemStats {
  entities: {
    leads: { total: number; last7d: number; last30d: number };
    deals: { total: number; won: number; active: number };
    tasks: { total: number; open: number };
    users: { total: number; active: number };
    bookings: { total: number };
    emailSequences: { total: number; active: number };
    reports: { total: number };
    formSubmissions: { total: number };
    gdprConsents: { total: number };
  };
  emails: { sent: number; last30d: number };
  database: { collections: number; totalDocuments: number };
}

export interface SavedFilter {
  id: string;
  userId: string;
  name: string;
  entityType: string;
  filters: Record<string, string>;
  isGlobal: boolean;
  createdAt: string;
}

// ── Audit Log ─────────────────────────────────────────────────
export function useAuditLog(filters?: {
  user_id?: string;
  entity_type?: string;
  action?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["audit-log", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([k, v]) => {
          if (v !== undefined) params.append(k, String(v));
        });
      }
      const qs = params.toString();
      return apiFetch(`/api/v1/admin/audit-log${qs ? `?${qs}` : ""}`) as Promise<AuditEntry[]>;
    },
  });
}

export function useAuditStats(days: number = 30) {
  return useQuery({
    queryKey: ["audit-stats", days],
    queryFn: async () => {
      return apiFetch(`/api/v1/admin/audit-log/stats?days=${days}`) as Promise<AuditStats>;
    },
  });
}

// ── System Stats ──────────────────────────────────────────────
export function useSystemStats() {
  return useQuery({
    queryKey: ["system-stats"],
    queryFn: async () => {
      return apiFetch("/api/v1/admin/system-stats") as Promise<SystemStats>;
    },
  });
}

// ── Saved Filters ─────────────────────────────────────────────
export function useSavedFilters(entityType?: string) {
  return useQuery({
    queryKey: ["saved-filters", entityType],
    queryFn: async () => {
      const qs = entityType ? `?entity_type=${entityType}` : "";
      return apiFetch(`/api/v1/admin/saved-filters${qs}`) as Promise<SavedFilter[]>;
    },
  });
}

export function useCreateSavedFilter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string; entityType: string; filters?: Record<string, string>; isGlobal?: boolean }) => {
      return apiFetch("/api/v1/admin/saved-filters", { method: "POST", body: JSON.stringify(data) });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved-filters"] }),
  });
}

export function useDeleteSavedFilter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return apiFetch(`/api/v1/admin/saved-filters/${id}`, { method: "DELETE" });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["saved-filters"] }),
  });
}