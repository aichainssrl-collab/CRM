"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Loader2, Sparkles, Plus, Power, Trash2, X } from "lucide-react";

export interface AgentSkill {
  id: string;
  name: string;
  title: string;
  description?: string;
  category?: string;
  triggers?: string[];
  body?: string;
  isActive?: boolean;
  isDefault?: boolean;
}

export function AgentSkillsManager() {
  const t = useTranslations("settings.agentSkills");
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState({
    title: "",
    description: "",
    category: "custom",
    triggers: "",
    body: "",
  });

  const { data, isLoading } = useQuery({
    queryKey: ["agent-skills"],
    queryFn: () => apiFetch("/api/v1/agent/skills") as Promise<{ skills: AgentSkill[] }>,
  });

  const invalidate = () => void qc.invalidateQueries({ queryKey: ["agent-skills"] });

  const create = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiFetch("/api/v1/agent/skills", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      invalidate();
      setOpen(false);
      setDraft({ title: "", description: "", category: "custom", triggers: "", body: "" });
      toast.success(t("created"));
    },
    onError: () => toast.error(t("saveError")),
  });

  const toggle = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/agent/skills/${id}/toggle`, { method: "POST" }),
    onSuccess: invalidate,
  });

  const remove = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/agent/skills/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      invalidate();
      toast.success(t("deleted"));
    },
    onError: () => toast.error(t("saveError")),
  });

  const skills = data?.skills ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          {t("title")}
        </CardTitle>
        <CardDescription>{t("subtitle")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            {t("loading")}
          </div>
        )}

        <div className="space-y-3">
          {skills.map((s) => (
            <div key={s.id} className="rounded-md border p-3 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm">{s.title}</p>
                    <Badge variant="secondary" className="text-[9px]">{s.category}</Badge>
                    {s.isDefault && <Badge variant="outline" className="text-[9px]">{t("default")}</Badge>}
                    {!s.isActive && <Badge variant="destructive" className="text-[9px]">{t("inactive")}</Badge>}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{s.description}</p>
                </div>
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 w-7 p-0"
                    title={t("toggle")}
                    onClick={() => toggle.mutate(s.id)}
                  >
                    <Power className={`h-3.5 w-3.5 ${s.isActive ? "text-success" : "text-muted-foreground"}`} />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 w-7 p-0"
                    title={t("delete")}
                    onClick={() => remove.mutate(s.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </Button>
                </div>
              </div>
              {!!s.triggers?.length && (
                <div className="flex flex-wrap gap-1">
                  {s.triggers.map((tr) => (
                    <Badge key={tr} variant="outline" className="text-[9px]">{tr}</Badge>
                  ))}
                </div>
              )}
              <pre className="text-xs whitespace-pre-wrap text-muted-foreground max-h-24 overflow-auto">
                {s.body}
              </pre>
            </div>
          ))}
        </div>

        {!open ? (
          <Button type="button" variant="outline" className="gap-2" onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4" />
            {t("add")}
          </Button>
        ) : (
          <div className="space-y-3 rounded-md border p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">{t("newSkill")}</p>
              <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => setOpen(false)}>
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
            <div className="space-y-2">
              <Label>{t("titleField")}</Label>
              <Input
                value={draft.title}
                onChange={(e) => setDraft((p) => ({ ...p, title: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>{t("description")}</Label>
              <Input
                value={draft.description}
                onChange={(e) => setDraft((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>{t("triggers")}</Label>
              <Input
                value={draft.triggers}
                onChange={(e) => setDraft((p) => ({ ...p, triggers: e.target.value }))}
                placeholder={t("triggersHint")}
              />
            </div>
            <div className="space-y-2">
              <Label>{t("body")}</Label>
              <Textarea
                rows={5}
                value={draft.body}
                onChange={(e) => setDraft((p) => ({ ...p, body: e.target.value }))}
              />
            </div>
            <Button
              onClick={() =>
                create.mutate({
                  title: draft.title,
                  description: draft.description,
                  category: draft.category,
                  triggers: draft.triggers.split(",").map((s) => s.trim()).filter(Boolean),
                  body: draft.body,
                  name: draft.title.toLowerCase().replace(/\s+/g, "-").slice(0, 40) || undefined,
                })
              }
              disabled={create.isPending || !draft.title.trim()}
            >
              {create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              {t("save")}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
