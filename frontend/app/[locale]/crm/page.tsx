"use client";

import { useState, useMemo } from "react";
import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { KpiCard } from "@/components/crm/KpiCard";
import { ActivityFeed } from "@/components/crm/ActivityFeed";
import { TeamLeaderboard } from "@/components/crm/TeamLeaderboard";
import { CompetitorAlerts } from "@/components/crm/CompetitorAlerts";
import { formatEUR } from "@/lib/format";
import {
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

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const tTime = useTranslations("timeRanges");
  const tCommon = useTranslations("common");
  const [timeRange, setTimeRange] = useState("30d");
  const { data: metrics, isLoading } = useDashboardMetrics(timeRange);
  const { data: leads = [] } = useLeads({});
  const { data: deals = [] } = useDeals();

  const recentLeads = leads.slice(0, 5);

  const TIME_RANGES = [
    { label: tTime("7d"), value: "7d" },
    { label: tTime("30d"), value: "30d" },
    { label: tTime("90d"), value: "90d" },
  ];

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
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
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
          title={t("pipelineValue")}
          value={isLoading || !metrics ? "—" : formatEUR(metrics.pipelineValue)}
          trend={12}
          trendLabel={tCommon("vsPreviousMonth")}
          icon={Euro}
          loading={isLoading}
          accent="bg-success-muted text-success"
        />
        <KpiCard
          title={t("activeDeals")}
          value={isLoading || !metrics ? "—" : String(metrics.activeDeals)}
          trend={4}
          trendLabel={tCommon("vsPreviousMonth")}
          icon={Briefcase}
          loading={isLoading}
          accent="bg-info-muted text-info"
        />
        <KpiCard
          title={t("conversionRate")}
          value={isLoading || !metrics ? "—" : `${metrics.conversionRate}%`}
          trend={-2}
          trendLabel={tCommon("vsPreviousMonth")}
          icon={Target}
          loading={isLoading}
          accent="bg-warning-muted text-warning"
        />
        <KpiCard
          title={t("newLeads")}
          value={isLoading || !metrics ? "—" : String(metrics.newLeads ?? leads.length)}
          trend={8}
          trendLabel={tCommon("vsPreviousMonth")}
          icon={Users}
          loading={isLoading}
          accent="bg-status-proposal-muted text-status-proposal"
        />
      </div>

      {/* Charts + Recent Leads */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Revenue chart — derived from real deals */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{t("pipelineRevenue")}</CardTitle>
            <CardDescription>{t("chartDescription")}</CardDescription>
          </CardHeader>
          <CardContent>
            {chartData.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[280px] gap-2 text-muted-foreground">
                <Euro className="h-8 w-8 text-muted-foreground/30" />
                <p className="text-sm">{t("noDealsChart")}</p>
                <Button variant="outline" size="sm" nativeButton={false} render={<Link href="/crm/pipeline" />} className="mt-1">
                  {t("goToPipeline")}
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
            <CardTitle>{t("recentLeads")}</CardTitle>
            <Link href="/crm/leads" className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
              {t("viewAll")} <ArrowRight className="h-3 w-3" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {recentLeads.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm text-muted-foreground">
                {t("noLeads")} <Link href="/crm/leads" className="underline">{t("importLeads")}</Link>
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

      {/* Activity Feed + Team Leaderboard */}
      <div className="grid gap-4 lg:grid-cols-2">
        <ActivityFeed limit={15} />
        <TeamLeaderboard days={30} />
      </div>

      {/* Competitor auto-monitor alerts */}
      <CompetitorAlerts limit={6} />
    </div>
  );
}