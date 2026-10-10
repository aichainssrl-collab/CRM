"use client";

import { useState, useEffect } from "react";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { useLeads, useCreateLead, useUpdateLead, useDeleteLead, Lead } from "@/hooks/useLeads";
import { useQueryClient } from "@tanstack/react-query";
import { LeadTable } from "@/components/crm/LeadTable";
import { LeadFilters } from "@/components/crm/LeadFilters";
import { LeadForm } from "@/components/crm/LeadForm";
import { CsvImportDialog } from "@/components/crm/CsvImportDialog";
import { ConfirmDialog } from "@/components/crm/ConfirmDialog";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
} from "@/components/ui/pagination";
import { Plus, Upload, Trash2, ChevronLeft, ChevronRight, Download } from "lucide-react";
import { toast } from "sonner";
import { downloadCSV } from "@/lib/export";

const PAGE_SIZE = 20;

function buildPageNumbers(current: number, total: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "…")[] = [1];
  if (current > 3) pages.push("…");
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i);
  if (current < total - 2) pages.push("…");
  pages.push(total);
  return pages;
}

export default function LeadsPage() {
  const t = useTranslations("leads");
  const router = useRouter();

  const [filters, setFilters] = useState<Record<string, string>>({});
  const [page, setPage] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleteConfirm, setDeleteConfirm] = useState<{ type: "single" | "bulk"; id?: string } | null>(null);

  const queryClient = useQueryClient();
  const { data: leads = [], isLoading } = useLeads(filters);
  const createLead = useCreateLead();
  const updateLead = useUpdateLead();
  const deleteLead = useDeleteLead();

  // Reset to page 1 whenever filters change
  useEffect(() => { setPage(1); }, [filters]);

  const totalPages = Math.max(1, Math.ceil(leads.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paginatedLeads = leads.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const pageNumbers = buildPageNumbers(safePage, totalPages);

  const handleFilterChange = (key: string, value: string | undefined) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === undefined) delete next[key]; else next[key] = value;
      return next;
    });
  };

  const handleEdit = (lead: Lead) => { setSelectedLead(lead); setIsFormOpen(true); };

  const handleDelete = (id: string) => {
    setDeleteConfirm({ type: "single", id });
  };

  const executeDelete = async () => {
    try {
      if (deleteConfirm?.type === "single" && deleteConfirm.id) {
        await deleteLead.mutateAsync(deleteConfirm.id);
        queryClient.invalidateQueries({ queryKey: ["leads"] });
        toast.success(t("leadDeleted"));
      } else if (deleteConfirm?.type === "bulk") {
        await Promise.all(Array.from(selectedIds).map((id) => deleteLead.mutateAsync(id)));
        setSelectedIds(new Set());
        queryClient.invalidateQueries({ queryKey: ["leads"] });
        toast.success(t("leadsDeleted", { count: selectedIds.size }));
      }
    } catch (err: unknown) {
      toast.error(t("deleteError"), { description: err instanceof Error ? err.message : String(err) });
    }
  };

  const handleView = (id: string) => router.push(`/crm/leads/${id}`);

  const handleFormSubmit = async (data: Partial<Lead>) => {
    if (selectedLead) {
      await updateLead.mutateAsync({ id: selectedLead.id, data });
      toast.success(t("leadUpdated"));
    } else {
      await createLead.mutateAsync(data);
      toast.success(t("leadCreated"));
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const handleToggleAll = () => {
    setSelectedIds((prev) =>
      prev.size === paginatedLeads.length
        ? new Set()
        : new Set(paginatedLeads.map((l) => l.id))
    );
  };

  return (
    <div className="flex flex-1 flex-col gap-4 p-6 overflow-hidden">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("title")}
            <span className="ml-2 text-base font-normal text-muted-foreground">({leads.length})</span>
          </h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {selectedIds.size > 0 && (
            <Button variant="destructive" size="sm" onClick={() => setDeleteConfirm({ type: "bulk" })} disabled={deleteLead.isPending} className="gap-2">
              <Trash2 className="h-4 w-4" />
              {t("deleteSelected")} ({selectedIds.size})
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => downloadCSV("leads").catch(() => toast.error("Export fallito"))} className="gap-2">
            <Download className="h-4 w-4" />
            CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => setIsImportOpen(true)} className="gap-2">
            <Upload className="h-4 w-4" />
            {t("importCsv")}
          </Button>
          <Button size="sm" onClick={() => { setSelectedLead(null); setIsFormOpen(true); }} className="gap-2">
            <Plus className="h-4 w-4" />
            {t("newLead")}
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="shrink-0">
        <LeadFilters filters={filters} onChange={handleFilterChange} />
      </div>

      {/* Table */}
      <div className="flex-1 overflow-hidden border rounded-md">
        <LeadTable
          leads={paginatedLeads}
          isLoading={isLoading}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onToggleAll={handleToggleAll}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onView={handleView}
        />
      </div>

      {/* Pagination */}
      {!isLoading && leads.length > PAGE_SIZE && (
        <div className="shrink-0 flex items-center justify-between gap-4">
          <p className="text-sm text-muted-foreground">
            {(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, leads.length)} {t("of")} {leads.length}
          </p>
          <Pagination className="w-auto mx-0">
            <PaginationContent>
              <PaginationItem>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9"
                  disabled={safePage === 1}
                  onClick={() => setPage((p) => p - 1)}
                  aria-label="Pagina precedente"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              </PaginationItem>

              {pageNumbers.map((n, i) =>
                n === "…" ? (
                  <PaginationItem key={`ellipsis-${i}`}>
                    <PaginationEllipsis />
                  </PaginationItem>
                ) : (
                  <PaginationItem key={n}>
                    <Button
                      variant={n === safePage ? "outline" : "ghost"}
                      size="icon"
                      className="h-9 w-9"
                      onClick={() => setPage(n)}
                      aria-current={n === safePage ? "page" : undefined}
                    >
                      {n}
                    </Button>
                  </PaginationItem>
                )
              )}

              <PaginationItem>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9"
                  disabled={safePage === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  aria-label="Pagina successiva"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}

      <LeadForm
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        lead={selectedLead}
        onSubmit={handleFormSubmit}
      />
      <CsvImportDialog open={isImportOpen} onOpenChange={setIsImportOpen} />

      <ConfirmDialog
        open={!!deleteConfirm}
        onOpenChange={(open) => { if (!open) setDeleteConfirm(null); }}
        title={deleteConfirm?.type === "bulk" ? t("confirmDeleteTitlePlural", { count: selectedIds.size }) : t("confirmDeleteTitle")}
        description={
          deleteConfirm?.type === "bulk"
            ? t("confirmDeleteDescPlural", { count: selectedIds.size })
            : t("confirmDeleteDesc")
        }
        confirmLabel={t("deleteSelected")}
        variant="destructive"
        onConfirm={executeDelete}
        loading={deleteLead.isPending}
      />
    </div>
  );
}