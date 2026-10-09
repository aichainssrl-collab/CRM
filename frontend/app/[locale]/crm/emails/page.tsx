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
  useEmailSequences, useCreateEmailSequence,
  useUpdateEmailSequence, useDeleteEmailSequence,
  useToggleEmailSequence, useEnrollLead,
  useEnrollmentAction,
  type EmailSequence, type SequenceStep,
} from "@/hooks/useEmailSequences";
import { useLeads } from "@/hooks/useLeads";
import {
  Mail, Plus, Play, Pause, Trash2, MoreHorizontal,
  Users, Clock, CheckCircle2, XCircle, Send, Loader2,
  ChevronRight, ChevronDown, Edit, UserPlus,
} from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────
function formatDate(iso: string | null) {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric" }); }
  catch { return iso; }
}

const STATUS_STYLES: Record<string, string> = {
  active: "bg-success/10 text-success",
  paused: "bg-warning/10 text-warning",
  completed: "bg-info/10 text-info",
  unsubscribed: "bg-destructive/10 text-destructive",
};

const STATUS_LABELS: Record<string, string> = {
  active: "Attiva",
  paused: "In pausa",
  completed: "Completata",
  unsubscribed: "Disiscritto",
};

// ── Step Editor Row ───────────────────────────────────────────
function StepEditor({ step, index, onChange, onRemove }: {
  step: SequenceStep;
  index: number;
  onChange: (s: SequenceStep) => void;
  onRemove: () => void;
}) {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
            {index + 1}
          </div>
          <span className="text-sm font-medium">Step {index + 1}</span>
        </div>
        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={onRemove}>
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
      <div className="grid gap-3 sm:grid-cols-[1fr_120px]">
        <div className="space-y-1">
          <Label className="text-xs">Oggetto</Label>
          <Input
            value={step.subject}
            onChange={(e) => onChange({ ...step, subject: e.target.value })}
            placeholder="Oggetto email..."
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Ritardo (gg)</Label>
          <Input
            type="number"
            min={0}
            max={365}
            value={step.delayDays}
            onChange={(e) => onChange({ ...step, delayDays: parseInt(e.target.value) || 0 })}
          />
        </div>
      </div>
      <div className="space-y-1">
        <Label className="text-xs">Corpo HTML</Label>
        <Textarea
          value={step.bodyHtml}
          onChange={(e) => onChange({ ...step, bodyHtml: e.target.value })}
          rows={4}
          placeholder="<p>Ciao {firstName},...</p>"
          className="font-mono text-xs"
        />
      </div>
    </div>
  );
}

