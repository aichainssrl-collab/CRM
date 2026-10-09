"use client";

import { useState, useMemo } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area,
  PieChart, Pie, Cell,
  ResponsiveContainer,
} from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useDashboardMetrics } from "@/hooks/useDashboard";
import { useLeads } from "@/hooks/useLeads";
import { useDeals } from "@/hooks/useDeals";
import {
  useReports, useGenerateReport, useDeleteReport, useSendReport,
  type ReportSummary,
} from "@/hooks/useReports";
import {
  Users, Briefcase, Target, UserPlus, BarChart3,
  FileText, Download, Mail, MoreHorizontal, Trash2,
  Plus, Clock, Loader2, CheckCircle2, Send,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { KpiCard } from "@/components/crm/KpiCard";
import { formatEUR } from "@/lib/format";

// ── Source label mapping ──────────────────────────────────────
const SOURCE_LABELS: Record<string, string> = {
  excel_import: "Excel Import",
  csv_import: "CSV Import",
  direct: "Direct",
  playbook: "Playbook",
  contact: "Contact Form",
  booking: "Booking",
  assessment: "Assessment",
  meta_ads: "Meta Ads",
  referral: "Referral",
  linkedin: "LinkedIn",
};

function sourceLabel(src: string): string {
  return SOURCE_LABELS[src] || src.charAt(0).toUpperCase() + src.slice(1).replace(/_/g, " ");
}

const STAGE_LABELS: Record<string, string> = {
  new: "New", contacted: "Contacted", qualified: "Qualified",
  proposal: "Proposal", negotiation: "Negotiation", won: "Won", lost: "Lost",
};
const STAGE_COLORS: Record<string, string> = {
  new: "var(--stage-new)", contacted: "var(--stage-contacted)", qualified: "var(--stage-qualified)",
  proposal: "var(--stage-proposal)", negotiation: "var(--stage-negotiation)",
  won: "var(--stage-won)", lost: "var(--stage-lost)",
};

const PIE_COLORS = [
  "var(--chart-1)", "var(--chart-2)", "var(--chart-3)",
  "var(--chart-4)", "var(--chart-5)",
  "var(--primary)", "var(--stage-qualified)", "var(--stage-contacted)",
];
const SCORE_BUCKETS = ["0-20", "21-40", "41-60", "61-80", "81-100"];
const SCORE_COLORS = ["var(--stage-lost)", "var(--stage-negotiation)", "var(--warning)", "var(--stage-won)", "var(--success)"];

const sourceChartConfig: ChartConfig = { count: { label: "Leads", color: "var(--chart-1)" } };
const stageChartConfig: ChartConfig = { value: { label: "Valore (EUR)", color: "var(--chart-2)" } };
const scoreChartConfig: ChartConfig = { count: { label: "Leads", color: "var(--chart-3)" } };
const industryChartConfig: ChartConfig = { count: { label: "Leads", color: "var(--chart-4)" } };

function ChartSkeleton() { return <Skeleton className="w-full h-[260px] rounded-lg" />; }
function EmptyChart({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[260px] gap-2 text-muted-foreground">
      <BarChart3 className="h-8 w-8 text-muted-foreground/30" />
      <p className="text-sm text-muted-foreground/60">{message}</p>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function renderPieLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }: Record<string, any>) {
  if (percent < 0.05) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 1.4;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="var(--foreground)" textAnchor={x > cx ? "start" : "end"} dominantBaseline="central" className="text-[11px]">
      {name} ({(percent * 100).toFixed(0)}%)
    </text>
  );
}

function formatDate(iso: string) {
  try { return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }); }
  catch { return iso; }
}

