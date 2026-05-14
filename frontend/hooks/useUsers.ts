import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface CRMUser {
  uid: string;
  email: string;
  displayName?: string;
  role: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CurrentUser {
  uid: string;
  email?: string;
  displayName?: string;
  role: string;
}

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      return apiFetch("/api/v1/users") as Promise<CRMUser[]>;
    },
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ["users", "me"],
    queryFn: async () => {
      return apiFetch("/api/v1/users/me") as Promise<CurrentUser>;
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      uid,
      data,
    }: {
      uid: string;
      data: { displayName?: string; role?: string; isActive?: boolean };
    }) => {
      return apiFetch(`/api/v1/users/${uid}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      uid: string;
      email: string;
      displayName?: string;
      role: string;
    }) => {
      return apiFetch("/api/v1/users", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}