// ── Sequence Card ─────────────────────────────────────────────
function SequenceCard({ seq, onEdit, onDelete, onToggle, onEnroll }: {
  seq: EmailSequence;
  onEdit: () => void;
  onDelete: () => void;
  onToggle: (active: boolean) => void;
  onEnroll: () => void;
}) {
  const [showEnrollments, setShowEnrollments] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const enrollAction = useEnrollmentAction();
  const stats = seq.stats;

  return (
    <Card>
      <CardContent className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-base truncate">{seq.name}</h3>
              <Badge variant={seq.isActive ? "default" : "secondary"} className="text-[10px] shrink-0">
                {seq.isActive ? "Attiva" : "Inattiva"}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5 line-clamp-1">{seq.description}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Mail className="h-3 w-3" /> {seq.steps.length} step
              </span>
              <span className="flex items-center gap-1">
                <Users className="h-3 w-3" /> {stats?.total ?? seq.enrollments?.length ?? 0} iscritti
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" /> {formatDate(seq.createdAt)}
              </span>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" />}>
              <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onEnroll}>
                <UserPlus className="mr-2 h-4 w-4" />
                Iscrivi Lead
              </DropdownMenuItem>
              <DropdownMenuItem onClick={onEdit}>
                <Edit className="mr-2 h-4 w-4" />
                Modifica
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => onToggle(!seq.isActive)}>
                {seq.isActive ? <Pause className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
                {seq.isActive ? "Disattiva" : "Attiva"}
              </DropdownMenuItem>
              {!confirmDelete ? (
                <DropdownMenuItem variant="destructive" onClick={() => setConfirmDelete(true)}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Elimina
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem variant="destructive" onClick={() => { onDelete(); setConfirmDelete(false); }}>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Conferma eliminazione
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Stats bar */}
        {stats && stats.total > 0 && (
          <div className="mt-4 flex gap-2">
            <div className="flex-1 rounded-md bg-success/10 px-3 py-2 text-center">
              <p className="text-lg font-bold text-success">{stats.active}</p>
              <p className="text-[10px] text-muted-foreground">Attivi</p>
            </div>
            <div className="flex-1 rounded-md bg-info/10 px-3 py-2 text-center">
              <p className="text-lg font-bold text-info">{stats.completed}</p>
              <p className="text-[10px] text-muted-foreground">Completati</p>
            </div>
            <div className="flex-1 rounded-md bg-warning/10 px-3 py-2 text-center">
              <p className="text-lg font-bold text-warning">{stats.paused}</p>
              <p className="text-[10px] text-muted-foreground">In pausa</p>
            </div>
            <div className="flex-1 rounded-md bg-muted px-3 py-2 text-center">
              <p className="text-lg font-bold">{stats.completionRate}%</p>
              <p className="text-[10px] text-muted-foreground">Tasso</p>
            </div>
          </div>
        )}

        {/* Steps preview */}
        <div className="mt-4 flex items-center gap-1">
          {seq.steps.map((step, i) => (
            <div key={i} className="flex items-center">
              <div className="flex h-6 items-center rounded-full bg-primary/10 px-2 text-[10px] font-medium text-primary">
                {i + 1}
                {step.delayDays > 0 && (
                  <span className="ml-1 text-muted-foreground">+{step.delayDays}g</span>
                )}
              </div>
              {i < seq.steps.length - 1 && <ChevronRight className="h-3 w-3 text-muted-foreground/40 mx-0.5" />}
            </div>
          ))}
        </div>

        {/* Enrollments toggle */}
        {seq.enrollments && seq.enrollments.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowEnrollments(!showEnrollments)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {showEnrollments ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              {seq.enrollments.length} iscrizioni
            </button>
            {showEnrollments && (
              <div className="mt-2 space-y-1.5 max-h-48 overflow-y-auto">
                {seq.enrollments.map((en) => (
                  <div key={en.id} className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-[10px] font-bold">
                      {en.leadName?.charAt(0).toUpperCase() || "?"}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium">{en.leadName || en.leadEmail}</p>
                      <p className="text-[10px] text-muted-foreground">
                        Step {en.currentStep + 1}/{seq.steps.length}
                      </p>
                    </div>
                    <Badge className={`text-[9px] ${STATUS_STYLES[en.status] || ""}`} variant="secondary">
                      {STATUS_LABELS[en.status] || en.status}
                    </Badge>
                    {en.status === "active" && (
                      <div className="flex gap-0.5">
                        <Button variant="ghost" size="icon" className="h-6 w-6" title="Avanza step"
                          onClick={() => enrollAction.mutate({ sequenceId: seq.id, enrollmentId: en.id, action: "advance" })}>
                          <Send className="h-3 w-3" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-6 w-6" title="Pausa"
                          onClick={() => enrollAction.mutate({ sequenceId: seq.id, enrollmentId: en.id, action: "pause" })}>
                          <Pause className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                    {en.status === "paused" && (
                      <Button variant="ghost" size="icon" className="h-6 w-6" title="Riprendi"
                        onClick={() => enrollAction.mutate({ sequenceId: seq.id, enrollmentId: en.id, action: "resume" })}>
                        <Play className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function EmailSequencesPage() {
  const t = useTranslations("emailSequences");
  const { data: sequences, isLoading } = useEmailSequences();
  const createSeq = useCreateEmailSequence();
  const updateSeq = useUpdateEmailSequence();
  const deleteSeq = useDeleteEmailSequence();
  const toggleSeq = useToggleEmailSequence();
  const enrollLead = useEnrollLead();

  // Create/Edit dialog
  const [editOpen, setEditOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [steps, setSteps] = useState<SequenceStep[]>([
    { subject: "", bodyHtml: "", delayDays: 0 },
  ]);

  // Enroll dialog
  const [enrollOpen, setEnrollOpen] = useState(false);
  const [enrollSeqId, setEnrollSeqId] = useState<string | null>(null);
  const [enrollLeadId, setEnrollLeadId] = useState("");
  const { data: leads = [] } = useLeads({ limit: 200 });

  function openCreate() {
    setEditingId(null);
    setName("");
    setDesc("");
    setSteps([{ subject: "", bodyHtml: "", delayDays: 0 }]);
    setEditOpen(true);
  }

  function openEdit(seq: EmailSequence) {
    setEditingId(seq.id);
    setName(seq.name);
    setDesc(seq.description);
    setSteps(seq.steps.map(s => ({ ...s })));
    setEditOpen(true);
  }

  function addStep() {
    setSteps(prev => [...prev, { subject: "", bodyHtml: "", delayDays: 3 }]);
  }

  function removeStep(index: number) {
    setSteps(prev => prev.filter((_, i) => i !== index));
  }

  function updateStep(index: number, step: SequenceStep) {
    setSteps(prev => prev.map((s, i) => i === index ? step : s));
  }

  async function handleSave() {
    const data = { name, description: desc, steps };
    if (editingId) {
      await updateSeq.mutateAsync({ id: editingId, data });
    } else {
      await createSeq.mutateAsync(data);
    }
    setEditOpen(false);
  }

  async function handleEnroll() {
    if (!enrollSeqId || !enrollLeadId) return;
    await enrollLead.mutateAsync({ sequenceId: enrollSeqId, leadId: enrollLeadId });
    setEnrollOpen(false);
    setEnrollLeadId("");
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Email Sequences</h1>
          <p className="text-sm text-muted-foreground">
            Drip campaign automatiche — crea, attiva e monitora le tue sequenze email
          </p>
        </div>
        <Button size="sm" className="gap-1.5" onClick={openCreate}>
          <Plus className="h-3.5 w-3.5" />
          Nuova Sequenza
        </Button>
      </div>

      {/* Sequences list */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-48 w-full rounded-xl" />)}
        </div>
      ) : !sequences?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-4">
            <Mail className="h-12 w-12 text-muted-foreground/25" />
            <div className="text-center">
              <p className="text-lg font-medium">Nessuna sequenza email</p>
              <p className="text-sm text-muted-foreground mt-1">
                Crea la tua prima drip campaign per automatizzare il nurturing dei lead
              </p>
            </div>
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4 mr-1.5" />
              Crea Prima Sequenza
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {sequences.map((seq) => (
            <SequenceCard
              key={seq.id}
              seq={seq}
              onEdit={() => openEdit(seq)}
              onDelete={() => deleteSeq.mutate(seq.id)}
              onToggle={(active) => toggleSeq.mutate({ id: seq.id, active })}
              onEnroll={() => { setEnrollSeqId(seq.id); setEnrollOpen(true); }}
            />
          ))}
        </div>
      )}

      {/* ── Create/Edit Dialog ── */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingId ? "Modifica Sequenza" : "Nuova Sequenza"}</DialogTitle>
            <DialogDescription>
              Configura i passaggi email. Usa {"{firstName}"} e {"{company}"} per personalizzare.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Nome</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Es. Welcome Playbook" />
            </div>
            <div className="space-y-2">
              <Label>Descrizione</Label>
              <Input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Descrizione opzionale" />
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Email Steps</Label>
                <Button variant="outline" size="sm" onClick={addStep}>
                  <Plus className="h-3 w-3 mr-1" /> Step
                </Button>
              </div>
              {steps.map((step, i) => (
                <StepEditor
                  key={i}
                  step={step}
                  index={i}
                  onChange={(s) => updateStep(i, s)}
                  onRemove={() => removeStep(i)}
                />
              ))}
              {steps.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Nessuno step. Aggiungi almeno un'email.
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)}>Annulla</Button>
            <Button onClick={handleSave} disabled={!name || steps.length === 0 || createSeq.isPending || updateSeq.isPending}>
              {(createSeq.isPending || updateSeq.isPending) && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Salva
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Enroll Dialog ── */}
      <Dialog open={enrollOpen} onOpenChange={setEnrollOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Iscrivi Lead alla Sequenza</DialogTitle>
            <DialogDescription>
              Il lead riceverà le email della sequenza secondo i ritardi configurati
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Seleziona Lead</Label>
            <select
              value={enrollLeadId}
              onChange={(e) => setEnrollLeadId(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">— Seleziona un lead —</option>
              {leads.map((lead) => (
                <option key={lead.id} value={lead.id}>
                  {lead.firstName} {lead.lastName} ({lead.email})
                </option>
              ))}
            </select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEnrollOpen(false)}>Annulla</Button>
            <Button onClick={handleEnroll} disabled={!enrollLeadId || enrollLead.isPending}>
              {enrollLead.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <UserPlus className="h-4 w-4 mr-2" />}
              Iscrivi
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}