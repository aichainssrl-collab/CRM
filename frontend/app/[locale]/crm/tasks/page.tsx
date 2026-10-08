"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useTasks } from "@/hooks/useTasks";
import { TaskList } from "@/components/crm/TaskList";
import { TaskForm } from "@/components/crm/TaskForm";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, ClipboardCheck } from "lucide-react";

export default function TasksPage() {
  const t = useTranslations("tasks");
  const [tab, setTab] = useState<"all" | "pending" | "completed">("all");
  const [dueToday, setDueToday] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

  const todayISO = new Date().toISOString().split("T")[0] + "T23:59:59Z";

  const status = tab === "all" ? undefined : tab;
  const dueBefore = dueToday ? todayISO : undefined;

  const { data: tasks, isLoading } = useTasks(undefined, status, dueBefore);

  const tabs: { label: string; value: typeof tab }[] = [
    { label: t("all"), value: "all" },
    { label: t("inProgress"), value: "pending" },
    { label: t("completed"), value: "completed" },
  ];

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>
        <Button onClick={() => setFormOpen(true)} className="gap-2 self-start sm:self-auto">
          <Plus className="h-4 w-4" />
          {t("newTask")}
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Tabs value={tab} onValueChange={(v) => v && setTab(v as typeof tab)}>
          <TabsList>
            {tabs.map((tabItem) => (
              <TabsTrigger key={tabItem.value} value={tabItem.value}>
                {tabItem.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <Button
          variant={dueToday ? "secondary" : "outline"}
          size="sm"
          onClick={() => setDueToday((d) => !d)}
        >
          {t("dueToday")}
        </Button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-16 w-full rounded-md" />
          <Skeleton className="h-16 w-full rounded-md" />
          <Skeleton className="h-16 w-full rounded-md" />
        </div>
      ) : !tasks || tasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-16 text-center">
          <ClipboardCheck className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">{t("noTasks")}</p>
          <Button variant="outline" size="sm" onClick={() => setFormOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            {t("createFirst")}
          </Button>
        </div>
      ) : (
        <TaskList tasks={tasks} />
      )}

      <TaskForm open={formOpen} onOpenChange={setFormOpen} />
    </div>
  );
}