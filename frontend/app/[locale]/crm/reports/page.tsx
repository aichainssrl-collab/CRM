"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
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
import { useDashboardMetrics } from "@/hooks/useDashboard";
import { useLeads } from "@/hooks/useLeads";
import { useDeals } from "@/hooks/useDeals";
import { Users, Briefcase, Target, UserPlus, BarChart3 } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const TIME_RANGES = [
  { label: "7 giorni", value: "7d" },
  { label: "30 giorni", value: "30d" },
  { label: "90 giorni", value: "90d" },
];

function formatEUR(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency", currency: "EUR", maximumFractionDigits: 0,
  }).format(value);
}

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

// ── Stage label mapping ──────────────────────────────────────
const STAGE_LABELS: Record<string, string> = {
  new: "New",
  contacted: "Contacted",
  qualified: "Qualified",
  proposal: "Proposal",
  negotiation: "Negotiation",
  won: "Won",
  lost: "Lost",
};
const STAGE_COLORS: Record<string, string> = {
  new: "#94a3b8",
  contacted: "#60a5fa",
  qualified: "#818cf8",
  proposal: "#a78bfa",
  negotiation: "#f59e0b",
  won: "#22c55e",
  lost: "#ef4444",
};

// ── Pie colors ───────────────────────────────────────────────
const PIE_COLORS = ["#1d3173", "#3b5bdb", "#5c7cfa", "#748ffc", "#91a7ff", "#bac8ff", "#dbe4ff", "#e7ecff"];

// ── Score gradient buckets ───────────────────────────────────
const SCORE_BUCKETS = ["0-20", "21-40", "41-60", "61-80", "81-100"];
const SCORE_COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#15803d"];

// ── Chart configs ────────────────────────────────────────────
const sourceChartConfig: ChartConfig = {
  count: { label: "Leads", color: "var(--chart-1)" },
};
const stageChartConfig: ChartConfig = {
  value: { label: "Valore (EUR)", color: "var(--chart-2)" },
};
const scoreChartConfig: ChartConfig = {
  count: { label: "Leads", color: "var(--chart-3)" },
};
const industryChartConfig: ChartConfig = {
  count: { label: "Leads", color: "var(--chart-4)" },
};

// ── Shared components ────────────────────────────────────────
function ChartSkeleton() {
  return <Skeleton className="w-full h-[260px] rounded-lg" />;
}

function EmptyChart({ message = "Nessun dato disponibile" }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[260px] gap-2 text-muted-foreground">
      <BarChart3 className="h-8 w-8 text-muted-foreground/30" />
      <p className="text-sm text-muted-foreground/60">{message}</p>
    </div>
  );
}

function KpiCard({
  title, value, icon: Icon, loading, accent,
}: {
  title: string; value: string; icon: React.ElementType; loading: boolean; accent?: string;
}) {
  return (
    <Card className="group relative overflow-hidden transition-shadow duration-200 hover:shadow-md hover:shadow-primary/5">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-[13px] font-medium text-muted-foreground">{title}</CardTitle>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${accent ?? "bg-primary/8 text-primary"}`}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? <Skeleton className="h-8 w-24" /> : <div className="text-2xl font-bold tracking-tight">{value}</div>}
      </CardContent>
      <div className={`absolute bottom-0 left-0 h-0.5 w-full opacity-0 transition-opacity duration-200 group-hover:opacity-100 ${accent ?? "bg-primary"}`} />
    </Card>
  );
}

// ── Custom pie label ─────────────────────────────────────────
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

