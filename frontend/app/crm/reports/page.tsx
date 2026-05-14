"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
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

const TIME_RANGES = [
  { label: "7d", value: "7d" },
  { label: "30d", value: "30d" },
  { label: "90d", value: "90d" },
];

function formatEUR(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

const sourceChartConfig: ChartConfig = {
  count: { label: "Leads", color: "#6366f1" },
};

const stageChartConfig: ChartConfig = {
  value: { label: "Valore (EUR)", color: "#0891b2" },
};

const scoreChartConfig: ChartConfig = {
  count: { label: "Leads", color: "#059669" },
};

const SCORE_BUCKETS = ["0-20", "21-40", "41-60", "61-80", "81-100"];

function ChartSkeleton() {
  return <Skeleton className="w-full h-[220px] rounded" />;
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[220px] gap-2 text-on-surface-variant">
      <span className="material-symbols-outlined text-[40px] text-outline">bar_chart</span>
      <p className="font-body text-body">{label}</p>
    </div>
  );
}

export default function ReportsPage() {
  const [timeRange, setTimeRange] = useState("30d");

  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics(timeRange);
  const { data: leads, isLoading: leadsLoading } = useLeads({ limit: 100 });
  const { data: deals, isLoading: dealsLoading } = useDeals({ limit: 100 });

  const sourceData = useMemo(() => {
    if (!leads?.length) return [];
    const counts: Record<string, number> = {};
    for (const lead of leads) {
      const src = (lead as any).source ?? "Unknown";
      counts[src] = (counts[src] ?? 0) + 1;
    }
    return Object.entries(counts)
      .map(([source, count]) => ({ source, count }))
      .sort((a, b) => b.count - a.count);
  }, [leads]);

  const stageData = useMemo(() => {
    if (!deals?.length) return [];
    const totals: Record<string, number> = {};
    for (const deal of deals) {
      totals[deal.stage] = (totals[deal.stage] ?? 0) + (deal.value ?? 0);
    }
    return Object.entries(totals)
      .map(([stage, value]) => ({ stage, value }))
      .sort((a, b) => b.value - a.value);
  }, [deals]);

  const scoreData = useMemo(() => {
    if (!leads?.length) return [];
    const buckets: Record<string, number> = {
      "0-20": 0,
      "21-40": 0,
      "41-60": 0,
      "61-80": 0,
      "81-100": 0,
    };
    for (const lead of leads) {
      const s = lead.leadScore ?? 0;
      if (s <= 20) buckets["0-20"]++;
      else if (s <= 40) buckets["21-40"]++;
      else if (s <= 60) buckets["41-60"]++;
      else if (s <= 80) buckets["61-80"]++;
      else buckets["81-100"]++;
    }
    return SCORE_BUCKETS.map((range) => ({ range, count: buckets[range] }));
  }, [leads]);

  const dash = (v: number | undefined, format?: (n: number) => string) => {
    if (metricsLoading || v === undefined) return "—";
    return format ? format(v) : v.toLocaleString("it-IT");
  };

  return (
    <main className="p-container_padding max-w-[1440px] w-full mx-auto flex flex-col gap-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="font-display text-display text-on-surface">Reports & Analytics</h2>
        </div>
        <div className="flex items-center gap-1 bg-surface-container rounded p-1">
          {TIME_RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => setTimeRange(r.value)}
              className={`px-3 py-1 rounded font-small-medium text-small-medium transition-colors ${
                timeRange === r.value
                  ? "bg-primary text-on-primary"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardContent className="p-5 flex flex-col justify-between h-[100px]">
            <div className="flex justify-between items-start">
              <span className="font-small-medium text-small-medium text-on-surface-variant">Total Leads</span>
              <span className="material-symbols-outlined text-outline">groups</span>
            </div>
            <div className="font-display text-display text-on-surface">
              {dash(metrics?.totalLeads)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardContent className="p-5 flex flex-col justify-between h-[100px]">
            <div className="flex justify-between items-start">
              <span className="font-small-medium text-small-medium text-on-surface-variant">New Leads</span>
              <span className="material-symbols-outlined text-outline">person_add</span>
            </div>
            <div className="font-display text-display text-on-surface">
              {dash(metrics?.newLeads)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardContent className="p-5 flex flex-col justify-between h-[100px]">
            <div className="flex justify-between items-start">
              <span className="font-small-medium text-small-medium text-on-surface-variant">Active Deals</span>
              <span className="material-symbols-outlined text-outline">work</span>
            </div>
            <div className="font-display text-display text-on-surface">
              {dash(metrics?.activeDeals)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardContent className="p-5 flex flex-col justify-between h-[100px]">
            <div className="flex justify-between items-start">
              <span className="font-small-medium text-small-medium text-on-surface-variant">Conversion Rate</span>
              <span className="material-symbols-outlined text-outline">emoji_events</span>
            </div>
            <div className="font-display text-display text-on-surface">
              {metricsLoading || metrics?.conversionRate === undefined
                ? "—"
                : `${metrics.conversionRate}%`}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardHeader className="p-6 pb-2">
            <CardTitle className="font-h3 text-h3 text-on-surface">Leads per Fonte</CardTitle>
          </CardHeader>
          <CardContent className="p-6 pt-2">
            {leadsLoading ? (
              <ChartSkeleton />
            ) : sourceData.length === 0 ? (
              <EmptyState label="Nessun dato disponibile" />
            ) : (
              <ChartContainer config={sourceChartConfig} className="w-full h-[220px]">
                <BarChart data={sourceData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#c8c5cd" />
                  <XAxis
                    dataKey="source"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    tick={{ fill: "#5e5d68", fontSize: 11 }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: "#5e5d68", fontSize: 11 }}
                    width={30}
                  />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="count" fill="var(--color-count)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ChartContainer>
            )}
          </CardContent>
        </Card>

        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardHeader className="p-6 pb-2">
            <CardTitle className="font-h3 text-h3 text-on-surface">Pipeline per Stage</CardTitle>
          </CardHeader>
          <CardContent className="p-6 pt-2">
            {dealsLoading ? (
              <ChartSkeleton />
            ) : stageData.length === 0 ? (
              <EmptyState label="Nessun dato disponibile" />
            ) : (
              <ChartContainer config={stageChartConfig} className="w-full h-[220px]">
                <BarChart data={stageData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#c8c5cd" />
                  <XAxis
                    dataKey="stage"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    tick={{ fill: "#5e5d68", fontSize: 11 }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: "#5e5d68", fontSize: 11 }}
                    width={60}
                    tickFormatter={(v) =>
                      v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)
                    }
                  />
                  <ChartTooltip
                    content={
                      <ChartTooltipContent
                        formatter={(value) => [
                          formatEUR(value as number),
                          "Valore",
                        ]}
                      />
                    }
                  />
                  <Bar dataKey="value" fill="var(--color-value)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ChartContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
        <CardHeader className="p-6 pb-2">
          <CardTitle className="font-h3 text-h3 text-on-surface">Distribuzione Lead Score</CardTitle>
        </CardHeader>
        <CardContent className="p-6 pt-2">
          {leadsLoading ? (
            <ChartSkeleton />
          ) : (leads?.length ?? 0) === 0 ? (
            <EmptyState label="Nessun dato disponibile" />
          ) : (
            <ChartContainer config={scoreChartConfig} className="w-full h-[220px]">
              <BarChart data={scoreData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#c8c5cd" />
                <XAxis
                  dataKey="range"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  tick={{ fill: "#5e5d68", fontSize: 12 }}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "#5e5d68", fontSize: 12 }}
                  width={30}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="count" fill="var(--color-count)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ChartContainer>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
