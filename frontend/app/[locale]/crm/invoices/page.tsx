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
  useInvoices, useInvoiceStats, useCreateInvoice, useUpdateInvoice,
  useDeleteInvoice, useSendInvoice, usePayInvoice, useCancelInvoice,
  useInvoiceFromProposal,
  type Invoice, type InvoiceItem,
} from "@/hooks/useInvoices";
import { useProposals } from "@/hooks/useProposals";
import {
  Receipt, Plus, Trash2, MoreHorizontal, Send, CheckCircle2,
  XCircle, Loader2, FileText,
} from "lucide-react";

function formatEUR(n: number) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n);
}

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "outline",
  sent: "default",
  paid: "secondary",
  overdue: "destructive",
  cancelled: "outline",
};

function emptyItem(): InvoiceItem {
  return { name: "", quantity: 1, unitPrice: 0 };
}

export default function InvoicesPage() {
  const t = useTranslations("invoices");
  const tSidebar = useTranslations("sidebar");
  const { data: invoices, isLoading } = useInvoices();
  const { data: stats } = useInvoiceStats();
  const { data: acceptedProposals } = useProposals("accepted");
  const createInvoice = useCreateInvoice();
  const updateInvoice = useUpdateInvoice();
  const deleteInvoice = useDeleteInvoice();
  const sendInvoice = useSendInvoice();
  const payInvoice = usePayInvoice();
  const cancelInvoice = useCancelInvoice();
  const fromProposal = useInvoiceFromProposal();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [clientName, setClientName] = useState("");
  const [clientEmail, setClientEmail] = useState("");
  const [taxRate, setTaxRate] = useState(22);
  const [dueDate, setDueDate] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<InvoiceItem[]>([emptyItem()]);
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
    setDueDate("");
    setNotes("");
    setItems([emptyItem()]);
  }

  function openCreate() {
    resetForm();
    setDialogOpen(true);
  }

  function openEdit(inv: Invoice) {
    setEditingId(inv.id);
    setTitle(inv.title);
    setClientName(inv.clientName);
    setClientEmail(inv.clientEmail);
    setTaxRate(inv.taxRate);
    setDueDate(inv.dueDate || "");
    setNotes(inv.notes || "");
    setItems(inv.items?.length ? inv.items.map((i) => ({ ...i })) : [emptyItem()]);
    setDialogOpen(true);
  }

  function updateItem(idx: number, patch: Partial<InvoiceItem>) {
    setItems((prev) => prev.map((it, i) => (i === idx ? { ...it, ...patch } : it)));
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
        dueDate: dueDate || undefined,
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
        await updateInvoice.mutateAsync({ id: editingId, data: payload });
      } else {
        await createInvoice.mutateAsync(payload);
      }
      setDialogOpen(false);
      resetForm();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm(t("confirmDelete"))) return;
    await deleteInvoice.mutateAsync(id);
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{tSidebar("invoices")}</h1>
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
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("totalValue")}</CardDescription>
            <CardTitle className="text-xl">{stats ? formatEUR(stats.totalValue) : "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("paidValue")}</CardDescription>
            <CardTitle className="text-xl text-primary">
              {stats ? formatEUR(stats.paidValue) : "—"}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("outstanding")}</CardDescription>
            <CardTitle className="text-xl">
              {stats ? formatEUR(stats.outstandingValue) : "—"}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* From accepted proposals */}
      {!!acceptedProposals?.length && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-4 w-4 text-primary" />
              {t("fromProposals")}
            </CardTitle>
            <CardDescription>{t("fromProposalsHint")}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {acceptedProposals.map((p) => (
              <Button
                key={p.id}
                variant="outline"
                size="sm"
                onClick={() => fromProposal.mutate(p.id)}
                disabled={fromProposal.isPending}
              >
                <Receipt className="mr-2 h-3 w-3" />
                {p.number} — {p.clientName || p.title}
              </Button>
            ))}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Receipt className="h-5 w-5 text-primary" />
            {t("listTitle")}
          </CardTitle>
          <CardDescription>{t("listDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !invoices?.length ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Receipt className="h-10 w-10 text-muted-foreground/40 mb-3" />
              <p className="text-sm text-muted-foreground">{t("empty")}</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={openCreate}>
                <Plus className="mr-2 h-4 w-4" />
                {t("new")}
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {invoices.map((inv) => (
                <div
                  key={inv.id}
                  className="flex flex-col gap-2 rounded-lg border border-border/60 p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-muted-foreground">{inv.number}</span>
                      <Badge variant={STATUS_VARIANT[inv.status] ?? "outline"}>
                        {t(`status.${inv.status}`)}
                      </Badge>
                    </div>
                    <p className="font-medium truncate">{inv.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {inv.clientName || "—"}
                      {inv.dueDate ? ` · ${t("due")} ${new Date(inv.dueDate).toLocaleDateString("it-IT")}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <p className="font-semibold">{formatEUR(inv.total)}</p>
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
                        <DropdownMenuItem onClick={() => openEdit(inv)}>
                          {t("edit")}
                        </DropdownMenuItem>
                        {inv.status === "draft" && (
                          <DropdownMenuItem onClick={() => sendInvoice.mutate(inv.id)}>
                            <Send className="mr-2 h-4 w-4" />
                            {t("send")}
                          </DropdownMenuItem>
                        )}
                        {inv.status !== "paid" && inv.status !== "cancelled" && (
                          <DropdownMenuItem onClick={() => payInvoice.mutate(inv.id)}>
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                            {t("markPaid")}
                          </DropdownMenuItem>
                        )}
                        {inv.status !== "paid" && (
                          <DropdownMenuItem onClick={() => cancelInvoice.mutate(inv.id)}>
                            <XCircle className="mr-2 h-4 w-4" />
                            {t("cancel")}
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem variant="destructive" onClick={() => handleDelete(inv.id)}>
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
              <Label htmlFor="inv-title">{t("title")}</Label>
              <Input id="inv-title" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="inv-client">{t("clientName")}</Label>
                <Input id="inv-client" value={clientName} onChange={(e) => setClientName(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="inv-email">{t("clientEmail")}</Label>
                <Input id="inv-email" type="email" value={clientEmail} onChange={(e) => setClientEmail(e.target.value)} />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="inv-tax">{t("taxRate")}</Label>
                <Input
                  id="inv-tax"
                  type="number"
                  min={0}
                  max={100}
                  value={taxRate}
                  onChange={(e) => setTaxRate(Number(e.target.value))}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="inv-due">{t("dueDate")}</Label>
                <Input id="inv-due" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
              </div>
            </div>

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
                  <div key={idx} className="grid gap-2 rounded-lg border p-2 sm:grid-cols-[1.4fr_0.5fr_0.8fr_auto]">
                    <Input
                      placeholder={t("itemName")}
                      value={item.name}
                      onChange={(e) => updateItem(idx, { name: e.target.value })}
                    />
                    <Input
                      type="number"
                      min={1}
                      value={item.quantity}
                      onChange={(e) => updateItem(idx, { quantity: Number(e.target.value) })}
                    />
                    <Input
                      type="number"
                      min={0}
                      step="0.01"
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

            <div className="flex items-end justify-between text-sm text-muted-foreground">
              <div className="w-full max-w-xs">
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

            <div className="grid gap-2">
              <Label htmlFor="inv-notes">{t("notes")}</Label>
              <Textarea id="inv-notes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
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