// ── Main Page ────────────────────────────────────────────────
export default function ReportsPage() {
  const [timeRange, setTimeRange] = useState("30d");

  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics(timeRange);
  const { data: leads, isLoading: leadsLoading } = useLeads({ limit: 500 });
  const { data: deals, isLoading: dealsLoading } = useDeals({ limit: 100 });

  // ── Source data with translated labels ──
  const sourceData = useMemo(() => {
    if (!leads?.length) return [];
    const counts: Record<string, number> = {};
    for (const lead of leads) {
      const src = lead.source ?? "direct";
      counts[src] = (counts[src] ?? 0) + 1;
    }
    return Object.entries(counts)
      .map(([source, count]) => ({ source: sourceLabel(source), count, _raw: source }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [leads]);

  // ── Stage data with colors ──
  const stageData = useMemo(() => {
    if (!deals?.length) return [];
    const totals: Record<string, number> = {};
    for (const deal of deals) {
      totals[deal.stage] = (totals[deal.stage] ?? 0) + (deal.value ?? 0);
    }
    return Object.entries(totals)
      .map(([stage, value]) => ({
        stage: STAGE_LABELS[stage] || stage,
        value,
        fill: STAGE_COLORS[stage] || "#94a3b8",
      }))
      .sort((a, b) => b.value - a.value);
  }, [deals]);

  // ── Score distribution ──
  const scoreData = useMemo(() => {
    if (!leads?.length) return [];
    const buckets: Record<string, number> = {
      "0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0,
    };
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

  // ── Industry breakdown ──
  const industryData = useMemo(() => {
    if (!leads?.length) return [];
    const counts: Record<string, number> = {};
    for (const lead of leads) {
      const ind = lead.industry || null;
      if (ind) counts[ind] = (counts[ind] ?? 0) + 1;
    }
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);
  }, [leads]);

  const dash = (v: number | undefined, format?: (n: number) => string) => {
    if (metricsLoading || v === undefined) return "\u2014";
    return format ? format(v) : v.toLocaleString("it-IT");
  };

  const totalLeadsWithIndustry = useMemo(() =>
    leads?.filter(l => l.industry).length ?? 0, [leads]);

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Reports & Analytics</h1>
          <p className="text-sm text-muted-foreground">Analisi delle performance commerciali</p>
        </div>
        <Tabs value={timeRange} onValueChange={(v) => v && setTimeRange(v)}>
          <TabsList>
            {TIME_RANGES.map((r) => (
              <TabsTrigger key={r.value} value={r.value}>{r.label}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Lead Totali" value={dash(metrics?.totalLeads)} icon={Users} loading={metricsLoading} accent="bg-violet-500/10 text-violet-600" />
        <KpiCard title="Nuovi Lead" value={dash(metrics?.newLeads)} icon={UserPlus} loading={metricsLoading} accent="bg-blue-500/10 text-blue-600" />
        <KpiCard title="Deal Attivi" value={dash(metrics?.activeDeals)} icon={Briefcase} loading={metricsLoading} accent="bg-emerald-500/10 text-emerald-600" />
        <KpiCard title="Tasso Conversione" value={metricsLoading || metrics?.conversionRate === undefined ? "\u2014" : `${metrics.conversionRate}%`} icon={Target} loading={metricsLoading} accent="bg-amber-500/10 text-amber-600" />
      </div>

      {/* Row 1: Source + Industry */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Leads per Source — horizontal bar */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Leads per Fonte</CardTitle>
            <CardDescription>Canali di acquisizione principali</CardDescription>
          </CardHeader>
          <CardContent>
            {leadsLoading ? <ChartSkeleton /> : sourceData.length === 0 ? <EmptyChart /> : (
              <ChartContainer config={sourceChartConfig} className="w-full h-[260px]">
                <BarChart data={sourceData} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} className="stroke-muted/50" />
                  <XAxis type="number" tickLine={false} axisLine={false} className="text-xs text-muted-foreground" />
                  <YAxis type="category" dataKey="source" tickLine={false} axisLine={false} width={100} className="text-xs text-muted-foreground" />
                  <ChartTooltip content={<ChartTooltipContent />} cursor={{ fill: "var(--muted)", opacity: 0.3 }} />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={28}>
                    {sourceData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        {/* Industry donut */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Distribuzione Settore</CardTitle>
            <CardDescription>
              {totalLeadsWithIndustry} lead con settore assegnato
            </CardDescription>
          </CardHeader>
          <CardContent>
            {leadsLoading ? <ChartSkeleton /> : industryData.length === 0 ? <EmptyChart message="Nessun settore assegnato" /> : (
              <ChartContainer config={industryChartConfig} className="w-full h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Pie
                      data={industryData}
                      dataKey="count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={85}
                      innerRadius={45}
                      paddingAngle={2}
                      label={renderPieLabel}
                      labelLine={false}
                    >
                      {industryData.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
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
        {/* Pipeline per stage — colored bars */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Pipeline per Stage</CardTitle>
            <CardDescription>Valore totale deal per fase di vendita</CardDescription>
          </CardHeader>
          <CardContent>
            {dealsLoading ? <ChartSkeleton /> : stageData.length === 0 ? <EmptyChart /> : (
              <ChartContainer config={stageChartConfig} className="w-full h-[260px]">
                <BarChart data={stageData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted/50" />
                  <XAxis dataKey="stage" tickLine={false} axisLine={false} tickMargin={8} className="text-xs text-muted-foreground" />
                  <YAxis tickLine={false} axisLine={false} className="text-xs text-muted-foreground" width={55} tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)} />
                  <ChartTooltip content={<ChartTooltipContent formatter={(value) => [formatEUR(value as number), "Valore"]} />} cursor={{ fill: "var(--muted)", opacity: 0.3 }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={48}>
                    {stageData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        {/* Score distribution — area chart with gradient */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Distribuzione Lead Score</CardTitle>
            <CardDescription>Qualita del parco lead per fascia di punteggio</CardDescription>
          </CardHeader>
          <CardContent>
            {leadsLoading ? <ChartSkeleton /> : (leads?.length ?? 0) === 0 ? <EmptyChart /> : (
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
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="var(--chart-3)"
                    strokeWidth={2}
                    fill="url(#scoreGradient)"
                  />
                  {/* Colored dots per bucket */}
                  {scoreData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </AreaChart>
              </ChartContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}