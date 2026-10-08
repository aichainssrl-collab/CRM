import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export type DatePreset = "7d" | "30d" | "90d";

export interface MetaStatus {
  configured: boolean;
  account_id: string | null;
  account_name: string | null;
  currency?: string;
  account_status?: number;
  error?: string;
}

export interface MetaSummary {
  spend: number;
  impressions: number;
  clicks: number;
  ctr: number;
  cpc: number;
  cpm: number;
  reach: number;
  conversions: number;
  link_clicks: number;
  date_preset: string;
}

export interface MetaCampaign {
  id: string;
  name: string;
  status: string;
  objective: string;
  spend: number;
  impressions: number;
  clicks: number;
  ctr: number;
  cpc: number;
  cpm: number;
  reach: number;
  conversions: number;
  link_clicks: number;
  date_start?: string;
  date_stop?: string;
}

export interface MetaCampaignsResponse {
  campaigns: MetaCampaign[];
  total: number;
  date_preset: string;
}

export interface MetaTrendPoint {
  date: string;
  spend: number;
  clicks: number;
  impressions: number;
  reach: number;
}

export interface MetaTrendResponse {
  trend: MetaTrendPoint[];
  date_preset: string;
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

export function useMetaStatus() {
  return useQuery<MetaStatus>({
    queryKey: ["meta", "status"],
    queryFn: () => apiFetch("/api/v1/meta/status"),
    staleTime: 5 * 60 * 1000, // 5 minuti
    retry: false,
  });
}

export function useMetaSummary(datePreset: DatePreset = "30d") {
  return useQuery<MetaSummary>({
    queryKey: ["meta", "summary", datePreset],
    queryFn: () => apiFetch(`/api/v1/meta/summary?date_preset=${datePreset}`),
    staleTime: 15 * 60 * 1000, // 15 minuti (allineato alla cache backend)
    retry: 1,
  });
}

export function useMetaCampaigns(datePreset: DatePreset = "30d") {
  return useQuery<MetaCampaignsResponse>({
    queryKey: ["meta", "campaigns", datePreset],
    queryFn: () => apiFetch(`/api/v1/meta/campaigns?date_preset=${datePreset}&status=ACTIVE,PAUSED`),
    staleTime: 15 * 60 * 1000,
    retry: 1,
  });
}

export function useMetaTrend(datePreset: DatePreset = "30d") {
  return useQuery<MetaTrendResponse>({
    queryKey: ["meta", "trend", datePreset],
    queryFn: () => apiFetch(`/api/v1/meta/trend?date_preset=${datePreset}`),
    staleTime: 15 * 60 * 1000,
    retry: 1,
  });
}
