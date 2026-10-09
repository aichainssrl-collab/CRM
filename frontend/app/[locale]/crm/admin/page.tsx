"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useAuditLog, useAuditStats, useSystemStats,
} from "@/hooks/useAdmin";
import {
  Shield, Activity, Database, Users, Briefcase, Mail,
  FileText, CheckSquare, Calendar, ClipboardList, Globe,
} from "lucide-react";

const ACTION_LABELS: Record<string, string> = {
  create: "Creazione",
  update: "Aggiornamento",
  delete: "Eliminazione",
  soft_delete: "Soft Delete",
  login: "Login",
  export: "Export",
  enroll: "Iscrizione",
};

const ENTITY_LABELS: Record<string, string> = {
  lead: "Lead",
  deal: "Deal",
  task: "Task",
  user: "Utente",
  sequence: "Sequenza",
  report: "Report",
  booking: "Booking",
};

const ACTION_COLORS: Record<string, string> = {
  create: "bg-success/10 text-success",
  update: "bg-info/10 text-info",
  delete: "bg-destructive/10 text-destructive",
  soft_delete: "bg-destructive/10 text-destructive",
  login: "bg-muted text-muted-foreground",
  export: "bg-warning/10 text-warning",
};

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("it-IT", {
      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
    });
  } catch { return iso; }
}

function StatCard({ label, value, sub, icon: Icon, accent }: {
  label: string;
  value: number | string;
  sub?: string;
  icon: React.ElementType;
  accent: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-4">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${accent}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground truncate">{label}</p>
        <p className="text-xl font-bold tracking-tight">{value}</p>
        {sub && <p className="text-[10px] text-muted-foreground">{sub}</p>}
      </div>
    </div>
  );
}

export default function AdminPage() {
  const [tab, setTab] = useState<"overview" | "audit">("overview");
  const { data: stats, isLoading: statsLoading } = useSystemStats();
  const { data: auditEntries, isLoading: auditLoading } = useAuditLog({ limit: 50 });
  const { data: auditStats, isLoading: auditStatsLoading } = useAuditStats(30);

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Sistema & Audit</h1>
          <p className="text-sm text-muted-foreground">
            Panoramica sistema, statistiche e registro operazioni
          </p>
        </div>
        <Tabs value={tab} onValueChange={(v) => v && setTab(v as "overview" | "audit")}>
          <TabsList>
            <TabsTrigger value="overview">Panoramica</TabsTrigger>
            <TabsTrigger value="audit">Audit Log</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* ═══ Overview Tab ═══ */}
      {tab === "overview" && (
        <>
          {/* Entity Stats */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Lead Totali"
              value={statsLoading ? "—" : stats?.entities.leads.total ?? 0}
              sub={stats ? `+${stats.entities.leads.last7d} questa settimana` : ""}
              icon={Users}
              accent="bg-info-muted text-info"
            />
            <StatCard
              label="Deal Attivi"
              value={statsLoading ? "—" : stats?.entities.deals.active ?? 0}
              sub={stats ? `${stats.entities.deals.won} vinti` : ""}
              icon={Briefcase}
              accent="bg-success-muted text-success"
            />
            <StatCard
              label="Task Aperti"
              value={statsLoading ? "—" : stats?.entities.tasks.open ?? 0}
              sub={stats ? `${stats.entities.tasks.total} totali` : ""}
              icon={CheckSquare}
              accent="bg-warning-muted text-warning"
            />
            <StatCard
              label="Utenti Attivi"
              value={statsLoading ? "—" : stats?.entities.users.active ?? 0}
              sub={stats ? `${stats.entities.users.total} totali` : ""}
              icon={Shield}
              accent="bg-status-proposal-muted text-status-proposal"
            />
          </div>

          {/* More entities */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Email Inviate"
              value={statsLoading ? "—" : stats?.emails.sent ?? 0}
              sub={stats ? `${stats.emails.last30d} negli ultimi 30gg` : ""}
              icon={Mail}
              accent="bg-primary/10 text-primary"
            />
            <StatCard
              label="Sequenze Attive"
              value={statsLoading ? "—" : stats?.entities.emailSequences.active ?? 0}
              sub={stats ? `${stats.entities.emailSequences.total} totali` : ""}
              icon={Mail}
              accent="bg-chart-1/10 text-chart-1"
            />
            <StatCard
              label="Form Submissions"
              value={statsLoading ? "—" : stats?.entities.formSubmissions.total ?? 0}
              icon={FileText}
              accent="bg-chart-2/10 text-chart-2"
            />
            <StatCard
              label="Documenti DB"
              value={statsLoading ? "—" : stats?.database.totalDocuments ?? 0}
              sub={stats ? `${stats.database.collections} collezioni` : ""}
              icon={Database}
              accent="bg-chart-3/10 text-chart-3"
            />
          </div>

          {/* Audit Stats Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Attività Ultimi 30 Giorni</CardTitle>
              <CardDescription>Azioni registrate nel registro audit</CardDescription>
            </CardHeader>
            <CardContent>
              {auditStatsLoading ? (
                <Skeleton className="h-32 w-full rounded-lg" />
              ) : !auditStats || auditStats.total === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                  <Activity className="h-8 w-8 text-muted-foreground/30" />
                  <p className="text-sm">Nessuna attività registrata negli ultimi 30 giorni</p>
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-2">Azioni</p>
                    <div className="space-y-1.5">
                      {Object.entries(auditStats.byAction).map(([action, count]) => (
                        <div key={action} className="flex items-center justify-between text-sm">
                          <Badge variant="secondary" className={`text-[10px] ${ACTION_COLORS[action] || ""}`}>
                            {ACTION_LABELS[action] || action}
                          </Badge>
                          <span className="font-medium tabular-nums">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-2">Entità</p>
                    <div className="space-y-1.5">
                      {Object.entries(auditStats.byEntity).map(([entity, count]) => (
                        <div key={entity} className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">{ENTITY_LABELS[entity] || entity}</span>
                          <span className="font-medium tabular-nums">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* ═══ Audit Log Tab ═══ */}
      {tab === "audit" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Registro Operazioni</CardTitle>
            <CardDescription>Ultime 50 operazioni registrate</CardDescription>
          </CardHeader>
          <CardContent>
            {auditLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-14 w-full rounded-lg" />)}
              </div>
            ) : !auditEntries?.length ? (
              <div className="flex flex-col items-center justify-center py-12 gap-2 text-muted-foreground">
                <ClipboardList className="h-10 w-10 text-muted-foreground/30" />
                <p className="text-sm">Nessuna operazione registrata</p>
              </div>
            ) : (
              <div className="space-y-2">
                {auditEntries.map((entry) => (
                  <div key={entry.id} className="flex items-center gap-3 rounded-lg border bg-card p-3 hover:bg-muted/30 transition-colors">
                    <Badge variant="secondary" className={`text-[9px] shrink-0 ${ACTION_COLORS[entry.action] || ""}`}>
                      {ACTION_LABELS[entry.action] || entry.action}
                    </Badge>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm truncate">{entry.description || `${entry.action} ${ENTITY_LABELS[entry.entityType] || entry.entityType}`}</p>
                      <p className="text-[10px] text-muted-foreground">
                        <span className="font-medium">{entry.userName}</span> · {ENTITY_LABELS[entry.entityType] || entry.entityType}
                      </p>
                    </div>
                    <span className="text-[10px] text-muted-foreground shrink-0">{formatDate(entry.createdAt)}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}