// ── Main Page ─────────────────────────────────────────────────
export default function ReportsPage() {
  const t = useTranslations("reports");
  const tTime = useTranslations("timeRanges");
  const [timeRange, setTimeRange] = useState("30d");
  const [tab, setTab] = useState<"charts" | "history">("charts");

  // Charts data
  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics(timeRange);
  const { data: leads, isLoading: leadsLoading } = useLeads({ limit: 500 });
  const { data: deals, isLoading: dealsLoading } = useDeals({ limit: 100 });

  // Reports data
  const { data: reportsList, isLoading: reportsLoading } = useReports(50);
  const generateReport = useGenerateReport();
  const deleteReport = useDeleteReport();
  const sendReport = useSendReport();

  // Generate dialog state
  const [genOpen, setGenOpen] = useState(false);
  const [genTitle, setGenTitle] = useState(`Report ${new Date().toLocaleDateString("it-IT")}`);
  const [genRange, setGenRange] = useState("30d");
  const [genOptions, setGenOptions] = useState({
    funnel: true, velocity: true, performance: true, forecast: true,
  });

  // Email dialog state
  const [emailOpen, setEmailOpen] = useState(false);
  const [emailReportId, setEmailReportId] = useState<string | null>(null);
  const [emailTo, setEmailTo] = useState("");
  const [emailMsg, setEmailMsg] = useState("");

  const TIME_RANGES = [
    { label: tTime("7d"), value: "7d" },
    { label: tTime("30d"), value: "30d" },
    { label: tTime("90d"), value: "90d" },
  ];

  // ── Chart data ──
  const sourceData = useMemo(() => {
    if (!leads?.length) return [];
    const counts: Record<string, number> = {};
    for (const lead of leads) { counts[lead.source ?? "direct"] = (counts[lead.source ?? "direct"] ?? 0) + 1; }
    return Object.entries(counts).map(([source, count]) => ({ source: sourceLabel(source), count, _raw: source })).sort((a, b) => b.count - a.count).slice(0, 8);
  }, [leads]);

  const stageData = useMemo(() => {
    if (!deals?.length) return [];
    const totals: Record<string, number> = {};
    for (const deal of deals) { totals[deal.stage] = (totals[deal.stage] ?? 0) + (deal.value ?? 0); }
    return Object.entries(totals).map(([stage, value]) => ({
      stage: STAGE_LABELS[stage] || stage, value,
      fill: STAGE_COLORS[stage] || "var(--stage-new)",
    })).sort((a, b) => b.value - a.value);
  }, [deals]);

  const scoreData = useMemo(() => {
    if (!leads?.length) return [];
    const buckets: Record<string, number> = { "0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0 };
    for (const lead of leads) {
      const s = lead.leadScore ?? 0;
      if (s <= 20) buckets["0-20"]++;
      else if (s <= 40) buckets["21-40"]++;
      else if (s <= 60) buckets["41-60"]++;
      else if (s <= 80) buckets["61-80"]++;
      else buckets["81-100"]++;
    }
    return SCORE_BUCKETS.map((range, i) => ({ range, count: buckets[range], fill: SCORE_COLORS[i] }));
  }, [leads]);

  const industryData = useMemo(() => {
    if (!leads?.length) return [];
    const counts: Record<string, number> = {};
    for (const lead of leads) { if (lead.industry) counts[lead.industry] = (counts[lead.industry] ?? 0) + 1; }
    return Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 8);
  }, [leads]);

  const totalLeadsWithIndustry = useMemo(() => leads?.filter(l => l.industry).length ?? 0, [leads]);

  const dash = (v: number | undefined, format?: (n: number) => string) => {
    if (metricsLoading || v === undefined) return "\u2014";
    return format ? format(v) : v.toLocaleString("it-IT");
  };

  // ── Handlers ──
  async function handleGenerate() {
    await generateReport.mutateAsync({
      title: genTitle,
      timeRange: genRange,
      includeFunnel: genOptions.funnel,
      includeVelocity: genOptions.velocity,
      includePerformance: genOptions.performance,
      includeForecast: genOptions.forecast,
    });
    setGenOpen(false);
    setTab("history");
  }

  async function handleSendEmail() {
    if (!emailReportId || !emailTo) return;
    await sendReport.mutateAsync({ id: emailReportId, to: emailTo, message: emailMsg || undefined });
    setEmailOpen(false);
    setEmailTo("");
    setEmailMsg("");
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>
        <div className="flex items-center gap-3">
          <Tabs value={tab} onValueChange={(v) => v && setTab(v as "charts" | "history")}>
            <TabsList>
              <TabsTrigger value="charts">Grafici</TabsTrigger>
              <TabsTrigger value="history">Report Salvati</TabsTrigger>
            </TabsList>
          </Tabs>
          <Button size="sm" className="gap-1.5" onClick={() => setGenOpen(true)}>
            <Plus className="h-3.5 w-3.5" />
            Genera Report
          </Button>
          <Dialog open={genOpen} onOpenChange={setGenOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Genera Report</DialogTitle>
                <DialogDescription>
                  Crea uno snapshot completo delle analytics del tuo CRM
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-2">
                <div className="space-y-2">
                  <Label>Titolo</Label>
                  <Input value={genTitle} onChange={(e) => setGenTitle(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Periodo</Label>
                  <Tabs value={genRange} onValueChange={(v) => v && setGenRange(v)}>
                    <TabsList>
                      <TabsTrigger value="7d">7 giorni</TabsTrigger>
                      <TabsTrigger value="30d">30 giorni</TabsTrigger>
                      <TabsTrigger value="90d">90 giorni</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
                <div className="space-y-3">
                  <Label>Includi sezioni</Label>
                  {(["funnel", "velocity", "performance", "forecast"] as const).map((key) => (
                    <div key={key} className="flex items-center gap-2">
                      <Checkbox
                        checked={genOptions[key]}
                        onCheckedChange={(checked) =>
                          setGenOptions((prev) => ({ ...prev, [key]: !!checked }))
                        }
                      />
                      <span className="text-sm capitalize">{key === "funnel" ? "Funnel conversioni" : key === "velocity" ? "Pipeline velocity" : key === "performance" ? "Performance team" : "Forecast ponderato"}</span>
                    </div>
                  ))}
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setGenOpen(false)}>Annulla</Button>
                <Button onClick={handleGenerate} disabled={generateReport.isPending}>
                  {generateReport.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Genera
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* ═══ Charts Tab ═══ */}
      {tab === "charts" && (
        <>
          {/* KPI Cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard title={t("totalLeads")} value={dash(metrics?.totalLeads)} icon={Users} loading={metricsLoading} accent="bg-status-proposal-muted text-status-proposal" />
            <KpiCard title={t("newLeads")} value={dash(metrics?.newLeads)} icon={UserPlus} loading={metricsLoading} accent="bg-info-muted text-info" />
            <KpiCard title={t("activeDeals")} value={dash(metrics?.activeDeals)} icon={Briefcase} loading={metricsLoading} accent="bg-success-muted text-success" />
            <KpiCard title={t("conversionRate")} value={metricsLoading || metrics?.conversionRate === undefined ? "\u2014" : `${metrics.conversionRate}%`} icon={Target} loading={metricsLoading} accent="bg-warning-muted text-warning" />
          </div>

          {/* Row 1: Source + Industry */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t("leadsPerSource")}</CardTitle>
                <CardDescription>{t("acquisitionChannels")}</CardDescription>
              </CardHeader>
              <CardContent>
                {leadsLoading ? <ChartSkeleton /> : sourceData.length === 0 ? <EmptyChart message={t("noData")} /> : (
                  <ChartContainer config={sourceChartConfig} className="w-full h-[260px]">
                    <BarChart data={sourceData} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} className="stroke-muted/50" />
                      <XAxis type="number" tickLine={false} axisLine={false} className="text-xs text-muted-foreground" />
                      <YAxis type="category" dataKey="source" tickLine={false} axisLine={false} width={100} className="text-xs text-muted-foreground" />
                      <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: "var(--muted)", opacity: 0.3 }} />
                      <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={28}>
                        {sourceData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ChartContainer>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t("sectorDistribution")}</CardTitle>
                <CardDescription>{t("leadsWithSector", { count: totalLeadsWithIndustry })}</CardDescription>
              </CardHeader>
              <CardContent>
                {leadsLoading ? <ChartSkeleton /> : industryData.length === 0 ? <EmptyChart message={t("noSector")} /> : (
                  <ChartContainer config={industryChartConfig} className="w-full h-[260px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Pie data={industryData} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={85} innerRadius={45} paddingAngle={2} label={renderPieLabel} labelLine={false}>
                          {industryData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Row 2: Pipeline stages + Score distribution */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t("pipelinePerStage")}</CardTitle>
                <CardDescription>{t("pipelineValueDesc")}</CardDescription>
              </CardHeader>
              <CardContent>
                {dealsLoading ? <ChartSkeleton /> : stageData.length === 0 ? <EmptyChart message={t("noData")} /> : (
                  <ChartContainer config={stageChartConfig} className="w-full h-[260px]">
                    <BarChart data={stageData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted/50" />
                      <XAxis dataKey="stage" tickLine={false} axisLine={false} tickMargin={8} className="text-xs text-muted-foreground" />
                      <YAxis tickLine={false} axisLine={false} className="text-xs text-muted-foreground" width={55} tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)} />
                      <ChartTooltip content={<ChartTooltipContent formatter={(value) => [formatEUR(value as number), "Valore"]} />} cursor={{ fill: "var(--muted)", opacity: 0.3 }} />
                      <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={48}>
                        {stageData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                      </Bar>
                    </BarChart>
                  </ChartContainer>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t("scoreDistribution")}</CardTitle>
                <CardDescription>{t("scoreQuality")}</CardDescription>
              </CardHeader>
              <CardContent>
                {leadsLoading ? <ChartSkeleton /> : (leads?.length ?? 0) === 0 ? <EmptyChart message={t("noData")} /> : (
                  <ChartContainer config={scoreChartConfig} className="w-full h-[260px]">
                    <AreaChart data={scoreData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--chart-3)" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="var(--chart-3)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted/50" />
                      <XAxis dataKey="range" tickLine={false} axisLine={false} tickMargin={8} className="text-xs text-muted-foreground" />
                      <YAxis tickLine={false} axisLine={false} className="text-xs text-muted-foreground" width={30} />
                      <ChartTooltip content={<ChartTooltipContent />} cursor={{ stroke: "var(--chart-3)", strokeWidth: 1, strokeDasharray: "4 4" }} />
                      <Area type="monotone" dataKey="count" stroke="var(--chart-3)" strokeWidth={2} fill="url(#scoreGradient)" />
                      {scoreData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </AreaChart>
                  </ChartContainer>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* ═══ History Tab ═══ */}
      {tab === "history" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Report Generati</CardTitle>
            <CardDescription>Snapshot salvati delle analytics CRM</CardDescription>
          </CardHeader>
          <CardContent>
            {reportsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}
              </div>
            ) : !reportsList?.length ? (
              <div className="flex flex-col items-center justify-center py-12 gap-3 text-muted-foreground">
                <FileText className="h-10 w-10 text-muted-foreground/30" />
                <p className="text-sm">Nessun report generato ancora.</p>
                <Button variant="outline" size="sm" onClick={() => setGenOpen(true)}>
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  Genera il primo report
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {reportsList.map((report) => (
                  <ReportRow
                    key={report.id}
                    report={report}
                    onDelete={() => deleteReport.mutate(report.id)}
                    onEmail={() => { setEmailReportId(report.id); setEmailOpen(true); }}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ═══ Email Dialog ═══ */}
      <Dialog open={emailOpen} onOpenChange={setEmailOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invia Report via Email</DialogTitle>
            <DialogDescription>Il report verrà inviato con i KPI e le sezioni incluse</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label>Destinatario</Label>
              <Input type="email" value={emailTo} onChange={(e) => setEmailTo(e.target.value)} placeholder="email@esempio.it" />
            </div>
            <div className="space-y-2">
              <Label>Messaggio (opzionale)</Label>
              <Input value={emailMsg} onChange={(e) => setEmailMsg(e.target.value)} placeholder="Messaggio da includere nell'email..." />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEmailOpen(false)}>Annulla</Button>
            <Button onClick={handleSendEmail} disabled={!emailTo || sendReport.isPending}>
              {sendReport.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
              Invia
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Report Row Component ──────────────────────────────────────
function ReportRow({ report, onDelete, onEmail }: {
  report: ReportSummary;
  onDelete: () => void;
  onEmail: () => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <div className="flex items-center gap-3 rounded-lg border bg-card p-4 hover:bg-muted/30 transition-colors">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
        <FileText className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{report.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatDate(report.createdAt)}
          </span>
          <Badge variant="secondary" className="text-[10px]">{report.timeRange}</Badge>
          <span className="text-xs text-muted-foreground">di {report.generatedByName}</span>
        </div>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onEmail} title="Invia email">
          <Mail className="h-4 w-4 text-muted-foreground" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="h-8 w-8" />}>
            <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={onEmail}>
              <Mail className="mr-2 h-4 w-4" />
              Invia via email
            </DropdownMenuItem>
            {!confirmDelete ? (
              <DropdownMenuItem onClick={() => setConfirmDelete(true)} variant="destructive">
                <Trash2 className="mr-2 h-4 w-4" />
                Elimina
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem
                onClick={() => { onDelete(); setConfirmDelete(false); }}
                variant="destructive"
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Conferma eliminazione
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}