"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  useWorkflows, useWorkflowStats, useCreateWorkflow, useUpdateWorkflow,
  useDeleteWorkflow, useToggleWorkflow,
  type Workflow, type WorkflowAction, type WorkflowCondition, type WorkflowTrigger,
} from "@/hooks/useWorkflows";
import {
  Zap, Plus, Trash2, MoreHorizontal, Play, Pause, Edit,
  Loader2, GitBranch,
} from "lucide-react";

const TRIGGERS: WorkflowTrigger[] = [
  "lead_created",
  "deal_stage_changed",
  "proposal_accepted",
  "task_completed",
  "manual",
];

const ACTION_TYPES = [
  "create_task",
  "add_tag",
  "update_lead_status",
  "send_notification",
  "send_email",
] as const;

const CONDITION_OPS = ["eq", "ne", "contains", "gte", "lte", "in"] as const;

function emptyCondition(): WorkflowCondition {
  return { field: "status", op: "eq", value: "" };
}

function emptyAction(): WorkflowAction {
  return { type: "create_task", title: "" };
}

export default function WorkflowsPage() {
  const t = useTranslations("workflows");
  const tSidebar = useTranslations("sidebar");
  const { data: workflows, isLoading } = useWorkflows();
  const { data: stats } = useWorkflowStats();
  const createWorkflow = useCreateWorkflow();
  const updateWorkflow = useUpdateWorkflow();
  const deleteWorkflow = useDeleteWorkflow();
  const toggleWorkflow = useToggleWorkflow();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [trigger, setTrigger] = useState<WorkflowTrigger>("lead_created");
  const [conditions, setConditions] = useState<WorkflowCondition[]>([emptyCondition()]);
  const [actions, setActions] = useState<WorkflowAction[]>([emptyAction()]);
  const [saving, setSaving] = useState(false);

  function resetForm() {
    setEditingId(null);
    setName("");
    setDescription("");
    setTrigger("lead_created");
    setConditions([emptyCondition()]);
    setActions([emptyAction()]);
  }

  function openCreate() {
    resetForm();
    setDialogOpen(true);
  }

  function openEdit(wf: Workflow) {
    setEditingId(wf.id);
    setName(wf.name);
    setDescription(wf.description || "");
    setTrigger(wf.trigger as WorkflowTrigger);
    setConditions(wf.conditions?.length ? wf.conditions.map((c) => ({ ...c })) : [emptyCondition()]);
    setActions(wf.actions?.length ? wf.actions.map((a) => ({ ...a })) : [emptyAction()]);
    setDialogOpen(true);
  }

  async function handleSave() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const payload = {
        name,
        description,
        trigger,
        conditions: conditions.filter((c) => c.field),
        actions: actions.filter((a) => a.type),
      };
      if (editingId) {
        await updateWorkflow.mutateAsync({ id: editingId, data: payload });
      } else {
        await createWorkflow.mutateAsync(payload);
      }
      setDialogOpen(false);
      resetForm();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm(t("confirmDelete"))) return;
    await deleteWorkflow.mutateAsync(id);
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{tSidebar("workflows")}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t("subtitle")}</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          {t("new")}
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("total")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.total ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("active")}</CardDescription>
            <CardTitle className="text-2xl text-primary">{stats?.active ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("topRun")}</CardDescription>
            <CardTitle className="text-lg truncate">
              {stats?.topRuns?.[0]
                ? `${stats.topRuns[0].name} (${stats.topRuns[0].runCount})`
                : "—"}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-primary" />
            {t("listTitle")}
          </CardTitle>
          <CardDescription>{t("listDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : !workflows?.length ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Zap className="h-10 w-10 text-muted-foreground/40 mb-3" />
              <p className="text-sm text-muted-foreground">{t("empty")}</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={openCreate}>
                <Plus className="mr-2 h-4 w-4" />
                {t("new")}
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {workflows.map((wf) => (
                <div
                  key={wf.id}
                  className="flex flex-col gap-2 rounded-lg border border-border/60 p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant={wf.isActive ? "default" : "outline"}>
                        {wf.isActive ? t("on") : t("off")}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{t(`triggers.${wf.trigger}`)}</span>
                    </div>
                    <p className="font-medium truncate">{wf.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {wf.conditions?.length || 0} {t("conditions")} · {wf.actions?.length || 0} {t("actions")} · {wf.runCount} {t("runs")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleWorkflow.mutate(wf.id)}
                    >
                      {wf.isActive ? (
                        <>
                          <Pause className="mr-1 h-3 w-3" />
                          {t("disable")}
                        </>
                      ) : (
                        <>
                          <Play className="mr-1 h-3 w-3" />
                          {t("enable")}
                        </>
                      )}
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={
                          <Button variant="ghost" size="icon" aria-label={t("actions")}>
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        }
                      />
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openEdit(wf)}>
                          <Edit className="mr-2 h-4 w-4" />
                          {t("edit")}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem variant="destructive" onClick={() => handleDelete(wf.id)}>
                          <Trash2 className="mr-2 h-4 w-4" />
                          {t("delete")}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingId ? t("editTitle") : t("newTitle")}</DialogTitle>
            <DialogDescription>{t("dialogDescription")}</DialogDescription>
          </DialogHeader>

          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="wf-name">{t("name")}</Label>
              <Input id="wf-name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="wf-desc">{t("description")}</Label>
              <Textarea id="wf-desc" value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="wf-trigger">{t("trigger")}</Label>
              <select
                id="wf-trigger"
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={trigger}
                onChange={(e) => setTrigger(e.target.value as WorkflowTrigger)}
              >
                {TRIGGERS.map((tr) => (
                  <option key={tr} value={tr}>
                    {t(`triggers.${tr}`)}
                  </option>
                ))}
              </select>
            </div>

            {/* Conditions */}
            <div className="grid gap-2">
              <div className="flex items-center justify-between">
                <Label>{t("conditions")}</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setConditions((prev) => [...prev, emptyCondition()])}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  {t("addCondition")}
                </Button>
              </div>
              {conditions.map((cond, idx) => (
                <div key={idx} className="grid gap-2 rounded-lg border p-2 sm:grid-cols-[1fr_0.7fr_1fr_auto]">
                  <Input
                    placeholder={t("field")}
                    value={cond.field}
                    onChange={(e) =>
                      setConditions((prev) =>
                        prev.map((c, i) => (i === idx ? { ...c, field: e.target.value } : c))
                      )
                    }
                  />
                  <select
                    className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-sm"
                    value={cond.op}
                    onChange={(e) =>
                      setConditions((prev) =>
                        prev.map((c, i) =>
                          i === idx ? { ...c, op: e.target.value as WorkflowCondition["op"] } : c
                        )
                      )
                    }
                  >
                    {CONDITION_OPS.map((op) => (
                      <option key={op} value={op}>
                        {op}
                      </option>
                    ))}
                  </select>
                  <Input
                    placeholder={t("value")}
                    value={String(cond.value ?? "")}
                    onChange={(e) =>
                      setConditions((prev) =>
                        prev.map((c, i) => (i === idx ? { ...c, value: e.target.value } : c))
                      )
                    }
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={t("remove")}
                    onClick={() => setConditions((prev) => prev.filter((_, i) => i !== idx))}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="grid gap-2">
              <div className="flex items-center justify-between">
                <Label>{t("actions")}</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setActions((prev) => [...prev, emptyAction()])}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  {t("addAction")}
                </Button>
              </div>
              {actions.map((action, idx) => (
                <div key={idx} className="grid gap-2 rounded-lg border p-2 sm:grid-cols-[1fr_1.2fr_auto]">
                  <select
                    className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-sm"
                    value={action.type}
                    onChange={(e) =>
                      setActions((prev) =>
                        prev.map((a, i) => (i === idx ? { ...a, type: e.target.value } : a))
                      )
                    }
                  >
                    {ACTION_TYPES.map((at) => (
                      <option key={at} value={at}>
                        {t(`actionTypes.${at}`)}
                      </option>
                    ))}
                  </select>
                  {action.type === "add_tag" ? (
                    <Input
                      placeholder={t("tag")}
                      value={action.tag ?? ""}
                      onChange={(e) =>
                        setActions((prev) =>
                          prev.map((a, i) => (i === idx ? { ...a, tag: e.target.value } : a))
                        )
                      }
                    />
                  ) : action.type === "update_lead_status" ? (
                    <Input
                      placeholder={t("status")}
                      value={action.status ?? ""}
                      onChange={(e) =>
                        setActions((prev) =>
                          prev.map((a, i) => (i === idx ? { ...a, status: e.target.value } : a))
                        )
                      }
                    />
                  ) : (
                    <Input
                      placeholder={t("actionTitle")}
                      value={action.title ?? ""}
                      onChange={(e) =>
                        setActions((prev) =>
                          prev.map((a, i) => (i === idx ? { ...a, title: e.target.value } : a))
                        )
                      }
                    />
                  )}
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={t("remove")}
                    onClick={() => setActions((prev) => prev.filter((_, i) => i !== idx))}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              {t("cancel")}
            </Button>
            <Button onClick={handleSave} disabled={saving || !name.trim()}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t("save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
