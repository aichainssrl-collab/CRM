"use client";

import { useState, useMemo } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area,
  LineChart, Line,
  ResponsiveContainer, Cell,
  Tooltip,
} from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  useFunnel, useVelocity, usePerformance,
  useTrends, useForecast, useCohorts,
  type FunnelStage, type VelocityItem,
} from "@/hooks/useAnalytics";
import { formatEUR } from "@/lib/format";
import {
  FunnelIcon, Timer, TrendingUp, Users,
  Target, Layers, BarChart3, ChevronRight,
} from "lucide-react";

// ── Colors ────────────────────────────────────────────────────
const STAGE_COLORS: Record<string, string> = {
  new: "var(--chart-1)",
  contacted: "var(--chart-2)",
  qualified: "var(--chart-3)",
  proposal: "var(--chart-4)",
  negotiation: "var(--chart-5)",
  won: "var(--success)",
  lost: "var(--destructive)",
};

const STAGE_LABELS: Record<string, string> = {
  new: "Nuovi",
  contacted: "Contattati",
  qualified: "Qualificati",
  proposal: "Proposta",
  negotiation: "Negoziazione",
  won: "Vinti",
  lost: "Persi",
};

const chartConfig: ChartConfig = {
  count: { label: "Conteggio", color: "var(--chart-1)" },
  value: { label: "Valore", color: "var(--chart-2)" },
  leads: { label: "Lead", color: "var(--chart-1)" },
  dealsWon: { label: "Deal Vinti", color: "var(--success)" },
  dealsLost: { label: "Deal Persi", color: "var(--destructive)" },
};

// ── Helpers ───────────────────────────────────────────────────
function ChartSkeleton() {
  return <Skeleton className="w-full h-[280px] rounded-lg" />;
}

function EmptyChart({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[280px] gap-2 text-muted-foreground">
      <BarChart3 className="h-8 w-8 text-muted-foreground/30" />
      <p className="text-sm text-muted-foreground/60">{message}</p>
    </div>
  );
}

function KpiMini({ label, value, icon: Icon, accent }: {
  label: string;
  value: string;
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
        <p className="text-lg font-bold tracking-tight">{value}</p>
      </div>
    </div>
  );
}

