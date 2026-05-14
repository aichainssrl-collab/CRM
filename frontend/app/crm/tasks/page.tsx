"use client";

import { useState } from "react";
import { useTasks } from "@/hooks/useTasks";
import { TaskList } from "@/components/crm/TaskList";
import { TaskForm } from "@/components/crm/TaskForm";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

export default function TasksPage() {
  const [tab, setTab] = useState<"all" | "pending" | "completed">("all");
  const [dueToday, setDueToday] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

  const todayISO = new Date().toISOString().split("T")[0] + "T23:59:59Z";

  const status = tab === "all" ? undefined : tab;
  const dueBefore = dueToday ? todayISO : undefined;

  const { data: tasks, isLoading } = useTasks(undefined, status, dueBefore);

  return (
    <main className="flex-1 flex flex-col p-8 bg-surface-container-low min-h-0">
      <div className="flex items-center justify-between mb-6 shrink-0">
        <h1 className="text-h1 font-h1 text-on-surface">Tasks</h1>
        <Button
          className="h-input_height px-4 bg-[#3B5BDB] text-white font-small-medium hover:bg-[#3B5BDB]/90 flex gap-2 shadow-sm"
          onClick={() => setFormOpen(true)}
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          Nuovo Task
        </Button>
      </div>

      <div className="flex items-center gap-4 mb-6 shrink-0">
        <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
          </TabsList>
        </Tabs>
        <button
          onClick={() => setDueToday((d) => !d)}
          className={`px-3 py-1 text-sm rounded-full border transition-colors ${
            dueToday
              ? "bg-[#3B5BDB] text-white border-[#3B5BDB]"
              : "bg-surface-container-lowest border-outline-variant text-on-surface-variant hover:bg-surface-container"
          }`}
        >
          Scaduti oggi
        </button>
      </div>

      <div className="flex-1 min-h-0">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full rounded-md" />
            <Skeleton className="h-16 w-full rounded-md" />
            <Skeleton className="h-16 w-full rounded-md" />
          </div>
        ) : !tasks || tasks.length === 0 ? (
          <div className="text-center py-16 text-on-surface-variant border border-dashed border-outline-variant rounded-lg bg-surface-container-lowest">
            <span className="material-symbols-outlined text-[40px] text-outline mb-3 block">task_alt</span>
            <p className="text-body-medium">Nessun task trovato.</p>
          </div>
        ) : (
          <TaskList tasks={tasks} />
        )}
      </div>

      <TaskForm open={formOpen} onOpenChange={setFormOpen} />
    </main>
  );
}
