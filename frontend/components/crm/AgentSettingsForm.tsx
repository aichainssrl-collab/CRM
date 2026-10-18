"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Loader2, Bot, Target, Heart, Scale, Eye } from "lucide-react";

export interface AgentConfig {
  agentName: string;
  role: string;
  company: string;
  goal: string;
  soul: string;
  tone: string;
  language: string;
  rules: string;
  fallbackBehavior: string;
  toolsPolicy: string;
  source?: string;
  updatedAt?: string;
}

export function AgentSettingsForm() {
  const t = useTranslations("settings.agent");
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["agent-config"],
    queryFn: () => apiFetch("/api/v1/agent/config") as Promise<AgentConfig>,
  });
  const [form, setForm] = useState<AgentConfig | null>(null);
  const [preview, setPreview] = useState("");
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  const save = useMutation({
    mutationFn: (payload: Partial<AgentConfig>) =>
      apiFetch("/api/v1/agent/config", {
        method: "PUT",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["agent-config"] });
      toast.success(t("saved"));
    },
    onError: (err) => {
      toast.error(t("saveError"), {
        description: err instanceof Error ? err.message : String(err),
      });
    },
  });

  async function loadPreview() {
    try {
      const res = (await apiFetch("/api/v1/agent/config/preview")) as { instructions: string };
      setPreview(res.instructions || "");
      setShowPreview(true);
    } catch {
      toast.error(t("previewError"));
    }
  }

  if (isLoading || !form) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        {t("loading")}
      </div>
    );
  }

  const set = (key: keyof AgentConfig) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((p) => (p ? { ...p, [key]: e.target.value } : p));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          {t("title")}
        </CardTitle>
        <CardDescription>{t("subtitle")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="agentName">{t("agentName")}</Label>
            <Input id="agentName" value={form.agentName} onChange={set("agentName")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company">{t("company")}</Label>
            <Input id="company" value={form.company} onChange={set("company")} />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="role" className="flex items-center gap-1.5">
            <Bot className="h-3.5 w-3.5" />
            {t("role")}
          </Label>
          <Textarea id="role" rows={3} value={form.role} onChange={set("role")} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="goal" className="flex items-center gap-1.5">
            <Target className="h-3.5 w-3.5" />
            {t("goal")}
          </Label>
          <Textarea id="goal" rows={5} value={form.goal} onChange={set("goal")} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="soul" className="flex items-center gap-1.5">
            <Heart className="h-3.5 w-3.5" />
            {t("soul")}
          </Label>
          <Textarea id="soul" rows={4} value={form.soul} onChange={set("soul")} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="tone">{t("tone")}</Label>
            <Input id="tone" value={form.tone} onChange={set("tone")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="language">{t("language")}</Label>
            <Input id="language" value={form.language} onChange={set("language")} />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="rules" className="flex items-center gap-1.5">
            <Scale className="h-3.5 w-3.5" />
            {t("rules")}
          </Label>
          <Textarea id="rules" rows={6} value={form.rules} onChange={set("rules")} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="fallbackBehavior">{t("fallback")}</Label>
          <Textarea id="fallbackBehavior" rows={3} value={form.fallbackBehavior} onChange={set("fallbackBehavior")} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="toolsPolicy">{t("toolsPolicy")}</Label>
          <Textarea id="toolsPolicy" rows={2} value={form.toolsPolicy} onChange={set("toolsPolicy")} />
        </div>

        {showPreview && (
          <pre className="max-h-64 overflow-auto rounded-md border bg-muted/30 p-3 text-xs whitespace-pre-wrap">
            {preview}
          </pre>
        )}

        <div className="flex flex-wrap gap-2">
          <Button onClick={() => save.mutate(form)} disabled={save.isPending}>
            {save.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {t("save")}
          </Button>
          <Button type="button" variant="outline" onClick={() => void loadPreview()}>
            <Eye className="h-4 w-4 mr-1" />
            {t("preview")}
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              // ripristina i default dal server (reset campi vuoti → default)
              save.mutate({
                agentName: "",
                role: "",
                company: "",
                goal: "",
                soul: "",
                tone: "",
                language: "",
                rules: "",
                fallbackBehavior: "",
                toolsPolicy: "",
              });
            }}
          >
            {t("resetDefaults")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
