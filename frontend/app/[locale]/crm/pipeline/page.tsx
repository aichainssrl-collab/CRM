"use client";

import { useState } from "react";
import { useDeals, useCreateDeal } from "@/hooks/useDeals";
import { useLeads } from "@/hooks/useLeads";
import { KanbanBoard } from "@/components/crm/KanbanBoard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";

const STAGES = [
  { id: "new", label: "New" },
  { id: "contacted", label: "Contacted" },
  { id: "qualified", label: "Qualified" },
  { id: "proposal", label: "Proposal" },
  { id: "won", label: "Won" },
  { id: "lost", label: "Lost" },
];

function formatCurrency(value: number) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

export default function PipelinePage() {
  const { data: deals, isLoading } = useDeals();
  const { mutateAsync: createDeal } = useCreateDeal();
  const { data: leads = [] } = useLeads();
  const [sheetOpen, setSheetOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedLeadId, setSelectedLeadId] = useState<string>("");
  const [selectedStage, setSelectedStage] = useState<string>("new");

  const totalValue = deals?.reduce((sum, d) => sum + (d.value ?? 0), 0) ?? 0;

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selectedLeadId) {
      toast.error("Seleziona un lead");
      return;
    }
    setSubmitting(true);
    const fd = new FormData(e.currentTarget);
    try {
      await createDeal({
        lead_id: selectedLeadId,
        title: fd.get("title") as string,
        value: fd.get("value") ? Number(fd.get("value")) : undefined,
        stage: selectedStage,
        probability: fd.get("probability") ? Number(fd.get("probability")) : 0,
      });
      setSheetOpen(false);
      setSelectedLeadId("");
      setSelectedStage("new");
      toast.success("Deal creato");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error("Errore durante la creazione del deal", { description: msg });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden p-6 gap-4">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Deals Pipeline</h1>
          {!isLoading && deals && (
            <p className="text-sm text-muted-foreground mt-0.5">
              {deals.length} deal{deals.length !== 1 ? "s" : ""} · {formatCurrency(totalValue)} totale
            </p>
          )}
        </div>
        <Button onClick={() => setSheetOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Nuovo Deal
        </Button>
      </div>

      {isLoading ? (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map(s => (
            <div key={s.id} className="flex-shrink-0 w-[300px] space-y-3">
              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-24 w-full rounded-lg" />
              <Skeleton className="h-24 w-full rounded-lg" />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex-1 overflow-hidden">
          <KanbanBoard deals={deals ?? []} />
        </div>
      )}

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent className="sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Nuovo Deal</SheetTitle>
            <SheetDescription>Crea una nuova opportunità commerciale.</SheetDescription>
          </SheetHeader>
          <form onSubmit={handleCreate} className="space-y-4 py-6">
            <div className="space-y-2">
              <Label>Lead *</Label>
              <Select value={selectedLeadId} onValueChange={(v) => setSelectedLeadId(v ?? "")} required>
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona un lead..." />
                </SelectTrigger>
                <SelectContent>
                  {leads.map(l => (
                    <SelectItem key={l.id} value={l.id}>
                      {[l.firstName, l.lastName].filter(Boolean).join(" ") || l.email}
                      {l.companyName ? ` — ${l.companyName}` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="title">Titolo *</Label>
              <Input id="title" name="title" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="value">Valore (€)</Label>
              <Input id="value" name="value" type="number" min={0} step={100} placeholder="0" />
            </div>
            <div className="space-y-2">
              <Label>Stage *</Label>
              <Select value={selectedStage} onValueChange={(v) => setSelectedStage(v ?? "new")} required>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STAGES.map(s => (
                    <SelectItem key={s.id} value={s.id}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="probability">Probabilità (0–100)</Label>
              <Input id="probability" name="probability" type="number" min={0} max={100} step={5} placeholder="0" />
            </div>
            <SheetFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setSheetOpen(false)}>
                Annulla
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Salvataggio..." : "Crea Deal"}
              </Button>
            </SheetFooter>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}
