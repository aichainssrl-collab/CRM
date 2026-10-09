"use client";

import { useTranslations } from "next-intl";
import { useInsights, useSuggestions } from "@/hooks/useMarketingData";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users,
  Target,
  Tag,
  RefreshCw,
  Lightbulb,
  ArrowRight,
  BarChart3,
  Euro,
} from "lucide-react";

// ── Stat card mini ─────────────────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, sub }: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="flex items-start gap-3 p-4 rounded-lg border bg-card">
      <div className="h-9 w-9 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
        <Icon className="h-4 w-4 text-primary" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-lg font-bold tabular-nums">{value}</p>
        {sub && <p className="text-[10px] text-muted-foreground mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ── Bar chart semplice (CSS only) ──────────────────────────────────────────────

function SimpleBar({ label, value, max, color = "bg-primary" }: {
  label: string;
  value: number;
  max: number;
  color?: string;
}) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-xs text-muted-foreground w-24 truncate" title={label}>{label}</span>
      <div className="flex-1 h-5 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium tabular-nums w-10 text-right">{value}</span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function InsightsPanel() {
  const t = useTranslations("marketing.insights");
  const { insights, loading, refetch } = useInsights();
  const { suggestions, loading: sugLoading, refetch: refetchSuggestions } = useSuggestions();

  if (loading) {
    return (
      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-24" />)}
          </div>
          <Skeleton className="h-64" />
          <Skeleton className="h-48" />
        </div>
        <Skeleton className="h-80" />
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-sm text-muted-foreground">{t("noData")}</p>
        <Button variant="outline" size="sm" className="mt-3" onClick={refetch}>
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> {t("retry")}
        </Button>
      </div>
    );
  }

  const { summary, leadsBySource, leadsByStatus, dealsByStage, topTags } = insights;
  const maxSource = Math.max(...leadsBySource.map((s) => s.count), 1);
  const maxStatus = Math.max(...leadsByStatus.map((s) => s.count), 1);
  const maxTag = Math.max(...topTags.map((t) => t.count), 1);

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
      {/* Left — data */}
      <div className="space-y-6">
        {/* Summary cards */}
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard icon={Users} label={t("totalLeads")} value={summary.totalLeads} />
          <StatCard icon={Target} label={t("totalDeals")} value={summary.totalDeals} />
          <StatCard
            icon={Euro}
            label={t("dealValue")}
            value={`€${summary.totalDealValue.toLocaleString("it-IT")}`}
          />
        </div>

        {/* Leads by source */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">{t("leadsBySource")}</CardTitle>
          </CardHeader>
          <CardContent>
            {leadsBySource.length === 0 ? (
              <p className="text-xs text-muted-foreground">{t("noData")}</p>
            ) : (
              <div className="space-y-1">
                {leadsBySource.map((s) => (
                  <SimpleBar key={s.source} label={s.source} value={s.count} max={maxSource} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Leads by status */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">{t("leadsByStatus")}</CardTitle>
          </CardHeader>
          <CardContent>
            {leadsByStatus.length === 0 ? (
              <p className="text-xs text-muted-foreground">{t("noData")}</p>
            ) : (
              <div className="space-y-1">
                {leadsByStatus.map((s) => (
                  <SimpleBar
                    key={s.status}
                    label={s.status || "unknown"}
                    value={s.count}
                    max={maxStatus}
                    color="bg-chart-2"
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Deals by stage */}
        {dealsByStage.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">{t("dealsByStage")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {dealsByStage.map((d) => (
                  <div key={d.stage} className="flex items-center justify-between py-1.5 border-b last:border-0">
                    <span className="text-xs">{d.stage}</span>
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary" className="text-[10px]">{d.count}</Badge>
                      <span className="text-xs font-medium tabular-nums">
                        €{d.totalValue.toLocaleString("it-IT")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Top tags */}
        {topTags.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-1.5">
                <Tag className="h-3.5 w-3.5" />
                {t("topTags")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {topTags.map((tag) => (
                  <SimpleBar
                    key={tag.tag}
                    label={tag.tag}
                    value={tag.count}
                    max={maxTag}
                    color="bg-chart-3"
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Right — AI suggestions */}
      <div className="space-y-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-1.5">
                <Lightbulb className="h-4 w-4 text-yellow-500" />
                {t("suggestions")}
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={refetchSuggestions}
                disabled={sugLoading}
              >
                <RefreshCw className={`h-3.5 w-3.5 ${sugLoading ? "animate-spin" : ""}`} />
              </Button>
            </div>
            <CardDescription>{t("suggestionsDesc")}</CardDescription>
          </CardHeader>
          <CardContent>
            {sugLoading && suggestions.length === 0 ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-8" />)}
              </div>
            ) : (
              <div className="space-y-2.5">
                {suggestions.map((s, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2.5 p-2.5 rounded-lg border bg-muted/30 hover:bg-muted/60 transition-colors cursor-pointer group"
                  >
                    <span className="h-5 w-5 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-[10px] font-bold text-primary">{i + 1}</span>
                    </span>
                    <p className="text-xs leading-relaxed flex-1">{s}</p>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-0.5" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}