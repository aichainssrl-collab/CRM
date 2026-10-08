"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import {
  useMetaStatus,
  useMetaSummary,
  useMetaCampaigns,
  useMetaTrend,
  type DatePreset,
  type MetaCampaign,
} from "@/hooks/useMetaAds";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  AlertCircle,
  TrendingUp,
  MousePointerClick,
  Eye,
  Euro,
  Users,
  Target,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useQueryClient } from "@tanstack/react-query";

// ── Formatters ────────────────────────────────────────────────────────────────

function fEUR(v: number) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 2 }).format(v);
}
function fNum(v: number) {
  return new Intl.NumberFormat("it-IT").format(v);
}
function fPct(v: number) {
  return `${(v * 100).toFixed(2)}%`;
}

// ── Status badge campagna ─────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const t = useTranslations("marketing");
  const map: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    ACTIVE: "default",
    PAUSED: "secondary",
    ARCHIVED: "outline",
    DELETED: "destructive",
  };
  return (
    <Badge variant={map[status] ?? "secondary"} className="text-[10px] uppercase">
      {status === "ACTIVE" ? t("active") : status === "PAUSED" ? t("paused") : status}
    </Badge>
  );
}

// ── KPI card ──────────────────────────────────────────────────────────────────

function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  loading,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ElementType;
  loading: boolean;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-28 mb-1" />
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
        {subtitle && !loading && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}

// ── Chart configs ─────────────────────────────────────────────────────────────

const spendChartConfig = {
  spend: { label: "Spesa (€)", color: "var(--primary)" },
  clicks: { label: "Click", color: "var(--chart-2)" },
} satisfies ChartConfig;

// ── Blocco non configurato ────────────────────────────────────────────────────

function NotConfiguredAlert() {
  const t = useTranslations("marketing");
  return (
    <div className="flex flex-col gap-6 p-6 max-w-[900px] mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
      </div>
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>{t("notConfigured")}</AlertTitle>
        <AlertDescription className="mt-2 space-y-3">
          <p>{t("notConfiguredDesc")}</p>
          <pre className="rounded bg-muted px-4 py-3 text-xs font-mono">
{`META_ACCESS_TOKEN=EAAxxxxx...   # Token accesso Meta
META_AD_ACCOUNT_ID=act_123456789  # ID Ad Account`}
          </pre>
          <p className="text-sm">
            {t("getToken")}{" "}
            <a
              href="https://developers.facebook.com/tools/explorer/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline inline-flex items-center gap-1"
            >
              {t("graphApi")} <ExternalLink className="h-3 w-3" />
            </a>
            {" "}{t("withPerms")} <code className="text-xs bg-muted px-1 rounded">ads_read</code>,{" "}
            <code className="text-xs bg-muted px-1 rounded">read_insights</code>.
          </p>
          <p className="text-sm">
            {t("adAccountId")}{" "}
            <a
              href="https://business.facebook.com/adsmanager"
              target="_blank"
              rel="noopener noreferrer"
              className="underline inline-flex items-center gap-1"
            >
              {t("adsManager")} <ExternalLink className="h-3 w-3" />
            </a>
            {" "}→ in alto a sinistra (formato: <code className="text-xs bg-muted px-1 rounded">act_XXXXXXXXX</code>).
          </p>
        </AlertDescription>
      </Alert>
    </div>
  );
}

// ── Pagina principale ─────────────────────────────────────────────────────────

