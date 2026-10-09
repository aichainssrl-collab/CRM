"use client";

import { useState, useCallback, useEffect } from "react";
import { getAuthToken } from "@/lib/auth";
import apiClient from "@/lib/api";

// ── Conversations hook ─────────────────────────────────────────────────────────

export interface ConversationMeta {
  _id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount?: number;
}

export interface Conversation extends ConversationMeta {
  messages: { role: string; content: string }[];
}

export function useConversations() {
  const [conversations, setConversations] = useState<ConversationMeta[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchConversations = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get("/api/v1/marketing/conversations");
      setConversations(data.conversations ?? []);
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const saveConversation = useCallback(async (title: string, messages: { role: string; content: string }[]) => {
    try {
      const { data } = await apiClient.post("/api/v1/marketing/conversations", { title, messages });
      await fetchConversations();
      return data.id;
    } catch (err) {
      console.error("Failed to save conversation:", err);
      return null;
    }
  }, [fetchConversations]);

  const loadConversation = useCallback(async (id: string): Promise<Conversation | null> => {
    try {
      const { data } = await apiClient.get(`/api/v1/marketing/conversations/${id}`);
      return data;
    } catch (err) {
      console.error("Failed to load conversation:", err);
      return null;
    }
  }, []);

  const deleteConversation = useCallback(async (id: string) => {
    try {
      await apiClient.delete(`/api/v1/marketing/conversations/${id}`);
      await fetchConversations();
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  }, [fetchConversations]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return { conversations, loading, fetchConversations, saveConversation, loadConversation, deleteConversation };
}


// ── Insights hook ──────────────────────────────────────────────────────────────

export interface CRMInsights {
  summary: {
    totalLeads: number;
    totalDeals: number;
    totalDealValue: number;
    leadGrowth: Record<string, number>;
  };
  leadsBySource: { source: string; count: number }[];
  leadsByStatus: { status: string; count: number }[];
  dealsByStage: { stage: string; count: number; totalValue: number }[];
  topTags: { tag: string; count: number }[];
}

export function useInsights() {
  const [insights, setInsights] = useState<CRMInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchInsights = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get("/api/v1/marketing/insights");
      setInsights(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Errore caricamento insights";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  return { insights, loading, error, refetch: fetchInsights };
}


// ── Smart suggestions hook ─────────────────────────────────────────────────────

export function useSuggestions() {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchSuggestions = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get("/api/v1/marketing/suggestions");
      setSuggestions(data.suggestions ?? []);
    } catch (err) {
      console.error("Failed to fetch suggestions:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  return { suggestions, loading, refetch: fetchSuggestions };
}