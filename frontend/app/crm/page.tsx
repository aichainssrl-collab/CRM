"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Area, AreaChart, CartesianGrid, XAxis, ResponsiveContainer } from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { useDashboardMetrics } from "@/hooks/useDashboard";

const chartData = [
  { month: "Jan", revenue: 45000 },
  { month: "Feb", revenue: 52000 },
  { month: "Mar", revenue: 48000 },
  { month: "Apr", revenue: 61000 },
  { month: "May", revenue: 59000 },
  { month: "Jun", revenue: 75000 },
];

const chartConfig = {
  revenue: {
    label: "Revenue ($)",
    color: "#e2e0fc",
  },
} satisfies ChartConfig;

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

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState("30d");
  const { data: metrics, isLoading } = useDashboardMetrics(timeRange);

  const dash = (v: number | undefined, format?: (n: number) => string) => {
    if (isLoading || v === undefined) return "—";
    return format ? format(v) : v.toLocaleString("it-IT");
  };

  return (
    <main className="p-container_padding max-w-[1440px] w-full mx-auto flex flex-col gap-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="font-display text-display text-on-surface">Dashboard</h2>
        </div>
        <div className="flex items-center gap-3">
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
          <Button className="bg-primary text-on-primary h-input_height px-4 font-body-medium flex items-center gap-2 hover:bg-surface-tint transition-colors">
            <span className="material-symbols-outlined text-[18px]">download</span>
            Export Report
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardContent className="p-5 flex flex-col justify-between h-[120px]">
            <div className="flex justify-between items-start">
              <span className="font-small-medium text-small-medium text-on-surface-variant">Pipeline Value</span>
              <span className="material-symbols-outlined text-outline">payments</span>
            </div>
            <div>
              <div className="font-display text-display text-on-surface">
                {dash(metrics?.pipelineValue, formatEUR)}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardContent className="p-5 flex flex-col justify-between h-[120px]">
            <div className="flex justify-between items-start">
              <span className="font-small-medium text-small-medium text-on-surface-variant">Active Deals</span>
              <span className="material-symbols-outlined text-outline">work</span>
            </div>
            <div>
              <div className="font-display text-display text-on-surface">
                {dash(metrics?.activeDeals)}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardContent className="p-5 flex flex-col justify-between h-[120px]">
            <div className="flex justify-between items-start">
              <span className="font-small-medium text-small-medium text-on-surface-variant">Conversion Rate</span>
              <span className="material-symbols-outlined text-outline">emoji_events</span>
            </div>
            <div>
              <div className="font-display text-display text-on-surface">
                {isLoading || metrics?.conversionRate === undefined
                  ? "—"
                  : `${metrics.conversionRate}%`}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-container-lowest border-outline-variant shadow-none">
          <CardContent className="p-5 flex flex-col justify-between h-[120px]">
            <div className="flex justify-between items-start">
              <span className="font-small-medium text-small-medium text-on-surface-variant">New Leads</span>
              <span className="material-symbols-outlined text-outline">person_add</span>
            </div>
            <div>
              <div className="font-display text-display text-on-surface">
                {dash(metrics?.newLeads)}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 bg-surface-container-lowest border-outline-variant shadow-none flex flex-col">
          <CardHeader className="p-6 pb-0">
            <CardTitle className="font-h3 text-h3 text-on-surface">Revenue Pipeline</CardTitle>
          </CardHeader>
          <CardContent className="p-6 pt-6 flex-1 flex flex-col">
            <div className="flex-1 bg-surface-container-low rounded border border-outline-variant/50 relative min-h-[300px] w-full p-4">
              <ChartContainer config={chartConfig} className="w-full h-full min-h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="fillRevenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--color-revenue)" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="var(--color-revenue)" stopOpacity={0.1} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#c8c5cd" />
                    <XAxis
                      dataKey="month"
                      tickLine={false}
                      axisLine={false}
                      tickMargin={10}
                      tick={{ fill: "#5e5d68", fontSize: 12 }}
                    />
                    <ChartTooltip
                      cursor={false}
                      content={<ChartTooltipContent indicator="line" />}
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="#1a1a2e"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#fillRevenue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface-container-lowest border-outline-variant shadow-none flex flex-col">
          <div className="p-4 border-b border-outline-variant flex justify-between items-center">
            <h3 className="font-h3 text-h3 text-on-surface">Recent Leads</h3>
            <Button variant="ghost" className="h-auto p-0 font-small-medium text-secondary hover:text-primary transition-colors">
              View All
            </Button>
          </div>
          <div className="flex flex-col">
            <div className="p-4 flex items-center justify-between border-b border-outline-variant hover:bg-surface-container transition-colors">
              <div className="flex items-center gap-3">
                <Avatar className="w-8 h-8">
                  <AvatarFallback className="bg-secondary-fixed text-on-secondary-fixed font-small-medium">SJ</AvatarFallback>
                </Avatar>
                <div>
                  <div className="font-body-medium text-on-surface">Sarah Jenkins</div>
                  <div className="font-small text-on-surface-variant">Acme Corp</div>
                </div>
              </div>
              <Badge variant="secondary" className="bg-[#e3fafc] text-[#0b7285] hover:bg-[#e3fafc] rounded-full font-small-medium text-[10px]">Hot</Badge>
            </div>

            <div className="p-4 flex items-center justify-between border-b border-outline-variant hover:bg-surface-container transition-colors">
              <div className="flex items-center gap-3">
                <Avatar className="w-8 h-8">
                  <AvatarFallback className="bg-secondary-fixed text-on-secondary-fixed font-small-medium">MW</AvatarFallback>
                </Avatar>
                <div>
                  <div className="font-body-medium text-on-surface">Marcus Webb</div>
                  <div className="font-small text-on-surface-variant">TechFlow</div>
                </div>
              </div>
              <Badge variant="secondary" className="bg-[#fff3bf] text-[#e67700] hover:bg-[#fff3bf] rounded-full font-small-medium text-[10px]">Warm</Badge>
            </div>

            <div className="p-4 flex items-center justify-between border-b border-outline-variant hover:bg-surface-container transition-colors">
              <div className="flex items-center gap-3">
                <Avatar className="w-8 h-8">
                  <AvatarFallback className="bg-secondary-fixed text-on-secondary-fixed font-small-medium">EL</AvatarFallback>
                </Avatar>
                <div>
                  <div className="font-body-medium text-on-surface">Elena Lopez</div>
                  <div className="font-small text-on-surface-variant">Global Sync</div>
                </div>
              </div>
              <Badge variant="secondary" className="bg-[#f8f9fa] text-[#868e96] hover:bg-[#f8f9fa] rounded-full font-small-medium text-[10px]">Cold</Badge>
            </div>

            <div className="p-4 flex items-center justify-between hover:bg-surface-container transition-colors">
              <div className="flex items-center gap-3">
                <Avatar className="w-8 h-8">
                  <AvatarFallback className="bg-secondary-fixed text-on-secondary-fixed font-small-medium">DK</AvatarFallback>
                </Avatar>
                <div>
                  <div className="font-body-medium text-on-surface">David Kim</div>
                  <div className="font-small text-on-surface-variant">Nexus Industries</div>
                </div>
              </div>
              <Badge variant="secondary" className="bg-[#e3fafc] text-[#0b7285] hover:bg-[#e3fafc] rounded-full font-small-medium text-[10px]">Hot</Badge>
            </div>
          </div>
        </Card>
      </div>

      <Card className="bg-surface-container-lowest border-outline-variant shadow-none p-6">
        <h3 className="font-h3 text-h3 text-on-surface mb-6">Recent Activity</h3>
        <div className="flex flex-col gap-6 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-[2px] before:bg-outline-variant/30">
          <div className="flex gap-4 relative z-0">
            <div className="w-10 h-10 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center shrink-0 z-10">
              <span className="material-symbols-outlined text-[18px] text-primary">mail</span>
            </div>
            <div className="pt-2">
              <p className="font-body-medium text-body-medium text-on-surface">Proposal sent to <span className="font-semibold">Acme Corp</span></p>
              <p className="font-small text-small text-on-surface-variant mt-1">2 hours ago by Sarah Jenkins</p>
            </div>
          </div>

          <div className="flex gap-4 relative z-0">
            <div className="w-10 h-10 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center shrink-0 z-10">
              <span className="material-symbols-outlined text-[18px] text-primary">call</span>
            </div>
            <div className="pt-2">
              <p className="font-body-medium text-body-medium text-on-surface">Discovery call completed with <span className="font-semibold">TechFlow</span></p>
              <p className="font-small text-small text-on-surface-variant mt-1">4 hours ago by Marcus Webb</p>
            </div>
          </div>

          <div className="flex gap-4 relative z-0">
            <div className="w-10 h-10 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center shrink-0 z-10">
              <span className="material-symbols-outlined text-[18px] text-[#2b8a3e]">check_circle</span>
            </div>
            <div className="pt-2">
              <p className="font-body-medium text-body-medium text-on-surface">Deal won: <span className="font-semibold">Global Sync Enterprise License</span></p>
              <p className="font-small text-small text-on-surface-variant mt-1">Yesterday at 3:45 PM</p>
            </div>
          </div>
        </div>
      </Card>
    </main>
  );
}