export default function MarketingPage() {
  const t = useTranslations("marketing");
  const tTime = useTranslations("timeRanges");
  const [datePreset, setDatePreset] = useState<DatePreset>("30d");
  const queryClient = useQueryClient();

  const { data: status, isLoading: statusLoading } = useMetaStatus();
  const { data: summary, isLoading: summaryLoading } = useMetaSummary(datePreset);
  const { data: campaignsData, isLoading: campaignsLoading } = useMetaCampaigns(datePreset);
  const { data: trendData, isLoading: trendLoading } = useMetaTrend(datePreset);

  const isLoading = summaryLoading || statusLoading;

  const DATE_RANGES: { label: string; value: DatePreset }[] = [
    { label: tTime("7d"), value: "7d" },
    { label: tTime("30d"), value: "30d" },
    { label: tTime("90d"), value: "90d" },
  ];

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["meta"] });
  };

  // Mostra spinner durante il check iniziale
  if (statusLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // Non configurato
  if (!status?.configured) {
    return <NotConfiguredAlert />;
  }

  const campaigns = campaignsData?.campaigns ?? [];
  const trend = trendData?.trend ?? [];

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">
            {status.account_name
              ? `${t("account")}: ${status.account_name} · ${status.account_id}`
              : "Facebook & Instagram Ads"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-1.5" />
            Aggiorna
          </Button>
          <Tabs value={datePreset} onValueChange={(v) => v && setDatePreset(v as DatePreset)}>
            <TabsList>
              {DATE_RANGES.map((r) => (
                <TabsTrigger key={r.value} value={r.value}>
                  {r.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <KpiCard
          title={t("totalSpend")}
          value={summary ? fEUR(summary.spend) : "—"}
          subtitle={`CPM: ${summary ? fEUR(summary.cpm) : "—"}`}
          icon={Euro}
          loading={isLoading}
        />
        <KpiCard
          title={t("impressions")}
          value={summary ? fNum(summary.impressions) : "—"}
          icon={Eye}
          loading={isLoading}
        />
        <KpiCard
          title={t("clicks")}
          value={summary ? fNum(summary.clicks) : "—"}
          subtitle={`CTR: ${summary ? fPct(summary.ctr) : "—"}`}
          icon={MousePointerClick}
          loading={isLoading}
        />
        <KpiCard
          title={t("avgCpc")}
          value={summary ? fEUR(summary.cpc) : "—"}
          subtitle={t("costPerClick")}
          icon={TrendingUp}
          loading={isLoading}
        />
        <KpiCard
          title={t("reach")}
          value={summary ? fNum(summary.reach) : "—"}
          subtitle={t("peopleReached")}
          icon={Users}
          loading={isLoading}
        />
        <KpiCard
          title={t("conversions")}
          value={summary ? fNum(summary.conversions) : "—"}
          subtitle={t("leadAcquisitions")}
          icon={Target}
          loading={isLoading}
        />
      </div>

      {/* Trend chart */}
      <Card>
        <CardHeader>
          <CardTitle>{t("spendTrend")}</CardTitle>
          <CardDescription>{t("dailyBreakdown")}</CardDescription>
        </CardHeader>
        <CardContent>
          {trendLoading ? (
            <Skeleton className="h-[260px] w-full" />
          ) : trend.length === 0 ? (
            <div className="flex h-[260px] items-center justify-center text-sm text-muted-foreground">
              {t("noDataPeriod")}
            </div>
          ) : (
            <ChartContainer config={spendChartConfig} className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="fillSpend" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                  <XAxis
                    dataKey="date"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    tickFormatter={(v: string) => {
                      const d = new Date(v);
                      return `${d.getDate()}/${d.getMonth() + 1}`;
                    }}
                    className="text-xs text-muted-foreground"
                  />
                  <YAxis
                    yAxisId="spend"
                    orientation="left"
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v: number) => `€${v}`}
                    className="text-xs text-muted-foreground"
                    width={55}
                  />
                  <YAxis
                    yAxisId="clicks"
                    orientation="right"
                    tickLine={false}
                    axisLine={false}
                    className="text-xs text-muted-foreground"
                    width={45}
                  />
                  <ChartTooltip content={<ChartTooltipContent indicator="line" />} />
                  <Area
                    yAxisId="spend"
                    type="monotone"
                    dataKey="spend"
                    stroke="var(--primary)"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#fillSpend)"
                  />
                  <Area
                    yAxisId="clicks"
                    type="monotone"
                    dataKey="clicks"
                    stroke="var(--chart-2)"
                    strokeWidth={1.5}
                    fillOpacity={0}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </ChartContainer>
          )}
        </CardContent>
      </Card>

      {/* Tabella campagne */}
      <Card>
        <CardHeader>
          <CardTitle>{t("campaigns")}</CardTitle>
          <CardDescription>
            {campaignsLoading
              ? "Caricamento..."
              : t("campaignsLoaded", { count: campaignsData?.total ?? 0 })}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {campaignsLoading ? (
            <div className="p-6 space-y-3">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : campaigns.length === 0 ? (
            <div className="px-6 py-12 text-center text-sm text-muted-foreground">
              Nessuna campagna trovata per questo periodo
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[200px]">{t("campaign")}</TableHead>
                    <TableHead>Stato</TableHead>
                    <TableHead className="text-right">{t("totalSpend")}</TableHead>
                    <TableHead className="text-right">{t("impressions")}</TableHead>
                    <TableHead className="text-right">{t("clicks")}</TableHead>
                    <TableHead className="text-right">CTR</TableHead>
                    <TableHead className="text-right">CPC</TableHead>
                    <TableHead className="text-right">{t("reach")}</TableHead>
                    <TableHead className="text-right">Conv.</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaigns.map((c: MetaCampaign) => (
                    <TableRow key={c.id} className="hover:bg-muted/50">
                      <TableCell>
                        <div>
                          <p className="font-medium text-sm truncate max-w-[250px]" title={c.name}>
                            {c.name}
                          </p>
                          {c.objective && (
                            <p className="text-[10px] text-muted-foreground uppercase mt-0.5">
                              {c.objective.replace(/_/g, " ")}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={c.status} />
                      </TableCell>
                      <TableCell className="text-right font-medium tabular-nums">
                        {fEUR(c.spend)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {fNum(c.impressions)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {fNum(c.clicks)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {fPct(c.ctr)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {fEUR(c.cpc)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {fNum(c.reach)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums font-medium">
                        {c.conversions > 0 ? fNum(c.conversions) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}