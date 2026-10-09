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
  useCompetitors, useCompetitorStats, useCompetitorChanges,
  useCreateCompetitor, useUpdateCompetitor, useDeleteCompetitor,
  useScanCompetitor, useScanAll,
  type Competitor,
} from "@/hooks/useCompetitors";
import {
  Radar, Plus, Trash2, MoreHorizontal, RefreshCw, Edit,
  Loader2, Globe, TrendingUp,
} from "lucide-react";

export default function CompetitorsPage() {
  const t = useTranslations("competitors");
  const tSidebar = useTranslations("sidebar");
  const { data: competitors, isLoading } = useCompetitors();
  const { data: stats } = useCompetitorStats();
  const { data: changes } = useCompetitorChanges();
  const createCompetitor = useCreateCompetitor();
  const updateCompetitor = useUpdateCompetitor();
  const deleteCompetitor = useDeleteCompetitor();
  const scanCompetitor = useScanCompetitor();
  const scanAll = useScanAll();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [description, setDescription] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [scanningId, setScanningId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  function resetForm() {
    setEditingId(null);
    setName("");
    setWebsite("");
    setDescription("");
    setTagInput("");
  }

  function openCreate() {
    resetForm();
    setDialogOpen(true);
  }

  function openEdit(c: Competitor) {
    setEditingId(c.id);
    setName(c.name);
    setWebsite(c.website || "");
    setDescription(c.description || "");
    setTagInput((c.tags || []).join(", "));
    setDialogOpen(true);
  }

  async function handleSave() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        website: website.trim(),
        description: description.trim(),
        tags: tagInput.split(",").map((s) => s.trim()).filter(Boolean),
      };
      if (editingId) {
        await updateCompetitor.mutateAsync({ id: editingId, data: payload });
      } else {
        await createCompetitor.mutateAsync(payload);
      }
      setDialogOpen(false);
      resetForm();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm(t("confirmDelete"))) return;
    await deleteCompetitor.mutateAsync(id);
  }

  async function handleScan(id: string) {
    setScanningId(id);
    try {
      await scanCompetitor.mutateAsync(id);
    } finally {
      setScanningId(null);
    }
  }

  const recentChanges = (changes || []).slice(0, 8);

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{tSidebar("competitors")}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t("subtitle")}</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => scanAll.mutate()}
            disabled={scanAll.isPending}
          >
            {scanAll.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            {t("scanAll")}
          </Button>
          <Button onClick={openCreate}>
            <Plus className="mr-2 h-4 w-4" />
            {t("new")}
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("total")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.totalCount ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("active")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.activeCount ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("changes")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.changeCount ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("snapshots")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.snapshotCount ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Radar className="h-5 w-5 text-primary" />
              {t("listTitle")}
            </CardTitle>
            <CardDescription>{t("listDescription")}</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : !competitors?.length ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Radar className="h-10 w-10 text-muted-foreground/40 mb-3" />
                <p className="text-sm text-muted-foreground">{t("empty")}</p>
                <Button variant="outline" size="sm" className="mt-4" onClick={openCreate}>
                  <Plus className="mr-2 h-4 w-4" />
                  {t("new")}
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {competitors.map((c) => (
                  <div
                    key={c.id}
                    className="rounded-lg border border-border/60 p-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium">{c.name}</span>
                          <Badge variant={c.status === "active" ? "default" : "outline"}>
                            {t(`status.${c.status}`)}
                          </Badge>
                          {c.changeCount > 0 && (
                            <Badge variant="secondary">
                              {c.changeCount} {t("changeBadge")}
                            </Badge>
                          )}
                        </div>
                        {c.website && (
                          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                            <Globe className="h-3 w-3" />
                            {c.website}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-1 mt-1">
                          {(c.tags || []).map((tag) => (
                            <Badge key={tag} variant="outline" className="text-[10px]">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                        <p className="text-[11px] text-muted-foreground mt-1">
                          {t("lastChecked")}:{" "}
                          {c.lastCheckedAt
                            ? new Date(c.lastCheckedAt).toLocaleString()
                            : t("never")}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={t("scan")}
                          disabled={scanningId === c.id}
                          onClick={() => handleScan(c.id)}
                        >
                          {scanningId === c.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RefreshCw className="h-4 w-4" />
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
                            <DropdownMenuItem onClick={() => openEdit(c)}>
                              <Edit className="mr-2 h-4 w-4" />
                              {t("edit")}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() =>
                                setExpandedId(expandedId === c.id ? null : c.id)
                              }
                            >
                              <TrendingUp className="mr-2 h-4 w-4" />
                              {t("toggleChanges")}
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              variant="destructive"
                              onClick={() => handleDelete(c.id)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              {t("delete")}
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                    {expandedId === c.id && (
                      <div className="mt-3 border-t border-border/60 pt-2 space-y-1">
                        {(changes || [])
                          .filter((ch) => ch.competitorId === c.id)
                          .slice(0, 5)
                          .map((ch) => (
                            <div key={ch.id} className="text-xs">
                              <span className="font-medium">{ch.field}</span>
                              <span className="text-muted-foreground">: </span>
                              <span className="line-through opacity-60">
                                {(ch.from || "").slice(0, 40)}
                              </span>
                              {" → "}
                              <span>{(ch.to || "").slice(0, 40)}</span>
                            </div>
                          ))}
                        {!((changes || []).some((ch) => ch.competitorId === c.id)) && (
                          <p className="text-xs text-muted-foreground">{t("noChanges")}</p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              {t("recentChanges")}
            </CardTitle>
            <CardDescription>{t("recentChangesHint")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!recentChanges.length ? (
              <p className="text-sm text-muted-foreground">{t("noChanges")}</p>
            ) : (
              recentChanges.map((ch) => {
                const comp = competitors?.find((c) => c.id === ch.competitorId);
                return (
                  <div key={ch.id} className="text-xs border-b border-border/40 pb-2 last:border-0">
                    <p className="font-medium">{comp?.name || ch.competitorId}</p>
                    <p className="text-muted-foreground">
                      {ch.field}: {(ch.to || "").slice(0, 60)}
                    </p>
                    <p className="text-[10px] text-muted-foreground/70">
                      {new Date(ch.detectedAt).toLocaleString()}
                    </p>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingId ? t("editTitle") : t("newTitle")}</DialogTitle>
            <DialogDescription>{t("dialogDescription")}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="comp-name">{t("name")}</Label>
              <Input id="comp-name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="comp-web">{t("website")}</Label>
              <Input
                id="comp-web"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                placeholder="https://..."
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="comp-desc">{t("description")}</Label>
              <Textarea
                id="comp-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="comp-tags">{t("tags")}</Label>
              <Input
                id="comp-tags"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                placeholder="legal, rag, enterprise"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              {t("cancel")}
            </Button>
            <Button onClick={handleSave} disabled={saving || !name.trim()}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {t("save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
