import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface Product {
  id: string;
  name: string;
  description: string;
  sku: string;
  category: string;
  price: number;
  currency: string;
  billingModel: string;
  isActive: boolean;
  createdAt: string;
}

export interface Segment {
  id: string;
  userId: string;
  name: string;
  description: string;
  rules: Record<string, unknown>;
  entityType: string;
  isGlobal: boolean;
  matchCount: number;
  createdAt: string;
}

export interface TagAnalytics {
  tag: string;
  count: number;
  avgScore: number;
}

export interface IndustrySegment {
  industry: string;
  total: number;
  avgScore: number;
  statusBreakdown: Record<string, number>;
}

export interface SourcePerformance {
  source: string;
  total: number;
  converted: number;
  conversionRate: number;
}

// ── Products ──────────────────────────────────────────────────
export function useProducts() {
  return useQuery({
    queryKey: ["products"],
    queryFn: async () => apiFetch("/api/v1/products/") as Promise<Product[]>,
  });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Product>) =>
      apiFetch("/api/v1/products/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}

export function useUpdateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Product> }) =>
      apiFetch(`/api/v1/products/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}

export function useDeleteProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      apiFetch(`/api/v1/products/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}

// ── Segments ──────────────────────────────────────────────────
export function useSegments() {
  return useQuery({
    queryKey: ["segments"],
    queryFn: async () => apiFetch("/api/v1/segments/") as Promise<Segment[]>,
  });
}

export function useCreateSegment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string; description?: string; rules?: Record<string, unknown>; isGlobal?: boolean }) =>
      apiFetch("/api/v1/segments/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["segments"] }),
  });
}

export function useDeleteSegment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) =>
      apiFetch(`/api/v1/segments/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["segments"] }),
  });
}

// ── Analytics ─────────────────────────────────────────────────
export function useTagAnalytics() {
  return useQuery({
    queryKey: ["tag-analytics"],
    queryFn: async () => apiFetch("/api/v1/segments/analytics/tags") as Promise<TagAnalytics[]>,
  });
}

export function useIndustrySegments() {
  return useQuery({
    queryKey: ["industry-segments"],
    queryFn: async () => apiFetch("/api/v1/segments/analytics/industries") as Promise<IndustrySegment[]>,
  });
}

export function useSourcePerformance() {
  return useQuery({
    queryKey: ["source-performance"],
    queryFn: async () => apiFetch("/api/v1/segments/analytics/sources") as Promise<SourcePerformance[]>,
  });
}