"use client";

import { Task } from "@/hooks/useTasks";
import { TaskItem } from "@/components/crm/TaskItem";

export function TaskList({ tasks }: { tasks: Task[] }) {
  return (
    <div className="border rounded-md divide-y">
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} />
      ))}
    </div>
  );
}
