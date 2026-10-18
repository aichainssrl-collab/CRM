"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { CalendarClock, AlertTriangle, CalendarCheck, ArrowRight } from "lucide-react";
import type { DashboardMetrics, DueTask } from "@/hooks/useDashboard";

function formatDue(iso?: string | null) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function DueTasksCard({
  metrics,
  loading,
}: {
  metrics?: DashboardMetrics;
  loading?: boolean;
}) {
  const t = useTranslations("dashboard.dueTasks");
  const tasks = metrics?.dueTasks ?? [];
  const overdue = metrics?.overdueTasks ?? 0;
  const today = metrics?.dueTodayTasks ?? 0;
  const soon = metrics?.dueSoonTasks ?? 0;
  const hasAlert = overdue > 0 || today > 0;

  return (
    <Card className={hasAlert ? "border-destructive/40" : undefined}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className={`h-5 w-5 ${hasAlert ? "text-destructive" : "text-primary"}`} />
          {t("title")}
          {hasAlert && (
            <Badge variant="destructive" className="text-[10px]">
              {overdue + today}
            </Badge>
          )}
        </CardTitle>
        <CardDescription>{t("subtitle")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded-md border p-2">
                <div className="flex items-center justify-center gap-1 text-xs text-destructive">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  {t("overdue")}
                </div>
                <p className="text-xl font-semibold">{overdue}</p>
              </div>
              <div className="rounded-md border p-2">
                <div className="flex items-center justify-center gap-1 text-xs text-warning">
                  <CalendarClock className="h-3.5 w-3.5" />
                  {t("today")}
                </div>
                <p className="text-xl font-semibold">{today}</p>
              </div>
              <div className="rounded-md border p-2">
                <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
                  <CalendarCheck className="h-3.5 w-3.5" />
                  {t("week")}
                </div>
                <p className="text-xl font-semibold">{soon}</p>
              </div>
            </div>

            {tasks.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-2">{t("empty")}</p>
            ) : (
              <ul className="space-y-2">
                {tasks.slice(0, 6).map((task: DueTask) => (
                  <li
                    key={task.id}
                    className={`flex items-start justify-between gap-2 rounded-md border px-2.5 py-2 text-sm ${
                      task.isOverdue
                        ? "border-destructive/30 bg-destructive/5"
                        : task.isToday
                          ? "border-warning/30 bg-warning/5"
                          : ""
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium">{task.title || t("untitled")}</p>
                      <p className="text-xs text-muted-foreground">{formatDue(task.dueDate)}</p>
                    </div>
                    {task.isOverdue ? (
                      <Badge variant="destructive" className="text-[9px] shrink-0">
                        {t("overdue")}
                      </Badge>
                    ) : task.isToday ? (
                      <Badge variant="secondary" className="text-[9px] shrink-0">
                        {t("today")}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-[9px] shrink-0">
                        {task.priority || "—"}
                      </Badge>
                    )}
                  </li>
                ))}
              </ul>
            )}

            <Button variant="outline" size="sm" nativeButton={false} render={<Link href="/crm/tasks" />} className="w-full gap-1">
              {t("goToTasks")}
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
