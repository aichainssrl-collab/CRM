import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface ApolloProspect {
  apolloId: string;
  firstName: string;
  lastName: string;
  email: string;
  emailStatus?: string | null;
  title: string;
  linkedinUrl: string;
  phone: string;
  city: string;
  country: string;
  companyName: string;
  companyDomain: string;
  industry: string;
  numEmployeesRange: string;
  seniority: string;
  apolloScore: number | null;
}

export interface ApolloSearchFilters {
  q?: string;
  title?: string;
  industry?: string;
  location?: string;
  seniority?: string;
}

export interface ApolloSearchResult {
  people: ApolloProspect[];
  total: number;
  page: number;
  perPage: number;
  mode: "mock" | "live";
}

export interface ApolloImportResult {
  imported: Array<Record<string, unknown>>;
  importedCount: number;
  skipped: Array<{ email: string; reason: string; leadId?: string }>;
  skippedCount: number;
  errors: string[];
}

export function useApolloSearch(
  filters: ApolloSearchFilters,
  page = 1,
  enabled = false
) {
  return useQuery({
    queryKey: ["apollo", "search", filters, page],
    enabled,
    queryFn: async () =>
      apiFetch("/api/v1/apollo/search", {
        method: "POST",
        body: JSON.stringify({ filters, page, perPage: 25 }),
      }) as Promise<ApolloSearchResult>,
  });
}

export function useApolloImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (prospects: ApolloProspect[]) =>
      apiFetch("/api/v1/apollo/import", {
        method: "POST",
        body: JSON.stringify({ prospects }),
      }) as Promise<ApolloImportResult>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
    },
  });
}

export function useApolloEnrich() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leadId: string) =>
      apiFetch(`/api/v1/apollo/enrich/${leadId}`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["lead"] });
    },
  });
}

export interface ApolloBulkEnrichResult {
  results: Array<{
    leadId: string;
    status: "enriched" | "missed" | "skipped_fresh" | "not_found" | "error";
    error?: string;
  }>;
  enrichedCount: number;
  missedCount: number;
  skippedCount: number;
  errorCount: number;
  processedCount: number;
}

export function useApolloBulkEnrich() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { leadIds: string[]; onlyStale?: boolean }) =>
      apiFetch("/api/v1/apollo/bulk-enrich", {
        method: "POST",
        body: JSON.stringify({
          leadIds: payload.leadIds,
          onlyStale: payload.onlyStale ?? true,
        }),
      }) as Promise<ApolloBulkEnrichResult>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["lead"] });
    },
  });
}

export function useApolloUsage() {
  return useQuery({
    queryKey: ["apollo", "usage"],
    queryFn: () =>
      apiFetch("/api/v1/apollo/usage") as Promise<{
        mode: "mock" | "live";
        provider: string;
        hasApiKey: boolean;
      }>,
  });
}