// ── Funnel Bar ────────────────────────────────────────────────
function FunnelChart({ data, loading }: { data?: FunnelStage[]; loading: boolean }) {
  const maxCount = data?.reduce((m, d) => Math.max(m, d.count), 0) ?? 1;
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FunnelIcon className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-base">Funnel Conversioni</CardTitle>
        </div>
        <CardDescription>Distribuzione lead per fase del funnel</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? <ChartSkeleton /> : !data?.length ? <EmptyChart message="Nessun dato" /> : (
          <div className="space-y-3">
            {data.map((item, i) => {
              const pct = maxCount > 0 ? (item.count / maxCount) * 100 : 0;
              const prevCount = i > 0 ? data[i - 1].count : item.count;
              const convRate = prevCount > 0 ? Math.round((item.count / prevCount) * 100) : 0;
              return (
                <div key={item.stage} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium flex items-center gap-2">
                      {STAGE_LABELS[item.stage] || item.stage}
                      {i > 0 && (
                        <span className="text-xs text-muted-foreground flex items-center gap-0.5">
                          <ChevronRight className="h-3 w-3" />{convRate}%
                        </span>
                      )}
                    </span>
                    <span className="font-semibold tabular-nums">{item.count}</span>
                  </div>
                  <div className="h-3 w-full rounded-full bg-muted/50 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.max(pct, 2)}%`,
                        backgroundColor: STAGE_COLORS[item.stage] || "var(--primary)",
                        opacity: 0.85,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Velocity ──────────────────────────────────────────────────
function VelocityChart({ data, loading }: { data?: VelocityItem[]; loading: boolean }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Timer className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-base">Velocity Pipeline</CardTitle>
        </div>
        <CardDescription>Giorni medi per fase di vendita</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? <ChartSkeleton /> : !data?.length ? <EmptyChart message="Nessun dato" /> : (
          <ChartContainer config={chartConfig} className="w-full h-[280px]">
            <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted/50" />
              <XAxis
                dataKey="stage"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                className="text-xs text-muted-foreground"
                tickFormatter={(v) => STAGE_LABELS[v] || v}
              />
              <YAxis tickLine={false} axisLine={false} className="text-xs text-muted-foreground" width={40} label={{ value: "gg", position: "insideTopLeft", offset: -5, className: "text-xs fill-muted-foreground" }} />
              <ChartTooltip
                content={<ChartTooltipContent
                  formatter={(value, name) => [`${value} giorni`, "Tempo medio"]}
                  labelFormatter={(label) => STAGE_LABELS[label] || label}
                />}
                cursor={{ fill: "var(--muted)", opacity: 0.3 }}
              />
              <Bar dataKey="avgDays" radius={[4, 4, 0, 0]} maxBarSize={48}>
                {data.map((entry, i) => (
                  <Cell key={i} fill={STAGE_COLORS[entry.stage] || "var(--chart-1)"} />
                ))}
              </Bar>
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function AnalyticsPage() {
  const t = useTranslations("reports");
  const tTime = useTranslations("timeRanges");
  const [timeRange, setTimeRange] = useState("90d");
  const [trendPeriod, setTrendPeriod] = useState<"week" | "month">("week");

  const TIME_RANGES = [
    { label: tTime("30d"), value: "30d" },
    { label: tTime("90d"), value: "90d" },
    { label: "Tutto", value: "all" },
  ];

  // Queries
  const { data: funnel, isLoading: funnelLoading } = useFunnel(timeRange);
  const { data: velocity, isLoading: velocityLoading } = useVelocity();
  const { data: performance, isLoading: perfLoading } = usePerformance(timeRange);
  const { data: trends, isLoading: trendsLoading } = useTrends(trendPeriod, timeRange);
  const { data: forecastData, isLoading: forecastLoading } = useForecast();
  const { data: cohorts, isLoading: cohortsLoading } = useCohorts(6);

  // Forecast totals
  const forecast = forecastData?.forecast;
  const totalWeighted = forecastData?.totalWeighted ?? 0;
  const totalPipeline = forecastData?.totalPipeline ?? 0;

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics Avanzate</h1>
          <p className="text-sm text-muted-foreground">
            Funnel, velocity, performance, trend e forecasting del tuo CRM
          </p>
        </div>
        <Tabs value={timeRange} onValueChange={(v) => v && setTimeRange(v)}>
          <TabsList>
            {TIME_RANGES.map((r) => (
              <TabsTrigger key={r.value} value={r.value}>{r.label}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {/* Forecast KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiMini
          label="Forecast Ponderato"
          value={formatEUR(totalWeighted)}
          icon={Target}
          accent="bg-success-muted text-success"
        />
        <KpiMini
          label="Pipeline Totale"
          value={formatEUR(totalPipeline)}
          icon={Layers}
          accent="bg-info-muted text-info"
        />
        <KpiMini
          label="Tasso Win Rate"
          value={
            perfLoading || !performance?.length
              ? "—"
              : `${Math.round(performance.reduce((s, p) => s + p.dealsWon, 0) / Math.max(performance.reduce((s, p) => s + p.dealsWon + p.dealsLost, 0), 1) * 100)}%`
          }
          icon={TrendingUp}
          accent="bg-warning-muted text-warning"
        />
        <KpiMini
          label="Team Members"
          value={perfLoading ? "—" : String(performance?.length ?? 0)}
          icon={Users}
          accent="bg-status-proposal-muted text-status-proposal"
        />
      </div>

      {/* Row 1: Funnel + Velocity */}
      <div className="grid gap-4 lg:grid-cols-2">
        <FunnelChart data={funnel} loading={funnelLoading} />
        <VelocityChart data={velocity} loading={velocityLoading} />
      </div>

      {/* Row 2: Trends */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Trend Temporali</CardTitle>
            </div>
            <CardDescription>Lead acquisiti e deal vinti/persi nel tempo</CardDescription>
          </div>
          <Tabs value={trendPeriod} onValueChange={(v) => v && setTrendPeriod(v as "week" | "month")}>
            <TabsList className="h-8">
              <TabsTrigger value="week" className="text-xs px-3">Settimana</TabsTrigger>
              <TabsTrigger value="month" className="text-xs px-3">Mese</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          {trendsLoading ? <ChartSkeleton /> : !trends?.length ? <EmptyChart message="Nessun dato" /> : (
            <ChartContainer config={chartConfig} className="w-full h-[300px]">
              <LineChart data={trends} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted/50" />
                <XAxis dataKey="period" tickLine={false} axisLine={false} tickMargin={8} className="text-xs text-muted-foreground" />
                <YAxis tickLine={false} axisLine={false} className="text-xs text-muted-foreground" width={35} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line type="monotone" dataKey="leads" stroke="var(--chart-1)" strokeWidth={2} dot={{ r: 3 }} name="Lead" />
                <Line type="monotone" dataKey="dealsWon" stroke="var(--success)" strokeWidth={2} dot={{ r: 3 }} name="Deal Vinti" />
                <Line type="monotone" dataKey="dealsLost" stroke="var(--destructive)" strokeWidth={2} dot={{ r: 3 }} strokeDasharray="4 4" name="Deal Persi" />
              </LineChart>
            </ChartContainer>
          )}
        </CardContent>
      </Card>

      {/* Row 3: Forecast + Performance */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Forecast */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Forecast Pipeline</CardTitle>
            </div>
            <CardDescription>Valore ponderato per probabilità di chiusura</CardDescription>
          </CardHeader>
          <CardContent>
            {forecastLoading ? <ChartSkeleton /> : !forecast?.length ? <EmptyChart message="Nessun deal attivo" /> : (
              <ChartContainer config={chartConfig} className="w-full h-[280px]">
                <BarChart data={forecast} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted/50" />
                  <XAxis
                    dataKey="stage"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    className="text-xs text-muted-foreground"
                    tickFormatter={(v) => STAGE_LABELS[v] || v}
                  />
                  <YAxis tickLine={false} axisLine={false} className="text-xs text-muted-foreground" width={55} tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)} />
                  <ChartTooltip
                    content={<ChartTooltipContent
                      formatter={(value, name) => {
                        const label = name === "totalValue" ? "Totale" : "Ponderato";
                        return [formatEUR(value as number), label];
                      }}
                      labelFormatter={(label) => STAGE_LABELS[label] || label}
                    />}
                    cursor={{ fill: "var(--muted)", opacity: 0.3 }}
                  />
                  <Bar dataKey="totalValue" fill="var(--chart-1)" radius={[4, 4, 0, 0]} maxBarSize={36} name="totalValue" fillOpacity={0.4} />
                  <Bar dataKey="weightedValue" fill="var(--success)" radius={[4, 4, 0, 0]} maxBarSize={36} name="weightedValue" />
                </BarChart>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        {/* Performance per rep */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Performance Team</CardTitle>
            </div>
            <CardDescription>Classifica venditori per revenue e win rate</CardDescription>
          </CardHeader>
          <CardContent>
            {perfLoading ? <ChartSkeleton /> : !performance?.length ? <EmptyChart message="Nessun dato performance" /> : (
              <div className="space-y-4">
                {performance.map((rep) => (
                  <div key={rep.userId} className="flex items-center gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
                      {rep.userName.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium truncate">{rep.userName}</p>
                        <Badge variant="secondary" className="text-[10px] ml-2 shrink-0">
                          Win {rep.winRate}%
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                        <span>{rep.leads} lead</span>
                        <span>{rep.dealsWon} vinti</span>
                        <span className="font-medium text-foreground">{formatEUR(rep.revenue)}</span>
                      </div>
                      {/* Mini bar */}
                      <div className="mt-1.5 h-1.5 w-full rounded-full bg-muted/50 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-success"
                          style={{
                            width: `${Math.min(rep.winRate, 100)}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 4: Cohort Analysis */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Analisi Cohort</CardTitle>
          </div>
          <CardDescription>Conversione lead per mese di creazione</CardDescription>
        </CardHeader>
        <CardContent>
          {cohortsLoading ? <ChartSkeleton /> : !cohorts?.length ? <EmptyChart message="Nessun dato" /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 pr-4 font-medium text-muted-foreground">Mese</th>
                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Lead</th>
                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Contattati</th>
                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Tasso</th>
                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Qualificati</th>
                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Tasso</th>
                    <th className="text-right py-2 px-3 font-medium text-muted-foreground">Convertiti</th>
                    <th className="text-right py-2 pl-3 font-medium text-muted-foreground">Tasso</th>
                  </tr>
                </thead>
                <tbody>
                  {cohorts.map((row) => (
                    <tr key={row.month} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                      <td className="py-2.5 pr-4 font-medium">{row.month}</td>
                      <td className="text-right py-2.5 px-3 tabular-nums">{row.total}</td>
                      <td className="text-right py-2.5 px-3 tabular-nums">{row.contacted}</td>
                      <td className="text-right py-2.5 px-3">
                        <Badge variant={row.contactRate >= 50 ? "default" : "secondary"} className="text-[10px]">
                          {row.contactRate}%
                        </Badge>
                      </td>
                      <td className="text-right py-2.5 px-3 tabular-nums">{row.qualified}</td>
                      <td className="text-right py-2.5 px-3">
                        <Badge variant={row.qualifyRate >= 20 ? "default" : "secondary"} className="text-[10px]">
                          {row.qualifyRate}%
                        </Badge>
                      </td>
                      <td className="text-right py-2.5 px-3 tabular-nums">{row.converted}</td>
                      <td className="text-right py-2.5 pl-3">
                        <Badge variant={row.convertRate >= 5 ? "default" : "secondary"} className="text-[10px]">
                          {row.convertRate}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}