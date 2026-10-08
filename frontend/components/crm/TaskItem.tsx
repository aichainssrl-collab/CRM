"use client";

import { Task, useUpdateTask, useDeleteTask } from "@/hooks/useTasks";
import { useTranslations } from "next-intl";
import { Checkbox } from "@/components/ui/checkbox";
import { Calendar, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function TaskItem({ task }: { task: Task }) {
  const t = useTranslations("taskItem");
  const { mutate: updateTask } = useUpdateTask(task.leadId);
  const { mutate: deleteTask } = useDeleteTask(task.leadId);

  const handleToggle = () => {
    updateTask({
      id: task.id,
      data: {
        completedAt: task.completedAt ? undefined : new Date().toISOString(),
      }
    });
  };

  const isOverdue = !task.completedAt && new Date(task.dueDate) < new Date();

  return (
    <div className="flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors">
      <Checkbox
        checked={!!task.completedAt}
        onCheckedChange={handleToggle}
        aria-label={task.completedAt ? t("markIncomplete") : t("markComplete")}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <span className={`text-sm font-medium ${task.completedAt ? "line-through text-muted-foreground" : ""}`}>
          {task.title}
        </span>
        <div className="flex items-center gap-4 mt-1">
          <div className={`flex items-center gap-1 text-xs ${isOverdue ? "text-destructive font-medium" : "text-muted-foreground"}`}>
            <Calendar className="h-3 w-3" />
            {new Date(task.dueDate).toLocaleDateString()}
          </div>
          {task.assignedTo && (
            <div className="text-xs text-muted-foreground">
              {t("assignedTo")}: {task.assignedTo}
            </div>
          )}
        </div>
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="text-muted-foreground hover:text-destructive"
        onClick={() => deleteTask(task.id)}
        aria-label={t("deleteTask")}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}
