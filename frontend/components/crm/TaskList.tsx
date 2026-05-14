"use client";

import { Task } from "@/hooks/useTasks";
import { TaskItem } from "@/components/crm/TaskItem";
import { useState } from "react";

export function TaskList({ tasks }: { tasks: Task[] }) {
  const [filter, setFilter] = useState("all");

  const filteredTasks = tasks.filter(task => {
    if (filter === "completed") return task.completedAt;
    if (filter === "pending") return !task.completedAt;
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button 
          onClick={() => setFilter("all")} 
          className={`px-3 py-1 text-sm rounded-full ${filter === "all" ? "bg-primary text-primary-foreground" : "bg-muted"}`}
        >
          All
        </button>
        <button 
          onClick={() => setFilter("pending")} 
          className={`px-3 py-1 text-sm rounded-full ${filter === "pending" ? "bg-primary text-primary-foreground" : "bg-muted"}`}
        >
          Pending
        </button>
        <button 
          onClick={() => setFilter("completed")} 
          className={`px-3 py-1 text-sm rounded-full ${filter === "completed" ? "bg-primary text-primary-foreground" : "bg-muted"}`}
        >
          Completed
        </button>
      </div>
      
      {!filteredTasks.length ? (
        <div className="text-center py-8 text-muted-foreground border border-dashed rounded-lg bg-muted/20">
          No tasks found.
        </div>
      ) : (
        <div className="border rounded-md divide-y">
          {filteredTasks.map(task => (
            <TaskItem key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
