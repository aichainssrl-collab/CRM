"use client";

import { useDashboardMetrics } from "@/hooks/useDashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Handshake, TrendingUp, DollarSign } from "lucide-react";

export function DashboardKPIs() {
  const { data: metrics, isLoading } = useDashboardMetrics();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-muted rounded"></div>
              <div className="h-4 w-4 bg-muted rounded-full"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted rounded mb-2"></div>
              <div className="h-3 w-32 bg-muted rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const kpis = [
    {
      title: "Total Leads",
      value: metrics?.totalLeads || 0,
      description: "+20.1% from last month",
      icon: Users,
    },
    {
      title: "Active Deals",
      value: metrics?.activeDeals || 0,
      description: "+15% from last month",
      icon: Handshake,
    },
    {
      title: "Pipeline Value",
      value: new Intl.NumberFormat("en-US", { style: "currency", currency: "EUR" }).format(metrics?.pipelineValue || 0),
      description: "Based on active deals",
      icon: DollarSign,
    },
    {
      title: "Conversion Rate",
      value: `${(metrics?.conversionRate || 0).toFixed(1)}%`,
      description: "+2.4% from last month",
      icon: TrendingUp,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {kpis.map((kpi) => (
        <Card key={kpi.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{kpi.title}</CardTitle>
            <kpi.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpi.value}</div>
            <p className="text-xs text-muted-foreground">{kpi.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
