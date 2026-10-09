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
  useContent, useContentStats, useContentTags,
  useCreateContent, useUpdateContent, useDeleteContent,
  type ContentItem,
} from "@/hooks/useContent";
import {
  Library, Plus, Trash2, MoreHorizontal, Copy, Edit,
  Loader2, Search,
} from "lucide-react";

const TYPES = ["email", "ad_copy", "social", "landing", "blog", "other"] as const;

export default function ContentLibraryPage() {
  const t = useTranslations("contentLibrary");
  const tSidebar = useTranslations("sidebar");
  const [filterType, setFilterType] = useState<string>("");
  const [filterTag, setFilterTag] = useState<string>("");
  const [search, setSearch] = useState("");

  const { data: items, isLoading } = useContent({
    type: filterType || undefined,
    tag: filterTag || undefined,
    q: search || undefined,
  });
  const { data: stats } = useContentStats();
  const { data: tags } = useContentTags();
  const createContent = useCreateContent();
  const updateContent = useUpdateContent();
  const deleteContent = useDeleteContent();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [type, setType] = useState<string>("email");
  const [body, setBody] = useState("");
  const [description, setDescription] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  function resetForm() {
    setEditingId(null);
    setTitle("");
    setType("email");
    setBody("");
    setDescription("");
    setTagInput("");
  }

  function openCreate() {
    resetForm();
    setDialogOpen(true);
  }

  function openEdit(item: ContentItem) {
    setEditingId(item.id);
    setTitle(item.title);
    setType(item.type);
    setBody(item.body);
    setDescription(item.description || "");
    setTagInput((item.tags || []).join(", "));
    setDialogOpen(true);
  }

  async function handleSave() {
    if (!title.trim()) return;
    setSaving(true);
    try {
      const payload = {
        title,
        type,
        body,
        description,
        tags: tagInput.split(",").map((s) => s.trim()).filter(Boolean),
      };
      if (editingId) {
        await updateContent.mutateAsync({ id: editingId, data: payload });
      } else {
        await createContent.mutateAsync(payload);
      }
      setDialogOpen(false);
      resetForm();
    } finally {
      setSaving(false);
    }
  }

  async function handleCopy(item: ContentItem) {
    try {
      await navigator.clipboard.writeText(item.body);
      setCopiedId(item.id);
      setTimeout(() => setCopiedId(null), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  async function handleDelete(id: string) {
    if (!confirm(t("confirmDelete"))) return;
    await deleteContent.mutateAsync(id);
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{tSidebar("content")}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t("subtitle")}</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          {t("new")}
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("total")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.totalCount ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        {(["email", "social", "ad_copy"] as const).map((key) => (
          <Card key={key}>
            <CardHeader className="pb-2">
              <CardDescription>{t(`types.${key}`)}</CardDescription>
              <CardTitle className="text-2xl">{stats?.byType?.[key] ?? 0}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="w-56 pl-8"
            placeholder={t("search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="">{t("allTypes")}</option>
          {TYPES.map((ty) => (
            <option key={ty} value={ty}>
              {t(`types.${ty}`)}
            </option>
          ))}
        </select>
        {!!tags?.length && (
          <select
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
            value={filterTag}
            onChange={(e) => setFilterTag(e.target.value)}
          >
            <option value="">{t("allTags")}</option>
            {tags.map((tag) => (
              <option key={tag} value={tag}>
                #{tag}
              </option>
            ))}
          </select>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Library className="h-5 w-5 text-primary" />
            {t("listTitle")}
          </CardTitle>
          <CardDescription>{t("listDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : !items?.length ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Library className="h-10 w-10 text-muted-foreground/40 mb-3" />
              <p className="text-sm text-muted-foreground">{t("empty")}</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={openCreate}>
                <Plus className="mr-2 h-4 w-4" />
                {t("new")}
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border border-border/60 p-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{t(`types.${item.type}`)}</Badge>
                        {item.language && (
                          <span className="text-xs text-muted-foreground uppercase">{item.language}</span>
                        )}
                      </div>
                      <p className="font-medium truncate">{item.title}</p>
                      {item.tags?.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {item.tags.map((tag) => (
                            <button
                              key={tag}
                              type="button"
                              className="text-xs text-primary hover:underline"
                              onClick={() => setFilterTag(tag)}
                            >
                              #{tag}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(item)}
                      >
                        <Copy className="mr-1 h-3 w-3" />
                        {copiedId === item.id ? t("copied") : t("copy")}
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
                          <DropdownMenuItem onClick={() => openEdit(item)}>
                            <Edit className="mr-2 h-4 w-4" />
                            {t("edit")}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem variant="destructive" onClick={() => handleDelete(item.id)}>
                            <Trash2 className="mr-2 h-4 w-4" />
                            {t("delete")}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap rounded bg-muted/40 p-2 text-xs text-muted-foreground line-clamp-4">
                    {item.body}
                  </p>
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
              <Label htmlFor="cl-title">{t("title")}</Label>
              <Input id="cl-title" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="cl-type">{t("type")}</Label>
                <select
                  id="cl-type"
                  className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                >
                  {TYPES.map((ty) => (
                    <option key={ty} value={ty}>
                      {t(`types.${ty}`)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="cl-tags">{t("tags")}</Label>
                <Input
                  id="cl-tags"
                  placeholder={t("tagsPlaceholder")}
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="cl-desc">{t("description")}</Label>
              <Input id="cl-desc" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="cl-body">{t("body")}</Label>
              <Textarea id="cl-body" value={body} onChange={(e) => setBody(e.target.value)} rows={10} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              {t("cancel")}
            </Button>
            <Button onClick={handleSave} disabled={saving || !title.trim()}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t("save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
