import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface Lead {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  companyName?: string;
  phone?: string;
  pipelineStage: string;
  leadScore: number;
  assignedTo?: string;
  createdAt: string;
  // Campi CRM completi
  linkedinUrl?: string;
  website?: string;
  industry?: string;
  companySize?: string;
  numEmployeesRange?: string;
  roleTitle?: string;
  roleSeniority?: string;
  source?: string;
  status?: string;
  tags?: string[];
  notes?: string;
  // Enrichment
  enrichedAt?: string;
  enrichmentSource?: string;
  // campi annidati da MongoDB
  customFields?: Record<string, unknown>;
}

export function useLeads(filters?: Record<string, any>) {
  return useQuery({
    queryKey: ["leads", filters],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            searchParams.append(key, value.toString());
          }
        });
      }
      searchParams.set("limit", "100");
      const qs = searchParams.toString();
      const endpoint = `/api/v1/leads?${qs}`;
      return apiFetch(endpoint) as Promise<Lead[]>;
    },
  });
}

export function useLead(id: string) {
  return useQuery({
    queryKey: ["leads", id],
    queryFn: async () => {
      return apiFetch(`/api/v1/leads/${id}`) as Promise<Lead>;
    },
    enabled: !!id,
  });
}

export function useCreateLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Lead>) => {
      return apiFetch("/api/v1/leads", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
    },
  });
}

export function useUpdateLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Lead> }) => {
      return apiFetch(`/api/v1/leads/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["leads", variables.id] });
    },
  });
}

export function useDeleteLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return apiFetch(`/api/v1/leads/${id}`, {
        method: "DELETE",
      });
    },
    onSuccess: (_data, id) => {
      queryClient.setQueriesData<Lead[]>({ queryKey: ["leads"] }, (old) =>
        old ? old.filter((l) => l.id !== id) : old
      );
    },
  });
}
