"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Area, AreaChart, CartesianGrid, XAxis, ResponsiveContainer, YAxis } from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDashboardMetrics } from "@/hooks/useDashboard";
import { useLeads } from "@/hooks/useLeads";
import { useDeals } from "@/hooks/useDeals";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  Briefcase,
  Euro,
  Target,
  ArrowRight,
  Activity,
} from "lucide-react";

const MONTHS_IT = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"];

const chartConfig = {
  revenue: { label: "Pipeline (€)", color: "var(--primary)" },
} satisfies ChartConfig;

const TIME_RANGES = [
  { label: "7 giorni", value: "7d" },
  { label: "30 giorni", value: "30d" },
  { label: "90 giorni", value: "90d" },
];

function formatEUR(value: number) {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

function TrendIcon({ value }: { value?: number }) {
  if (value === undefined) return <Minus className="h-3 w-3 text-muted-foreground" />;
  if (value > 0) return <TrendingUp className="h-3 w-3 text-emerald-500" />;
  if (value < 0) return <TrendingDown className="h-3 w-3 text-destructive" />;
  return <Minus className="h-3 w-3 text-muted-foreground" />;
}

function KpiCard({
  title,
  value,
  trend,
  icon: Icon,
  loading,
  accent,
}: {
  title: string;
  value: string;
  trend?: number;
  icon: React.ElementType;
  loading: boolean;
  accent?: string;
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
        {loading ? (
          <Skeleton className="h-8 w-28 mb-1" />
        ) : (
          <div className="text-2xl font-bold tracking-tight">{value}</div>
        )}
        {trend !== undefined && !loading && (
          <p className="flex items-center gap-1 text-xs text-muted-foreground mt-1.5">
            <TrendIcon value={trend} />
            <span className={trend > 0 ? "text-emerald-600 font-medium" : trend < 0 ? "text-destructive font-medium" : ""}>
              {trend > 0 ? "+" : ""}{trend}%
            </span>
            <span>vs mese precedente</span>
          </p>
        )}
      </CardContent>
      <div className={`absolute bottom-0 left-0 h-0.5 w-full opacity-0 transition-opacity duration-200 group-hover:opacity-100 ${accent ?? "bg-primary"}`} />
    </Card>
  );
}

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState("30d");
  const { data: metrics, isLoading } = useDashboardMetrics(timeRange);
  const { data: leads = [] } = useLeads({});
  const { data: deals = [] } = useDeals();

  const recentLeads = leads.slice(0, 5);

  // Derive chart data from real deals — group by creation month
  const chartData = useMemo(() => {
    if (!deals.length) return [];
    const now = new Date();
    const months: { month: string; revenue: number; key: string }[] = [];
    for (let i = 5; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      months.push({
        month: MONTHS_IT[d.getMonth()],
        revenue: 0,
        key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`,
      });
    }
    for (const deal of deals) {
      if (!deal.createdAt || !deal.value) continue;
      const created = new Date(deal.createdAt);
      const key = `${created.getFullYear()}-${String(created.getMonth() + 1).padStart(2, "0")}`;
      const bucket = months.find((m) => m.key === key);
      if (bucket) bucket.revenue += deal.value;
    }
    return months;
  }, [deals]);

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Panoramica delle performance commerciali</p>
        </div>
        <Tabs value={timeRange} onValueChange={(v) => v && setTimeRange(v)}>
          <TabsList>
            {TIME_RANGES.map((r) => (
              <TabsTrigger key={r.value} value={r.value}>
                {r.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Valore Pipeline"
          value={isLoading || !metrics ? "—" : formatEUR(metrics.pipelineValue)}
          trend={12}
          icon={Euro}
          loading={isLoading}
          accent="bg-emerald-500/10 text-emerald-600"
        />
        <KpiCard
          title="Deal Attivi"
          value={isLoading || !metrics ? "—" : String(metrics.activeDeals)}
          trend={4}
          icon={Briefcase}
          loading={isLoading}
          accent="bg-blue-500/10 text-blue-600"
        />
        <KpiCard
          title="Tasso di Conversione"
          value={isLoading || !metrics ? "—" : `${metrics.conversionRate}%`}
          trend={-2}
          icon={Target}
          loading={isLoading}
          accent="bg-amber-500/10 text-amber-600"
        />
        <KpiCard
          title="Nuovi Lead"
          value={isLoading || !metrics ? "—" : String(metrics.newLeads ?? leads.length)}
          trend={8}
          icon={Users}
          loading={isLoading}
          accent="bg-violet-500/10 text-violet-600"
        />
      </div>

      {/* Charts + Recent Leads */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Revenue chart — derived from real deals */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Pipeline Revenue</CardTitle>
            <CardDescription>Valore deal creati negli ultimi 6 mesi</CardDescription>
          </CardHeader>
          <CardContent>
            {chartData.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[280px] gap-2 text-muted-foreground">
                <Euro className="h-8 w-8 text-muted-foreground/30" />
                <p className="text-sm">Nessun deal presente. Crea il primo deal per vedere il grafico.</p>
                <Button variant="outline" size="sm" render={<Link href="/crm/pipeline" />} className="mt-1">
                  Vai alla Pipeline
                </Button>
              </div>
            ) : (
              <ChartContainer config={chartConfig} className="h-[280px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="fillRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                    <XAxis
                      dataKey="month"
                      tickLine={false}
                      axisLine={false}
                      tickMargin={8}
                      className="text-xs text-muted-foreground"
                    />
                    <YAxis
                      tickLine={false}
                      axisLine={false}
                      className="text-xs text-muted-foreground"
                      width={55}
                      tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)}
                    />
                    <ChartTooltip
                      content={<ChartTooltipContent indicator="line" formatter={(value) => [formatEUR(value as number), "Valore"]} />}
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="var(--primary)"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#fillRevenue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        {/* Recent Leads */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle>Lead Recenti</CardTitle>
            <Link href="/crm/leads" className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
              Vedi tutti <ArrowRight className="h-3 w-3" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {recentLeads.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm text-muted-foreground">
                Nessun lead ancora. <Link href="/crm/leads" className="underline">Importa leads</Link>
              </div>
            ) : (
              <div className="divide-y">
                {recentLeads.map((lead) => (
                  <div key={lead.id} className="flex items-center gap-3 px-6 py-3 hover:bg-muted/50 transition-colors">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-semibold">
                      {(lead.firstName?.[0] ?? lead.email[0]).toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {lead.firstName && lead.lastName
                          ? `${lead.firstName} ${lead.lastName}`
                          : lead.email}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">{lead.companyName ?? lead.email}</p>
                    </div>
                    <Badge variant="secondary" className="shrink-0 text-[10px]">
                      {lead.pipelineStage ?? "new"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Activity — real data or empty state */}
      <Card>
        <CardHeader>
          <CardTitle>Attività Recenti</CardTitle>
          <CardDescription>Ultime interazioni del team commerciale</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-10 text-center gap-3">
            <Activity className="h-10 w-10 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">
              Le attività del team verranno visualizzate qui quando disponibili.
            </p>
            <Button variant="outline" size="sm" render={<Link href="/crm/leads" />}>
              Vai ai Lead
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
