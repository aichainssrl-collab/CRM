"use client";

import { useState } from "react";
import { Task, useCreateTask, useUpdateTask } from "@/hooks/useTasks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";

interface TaskFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task?: Task | null;
  leadId?: string;
}

export function TaskForm({ open, onOpenChange, task, leadId }: TaskFormProps) {
  const [loading, setLoading] = useState(false);
  const [formLeadId, setFormLeadId] = useState(leadId || task?.leadId || "");
  const actualLeadId = leadId || task?.leadId || formLeadId;
  const { mutateAsync: createTask } = useCreateTask(actualLeadId);
  const { mutateAsync: updateTask } = useUpdateTask(actualLeadId);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    
    const data = {
      title: formData.get("title") as string,
      description: formData.get("description") as string,
      dueDate: formData.get("dueDate") as string,
      type: "todo",
      priority: "normal",
      assignedTo: "user_1", // Mock assigned to self
    };

    try {
      if (task) {
        await updateTask({ id: task.id, data });
      } else {
        await createTask(data);
      }
      onOpenChange(false);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{task ? "Edit Task" : "Add New Task"}</SheetTitle>
          <SheetDescription>
            {task ? "Update task details below." : "Create a new task to track."}
          </SheetDescription>
        </SheetHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6 py-6">
          {!leadId && !task && (
            <div className="space-y-2">
              <label htmlFor="leadId" className="text-sm font-medium">Lead ID *</label>
              <Input
                id="leadId"
                name="leadId"
                required
                placeholder="es. abc123"
                value={formLeadId}
                onChange={(e) => setFormLeadId(e.target.value)}
              />
            </div>
          )}
          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium">Title *</label>
            <Input 
              id="title" 
              name="title" 
              required 
              defaultValue={task?.title} 
            />
          </div>
          
          <div className="space-y-2">
            <label htmlFor="dueDate" className="text-sm font-medium">Due Date *</label>
            <Input 
              id="dueDate" 
              name="dueDate" 
              type="datetime-local"
              required 
              defaultValue={task?.dueDate ? new Date(task.dueDate).toISOString().slice(0, 16) : ""} 
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium">Description</label>
            <Textarea 
              id="description" 
              name="description" 
              defaultValue={task?.description} 
              rows={3}
            />
          </div>

          <SheetFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Save Task"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
