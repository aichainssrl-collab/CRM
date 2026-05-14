"use client";

import { useState } from "react";
import { useDeals, useCreateDeal, Deal } from "@/hooks/useDeals";
import { KanbanBoard } from "@/components/crm/KanbanBoard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
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
  const [sheetOpen, setSheetOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const totalValue = deals?.reduce((sum, d) => sum + (d.value ?? 0), 0) ?? 0;
  const totalByStage = STAGES.reduce<Record<string, number>>((acc, s) => {
    acc[s.id] = deals?.filter(d => d.stage === s.id).reduce((sum, d) => sum + (d.value ?? 0), 0) ?? 0;
    return acc;
  }, {});

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    const fd = new FormData(e.currentTarget);
    try {
      await createDeal({
        lead_id: fd.get("leadId") as string,
        title: fd.get("title") as string,
        value: fd.get("value") ? Number(fd.get("value")) : undefined,
        stage: fd.get("stage") as string,
        probability: fd.get("probability") ? Number(fd.get("probability")) : 0,
      });
      setSheetOpen(false);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex-1 overflow-hidden flex flex-col p-8 bg-surface-container-low h-[calc(100vh-56px)]">
      <div className="flex items-center justify-between mb-6 shrink-0">
        <div>
          <h2 className="text-h1 font-h1 text-on-surface">Deals Pipeline</h2>
          {!isLoading && deals && (
            <p className="text-small text-on-surface-variant mt-0.5">
              {deals.length} deal{deals.length !== 1 ? "s" : ""} · {formatCurrency(totalValue)} totale
            </p>
          )}
        </div>
        <Button
          className="h-input_height px-4 bg-[#3B5BDB] text-white font-small-medium hover:bg-[#3B5BDB]/90 flex gap-2 shadow-sm"
          onClick={() => setSheetOpen(true)}
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
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
          <form onSubmit={handleCreate} className="space-y-5 py-6">
            <div className="space-y-2">
              <label htmlFor="leadId" className="text-sm font-medium">Lead ID *</label>
              <Input id="leadId" name="leadId" required placeholder="es. abc123" />
            </div>
            <div className="space-y-2">
              <label htmlFor="title" className="text-sm font-medium">Titolo *</label>
              <Input id="title" name="title" required />
            </div>
            <div className="space-y-2">
              <label htmlFor="value" className="text-sm font-medium">Valore (€)</label>
              <Input id="value" name="value" type="number" min={0} step={100} placeholder="0" />
            </div>
            <div className="space-y-2">
              <label htmlFor="stage" className="text-sm font-medium">Stage *</label>
              <select
                id="stage"
                name="stage"
                required
                defaultValue="new"
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                {STAGES.map(s => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label htmlFor="probability" className="text-sm font-medium">Probabilità (0–100)</label>
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
    </main>
  );
}
