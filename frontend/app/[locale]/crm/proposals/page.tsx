"use client";

import { useMemo, useState } from "react";
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
  useProposals, useProposalStats, useCreateProposal, useUpdateProposal,
  useDeleteProposal, useSendProposal, useAcceptProposal, useRejectProposal,
  type Proposal, type ProposalItem,
} from "@/hooks/useProposals";
import { useProducts } from "@/hooks/useProducts";
import {
  FileText, Plus, Trash2, MoreHorizontal, Send, CheckCircle2,
  XCircle, Loader2, Package, Euro, Download,
} from "lucide-react";
import { downloadDocumentPdf } from "@/lib/pdf";
import { useLocale } from "next-intl";

function formatEUR(n: number) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n);
}

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "outline",
  sent: "default",
  accepted: "secondary",
  rejected: "destructive",
  expired: "outline",
};

function emptyItem(): ProposalItem {
  return { name: "", quantity: 1, unitPrice: 0 };
}

export default function ProposalsPage() {
  const t = useTranslations("proposals");
  const tSidebar = useTranslations("sidebar");
  const locale = useLocale();
  const { data: proposals, isLoading } = useProposals();
  const { data: stats } = useProposalStats();
  const { data: products } = useProducts();
  const createProposal = useCreateProposal();
  const updateProposal = useUpdateProposal();
  const deleteProposal = useDeleteProposal();
  const sendProposal = useSendProposal();
  const acceptProposal = useAcceptProposal();
  const rejectProposal = useRejectProposal();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [clientName, setClientName] = useState("");
  const [clientEmail, setClientEmail] = useState("");
  const [taxRate, setTaxRate] = useState(22);
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<ProposalItem[]>([emptyItem()]);
  const [saving, setSaving] = useState(false);

  const lineSubtotal = useMemo(
    () => items.reduce((sum, i) => sum + (i.quantity || 0) * (i.unitPrice || 0), 0),
    [items]
  );
  const lineTotal = lineSubtotal * (1 + taxRate / 100);

  function resetForm() {
    setEditingId(null);
    setTitle("");
    setClientName("");
    setClientEmail("");
    setTaxRate(22);
    setNotes("");
    setItems([emptyItem()]);
  }

  function openCreate() {
    resetForm();
    setDialogOpen(true);
  }

  function openEdit(p: Proposal) {
    setEditingId(p.id);
    setTitle(p.title);
    setClientName(p.clientName);
    setClientEmail(p.clientEmail);
    setTaxRate(p.taxRate);
    setNotes(p.notes || "");
    setItems(p.items?.length ? p.items.map((i) => ({ ...i })) : [emptyItem()]);
    setDialogOpen(true);
  }

  function updateItem(idx: number, patch: Partial<ProposalItem>) {
    setItems((prev) => prev.map((it, i) => (i === idx ? { ...it, ...patch } : it)));
  }

  function pickProduct(idx: number, productId: string) {
    const prod = products?.find((p) => p.id === productId);
    if (!prod) return;
    updateItem(idx, {
      productId: prod.id,
      name: prod.name,
      description: prod.description,
      unitPrice: prod.price,
    });
  }

  async function handleSave() {
    if (!title.trim()) return;
    setSaving(true);
    try {
      const payload = {
        title,
        clientName,
        clientEmail,
        taxRate,
        notes,
        items: items.filter((i) => i.name.trim()).map((i) => ({
          productId: i.productId,
          name: i.name,
          description: i.description || "",
          quantity: i.quantity || 1,
          unitPrice: i.unitPrice || 0,
        })),
      };
      if (editingId) {
        await updateProposal.mutateAsync({ id: editingId, data: payload });
      } else {
        await createProposal.mutateAsync(payload);
      }
      setDialogOpen(false);
      resetForm();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm(t("confirmDelete"))) return;
    await deleteProposal.mutateAsync(id);
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{tSidebar("proposals")}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t("subtitle")}</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          {t("new")}
        </Button>
      </div>

      {/* KPI */}
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("total")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.totalCount ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("totalValue")}</CardDescription>
            <CardTitle className="text-2xl flex items-center gap-1">
              <Euro className="h-5 w-5 text-muted-foreground" />
              {stats ? formatEUR(stats.totalValue).replace("€", "").trim() : "—"}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("acceptedValue")}</CardDescription>
            <CardTitle className="text-2xl">
              {stats?.byStatus?.accepted
                ? formatEUR(stats.byStatus.accepted.totalValue).replace("€", "").trim()
                : "0"}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            {t("listTitle")}
          </CardTitle>
          <CardDescription>{t("listDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !proposals?.length ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Package className="h-10 w-10 text-muted-foreground/40 mb-3" />
              <p className="text-sm text-muted-foreground">{t("empty")}</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={openCreate}>
                <Plus className="mr-2 h-4 w-4" />
                {t("new")}
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {proposals.map((p) => (
                <div
                  key={p.id}
                  className="flex flex-col gap-2 rounded-lg border border-border/60 p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-muted-foreground">{p.number}</span>
                      <Badge variant={STATUS_VARIANT[p.status] ?? "outline"}>
                        {t(`status.${p.status}`)}
                      </Badge>
                    </div>
                    <p className="font-medium truncate">{p.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {p.clientName || "—"}
                      {p.items?.length ? ` · ${p.items.length} ${t("items")}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <p className="font-semibold">{formatEUR(p.total)}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(p.createdAt).toLocaleDateString("it-IT")}
                      </p>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={
                          <Button variant="ghost" size="icon" aria-label={t("actions")}>
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        }
                      />
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openEdit(p)}>
                          {t("edit")}
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() =>
                            downloadDocumentPdf(
                              "proposals",
                              p.id,
                              locale === "en" ? "en" : "it",
                              `${p.number || "proposal"}.pdf`
                            )
                          }
                        >
                          <Download className="mr-2 h-4 w-4" />
                          {t("downloadPdf")}
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() =>
                            downloadDocumentPdf(
                              "proposals",
                              p.id,
                              locale === "en" ? "it" : "en",
                              `${p.number || "proposal"}_${locale === "en" ? "it" : "en"}.pdf`
                            )
                          }
                        >
                          <Download className="mr-2 h-4 w-4" />
                          {locale === "en" ? t("downloadPdfIt") : t("downloadPdfEn")}
                        </DropdownMenuItem>
                        {p.status === "draft" && (
                          <DropdownMenuItem onClick={() => sendProposal.mutate(p.id)}>
                            <Send className="mr-2 h-4 w-4" />
                            {t("send")}
                          </DropdownMenuItem>
                        )}
                        {(p.status === "draft" || p.status === "sent") && (
                          <>
                            <DropdownMenuItem onClick={() => acceptProposal.mutate(p.id)}>
                              <CheckCircle2 className="mr-2 h-4 w-4" />
                              {t("accept")}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => rejectProposal.mutate(p.id)}>
                              <XCircle className="mr-2 h-4 w-4" />
                              {t("reject")}
                            </DropdownMenuItem>
                          </>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() => handleDelete(p.id)}
                        >
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

      {/* Create / Edit dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingId ? t("editTitle") : t("newTitle")}</DialogTitle>
            <DialogDescription>{t("dialogDescription")}</DialogDescription>
          </DialogHeader>

          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="prop-title">{t("title")}</Label>
              <Input
                id="prop-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={t("titlePlaceholder")}
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="prop-client">{t("clientName")}</Label>
                <Input
                  id="prop-client"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="prop-email">{t("clientEmail")}</Label>
                <Input
                  id="prop-email"
                  type="email"
                  value={clientEmail}
                  onChange={(e) => setClientEmail(e.target.value)}
                />
              </div>
            </div>

            {/* Line items */}
            <div className="grid gap-2">
              <div className="flex items-center justify-between">
                <Label>{t("items")}</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setItems((prev) => [...prev, emptyItem()])}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  {t("addItem")}
                </Button>
              </div>
              <div className="space-y-2">
                {items.map((item, idx) => (
                  <div key={idx} className="grid gap-2 rounded-lg border p-2 sm:grid-cols-[1.2fr_0.6fr_0.8fr_auto]">
                    <div className="grid gap-1">
                      {products?.length ? (
                        <select
                          className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-sm"
                          value={item.productId ?? ""}
                          onChange={(e) => {
                            if (e.target.value) pickProduct(idx, e.target.value);
                            else updateItem(idx, { productId: undefined });
                          }}
                        >
                          <option value="">{t("customItem")}</option>
                          {products.map((prod) => (
                            <option key={prod.id} value={prod.id}>
                              {prod.name}
                            </option>
                          ))}
                        </select>
                      ) : null}
                      <Input
                        placeholder={t("itemName")}
                        value={item.name}
                        onChange={(e) => updateItem(idx, { name: e.target.value })}
                      />
                    </div>
                    <Input
                      type="number"
                      min={1}
                      placeholder={t("qty")}
                      value={item.quantity}
                      onChange={(e) => updateItem(idx, { quantity: Number(e.target.value) })}
                    />
                    <Input
                      type="number"
                      min={0}
                      step="0.01"
                      placeholder={t("unitPrice")}
                      value={item.unitPrice}
                      onChange={(e) => updateItem(idx, { unitPrice: Number(e.target.value) })}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label={t("removeItem")}
                      onClick={() => setItems((prev) => prev.filter((_, i) => i !== idx))}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="prop-tax">{t("taxRate")}</Label>
                <Input
                  id="prop-tax"
                  type="number"
                  min={0}
                  max={100}
                  value={taxRate}
                  onChange={(e) => setTaxRate(Number(e.target.value))}
                />
              </div>
              <div className="flex items-end">
                <div className="text-sm text-muted-foreground w-full">
                  <div className="flex justify-between">
                    <span>{t("subtotal")}</span>
                    <span>{formatEUR(lineSubtotal)}</span>
                  </div>
                  <div className="flex justify-between font-semibold text-foreground">
                    <span>{t("total")}</span>
                    <span>{formatEUR(lineTotal)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="prop-notes">{t("notes")}</Label>
              <Textarea
                id="prop-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
              />
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
