"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useCompetitorChanges, useCompetitors, type CompetitorChange } from "@/hooks/useCompetitors";
import { Radar, ArrowRight, TrendingUp } from "lucide-react";

function ChangeRow({
  change,
  name,
}: {
  change: CompetitorChange;
  name: string;
}) {
  return (
    <div className="flex items-start gap-3 px-6 py-3 hover:bg-muted/50 transition-colors">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warning-muted text-warning">
        <TrendingUp className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{name}</p>
        <p className="truncate text-xs text-muted-foreground">
          {change.field}: {(change.to || "").slice(0, 60)}
        </p>
      </div>
      <Badge variant={change.field === "pricingMentions" ? "destructive" : "secondary"} className="shrink-0 text-[10px]">
        {change.field === "pricingMentions" ? "prezzi" : change.field}
      </Badge>
    </div>
  );
}

export function CompetitorAlerts({ limit = 6 }: { limit?: number }) {
  const t = useTranslations("dashboard");
  const { data: changes, isLoading } = useCompetitorChanges();
  const { data: competitors } = useCompetitors();
  const recent = (changes || []).slice(0, limit);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Radar className="h-4 w-4 text-primary" />
            {t("competitorAlerts")}
          </CardTitle>
          <CardDescription className="mt-1">{t("competitorAlertsHint")}</CardDescription>
        </div>
        <Link
          href="/crm/competitors"
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {t("viewAll")} <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-2 px-6 py-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : !recent.length ? (
          <div className="px-6 py-8 text-center text-sm text-muted-foreground">
            {t("noCompetitorAlerts")}
          </div>
        ) : (
          <div className="divide-y">
            {recent.map((ch) => (
              <ChangeRow
                key={ch.id}
                change={ch}
                name={competitors?.find((c) => c.id === ch.competitorId)?.name || ch.competitorId}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
