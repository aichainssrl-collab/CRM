"use client";

import { useState } from "react";
import { Task, useCreateTask, useUpdateTask } from "@/hooks/useTasks";
import { useLeads } from "@/hooks/useLeads";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { AlertCircle } from "lucide-react";

interface TaskFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task?: Task | null;
  leadId?: string;
}

export function TaskForm({ open, onOpenChange, task, leadId }: TaskFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLeadId, setSelectedLeadId] = useState(leadId || task?.leadId || "");
  const { user } = useAuth();

  const actualLeadId = leadId || task?.leadId || selectedLeadId;
  const { mutateAsync: createTask } = useCreateTask(actualLeadId);
  const { mutateAsync: updateTask } = useUpdateTask(actualLeadId);

  const { data: leads = [], isLoading: leadsLoading } = useLeads();

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (!actualLeadId) {
      setError("Seleziona un lead prima di salvare il task.");
      return;
    }

    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const rawDueDate = formData.get("dueDate") as string;

    let dueDateISO: string;
    try {
      dueDateISO = new Date(rawDueDate).toISOString();
    } catch {
      setError("Data di scadenza non valida.");
      setLoading(false);
      return;
    }

    const data = {
      title: formData.get("title") as string,
      description: (formData.get("description") as string) || undefined,
      dueDate: dueDateISO,
      type: "todo",
      priority: "normal",
      assignedTo: user?.uid ?? "",
    };

    try {
      if (task) {
        await updateTask({ id: task.id, data });
      } else {
        await createTask(data);
      }
      onOpenChange(false);
      setSelectedLeadId(leadId || "");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Errore durante il salvataggio.");
    } finally {
      setLoading(false);
    }
  }

  function handleOpenChange(val: boolean) {
    if (!val) {
      setError(null);
      setSelectedLeadId(leadId || task?.leadId || "");
    }
    onOpenChange(val);
  }

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent className="sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{task ? "Modifica Task" : "Nuovo Task"}</SheetTitle>
          <SheetDescription>
            {task ? "Aggiorna i dettagli del task." : "Crea un nuovo task da tracciare."}
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit} className="space-y-5 py-6">
          {/* Lead selector — shown only when no leadId is pre-set */}
          {!leadId && !task && (
            <div className="space-y-2">
              <label htmlFor="leadSelect" className="text-sm font-medium">Lead *</label>
              <select
                id="leadSelect"
                required
                value={selectedLeadId}
                onChange={(e) => setSelectedLeadId(e.target.value)}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">{leadsLoading ? "Caricamento…" : "Seleziona un lead"}</option>
                {leads.map((lead) => {
                  const name =
                    lead.firstName || lead.lastName
                      ? `${lead.firstName ?? ""} ${lead.lastName ?? ""}`.trim()
                      : lead.email;
                  const label = lead.companyName ? `${name} — ${lead.companyName}` : name;
                  return (
                    <option key={lead.id} value={lead.id}>
                      {label}
                    </option>
                  );
                })}
              </select>
            </div>
          )}

          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium">Titolo *</label>
            <Input
              id="title"
              name="title"
              required
              placeholder="Es. Chiamata di follow-up"
              defaultValue={task?.title}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="dueDate" className="text-sm font-medium">Scadenza *</label>
            <Input
              id="dueDate"
              name="dueDate"
              type="datetime-local"
              required
              defaultValue={task?.dueDate ? new Date(task.dueDate).toISOString().slice(0, 16) : ""}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium">Descrizione</label>
            <Textarea
              id="description"
              name="description"
              defaultValue={task?.description}
              rows={3}
              placeholder="Note aggiuntive…"
            />
          </div>

          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <SheetFooter className="mt-6 gap-2">
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Salvataggio…" : task ? "Aggiorna Task" : "Salva Task"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
