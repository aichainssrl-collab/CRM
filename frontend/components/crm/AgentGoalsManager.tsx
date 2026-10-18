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
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Loader2, Target, Plus, Check, RotateCcw, Trash2, X } from "lucide-react";

export interface AgentGoal {
  id: string;
  key?: string;
  title: string;
  description?: string;
  metric?: string;
  target?: number;
  progress?: number;
  percent?: number;
  status?: "pending" | "in_progress" | "completed" | "cancelled";
  isDefault?: boolean;
}

export function AgentGoalsManager() {
  const t = useTranslations("settings.agentGoals");
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState({ title: "", description: "", target: 10, metric: "actions_ok" });

  const { data, isLoading } = useQuery({
    queryKey: ["agent-goals"],
    queryFn: () => apiFetch("/api/v1/agent/goals") as Promise<{ goals: AgentGoal[] }>,
  });

  const invalidate = () => void qc.invalidateQueries({ queryKey: ["agent-goals"] });

  const create = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiFetch("/api/v1/agent/goals", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      invalidate();
      setOpen(false);
      setDraft({ title: "", description: "", target: 10, metric: "actions_ok" });
      toast.success(t("created"));
    },
  });

  const complete = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/agent/goals/${id}/complete`, { method: "POST" }),
    onSuccess: () => {
      invalidate();
      toast.success(t("completed"));
    },
  });

  const reset = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/agent/goals/${id}/reset`, { method: "POST" }),
    onSuccess: invalidate,
  });

  const remove = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/agent/goals/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      invalidate();
      toast.success(t("deleted"));
    },
  });

  const goals = data?.goals ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
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

        {goals.map((g) => (
          <div key={g.id} className="rounded-md border p-3 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{g.title}</p>
                  <Badge
                    variant={
                      g.status === "completed"
                        ? "default"
                        : g.status === "in_progress"
                          ? "secondary"
                          : "outline"
                    }
                    className="text-[9px]"
                  >
                    {t(`status.${g.status ?? "pending"}`)}
                  </Badge>
                  {g.isDefault && <Badge variant="outline" className="text-[9px]">{t("default")}</Badge>}
                </div>
                {g.description && (
                  <p className="text-xs text-muted-foreground mt-1">{g.description}</p>
                )}
              </div>
              <div className="flex gap-1">
                {g.status !== "completed" && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 w-7 p-0"
                    title={t("markComplete")}
                    onClick={() => complete.mutate(g.id)}
                  >
                    <Check className="h-3.5 w-3.5 text-success" />
                  </Button>
                )}
                {g.status === "completed" && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 w-7 p-0"
                    title={t("reset")}
                    onClick={() => reset.mutate(g.id)}
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 w-7 p-0"
                  title={t("delete")}
                  onClick={() => remove.mutate(g.id)}
                >
                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                </Button>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{g.metric}</span>
                <span>
                  {g.progress ?? 0}/{g.target ?? 1} ({g.percent ?? 0}%)
                </span>
              </div>
              <Progress value={g.percent ?? 0} className="h-2" />
            </div>
          </div>
        ))}

        {!open ? (
          <Button type="button" variant="outline" className="gap-2" onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4" />
            {t("add")}
          </Button>
        ) : (
          <div className="space-y-3 rounded-md border p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">{t("newGoal")}</p>
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
              <Textarea
                rows={2}
                value={draft.description}
                onChange={(e) => setDraft((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>{t("target")}</Label>
                <Input
                  type="number"
                  min={1}
                  value={draft.target}
                  onChange={(e) => setDraft((p) => ({ ...p, target: Number(e.target.value) || 1 }))}
                />
              </div>
              <div className="space-y-2">
                <Label>{t("metric")}</Label>
                <Input
                  value={draft.metric}
                  onChange={(e) => setDraft((p) => ({ ...p, metric: e.target.value }))}
                />
              </div>
            </div>
            <Button
              onClick={() =>
                create.mutate({
                  title: draft.title,
                  description: draft.description,
                  target: draft.target,
                  metric: draft.metric,
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
