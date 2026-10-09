import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface WaConversation {
  id: string;
  phone: string;
  leadId?: string | null;
  leadName?: string;
  status: "open" | "closed";
  lastMessageAt?: string | null;
  lastInboundAt?: string | null;
  lastOutboundAt?: string | null;
  unreadCount: number;
  assignedTo?: string;
  createdAt: string;
}

export interface WaMessage {
  id: string;
  conversationId: string;
  direction: "inbound" | "outbound";
  body: string;
  status: string;
  waMessageId?: string;
  sentBy?: string;
  createdAt: string;
}

export interface InboxStats {
  totalConversations: number;
  openConversations: number;
  unreadMessages: number;
}

export function useConversations(status?: string) {
  return useQuery({
    queryKey: ["whatsapp", "conversations", status ?? "all"],
    queryFn: async () =>
      apiFetch(
        `/api/v1/whatsapp/conversations${status ? `?status=${status}` : ""}`
      ) as Promise<WaConversation[]>,
  });
}

export function useConversation(id: string | null) {
  return useQuery({
    queryKey: ["whatsapp", "conversation", id],
    enabled: !!id,
    queryFn: async () =>
      apiFetch(`/api/v1/whatsapp/conversations/${id}`) as Promise<WaConversation>,
  });
}

export function useMessages(conversationId: string | null) {
  return useQuery({
    queryKey: ["whatsapp", "messages", conversationId],
    enabled: !!conversationId,
    queryFn: async () =>
      apiFetch(
        `/api/v1/whatsapp/conversations/${conversationId}/messages`
      ) as Promise<WaMessage[]>,
  });
}

export function useInboxStats() {
  return useQuery({
    queryKey: ["whatsapp", "stats"],
    queryFn: async () => apiFetch("/api/v1/whatsapp/stats") as Promise<InboxStats>,
  });
}

export function useCreateConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { phone: string; leadId?: string; leadName?: string }) =>
      apiFetch("/api/v1/whatsapp/conversations", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["whatsapp"] });
    },
  });
}

export function useSendMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ conversationId, body }: { conversationId: string; body: string }) =>
      apiFetch(`/api/v1/whatsapp/conversations/${conversationId}/messages`, {
        method: "POST",
        body: JSON.stringify({ body }),
      }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["whatsapp", "messages", vars.conversationId] });
      qc.invalidateQueries({ queryKey: ["whatsapp", "conversations"] });
      qc.invalidateQueries({ queryKey: ["whatsapp", "stats"] });
    },
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (conversationId: string) =>
      apiFetch(`/api/v1/whatsapp/conversations/${conversationId}/read`, {
        method: "POST",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["whatsapp"] });
    },
  });
}

export function useCloseConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (conversationId: string) =>
      apiFetch(`/api/v1/whatsapp/conversations/${conversationId}/close`, {
        method: "POST",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["whatsapp"] });
    },
  });
}

export function useReopenConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (conversationId: string) =>
      apiFetch(`/api/v1/whatsapp/conversations/${conversationId}/reopen`, {
        method: "POST",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["whatsapp"] });
    },
  });
}
