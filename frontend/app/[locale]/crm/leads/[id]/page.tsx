"use client";

import { useLead } from "@/hooks/useLeads";
import { useActivities } from "@/hooks/useActivities";
import { useTasks } from "@/hooks/useTasks";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { LeadDetail } from "@/components/crm/LeadDetail";
import { ActivityTimeline } from "@/components/crm/ActivityTimeline";
import { AddActivityForm } from "@/components/crm/AddActivityForm";
import { TaskList } from "@/components/crm/TaskList";
import { TaskForm } from "@/components/crm/TaskForm";
import { GdprConsentLog } from "@/components/crm/GdprConsentLog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const { data: lead, isLoading: isLoadingLead } = useLead(id);
  const { data: activities = [] } = useActivities(id);
  const { data: tasks = [] } = useTasks(id);
  
  const { data: gdprData } = useQuery({
    queryKey: ["gdpr", id],
    queryFn: async () => {
      // Usiamo il casting al tipo corretto previsto dal GdprConsentLog
      return apiFetch(`/api/v1/gdpr/${id}/export`) as Promise<{ consents: Array<{ id: string, leadId: string, action: string, purpose: string, timestamp: string, ipAddress?: string, userAgent?: string }> }>;
    },
    enabled: !!id,
  });
  
  const [isTaskFormOpen, setIsTaskFormOpen] = useState(false);

  if (isLoadingLead) {
    return (
      <main className="flex-1 overflow-y-auto p-8 flex items-center justify-center h-[calc(100vh-56px)]">
        <div className="animate-pulse text-muted-foreground">Loading lead details...</div>
      </main>
    );
  }

  if (!lead) {
    return (
      <main className="flex-1 overflow-y-auto p-8 flex flex-col items-center justify-center h-[calc(100vh-56px)]">
        <h2 className="text-xl font-medium mb-2">Lead not found</h2>
        <Link href="/crm/leads">
          <Button variant="outline"><ArrowLeft className="mr-2 h-4 w-4" /> Back to Leads</Button>
        </Link>
      </main>
    );
  }

  return (
    <main className="flex-1 overflow-y-auto p-container_padding bg-surface h-[calc(100vh-56px)]">
      <div className="max-w-[1200px] mx-auto flex flex-col gap-6">
        {/* Header Navigation */}
        <div>
          <Link href="/crm/leads" className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1 mb-4">
            <ArrowLeft className="h-4 w-4" /> Back to leads
          </Link>
          <LeadDetail lead={lead} />
        </div>

        {/* Tabs for content */}
        <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
          <Tabs defaultValue="activity" className="w-full">
            <TabsList className="mb-6 w-full justify-start border-b rounded-none h-auto p-0 bg-transparent">
              <TabsTrigger value="activity" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Activity</TabsTrigger>
              <TabsTrigger value="tasks" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">Tasks</TabsTrigger>
              <TabsTrigger value="gdpr" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">GDPR</TabsTrigger>
            </TabsList>
            
            <TabsContent value="activity" className="space-y-8">
              <AddActivityForm leadId={id} />
              <div className="pt-4">
                <h3 className="text-lg font-medium mb-4">Timeline</h3>
                <ActivityTimeline activities={activities} />
              </div>
            </TabsContent>
            
            <TabsContent value="tasks" className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Tasks ({tasks.length})</h3>
                <Button onClick={() => setIsTaskFormOpen(true)} size="sm">
                  <Plus className="h-4 w-4 mr-2" /> Add Task
                </Button>
              </div>
              <TaskList tasks={tasks} />
              <TaskForm 
                open={isTaskFormOpen} 
                onOpenChange={setIsTaskFormOpen} 
                leadId={id} 
              />
            </TabsContent>

            <TabsContent value="gdpr" className="space-y-6">
              <h3 className="text-lg font-medium">Consent Audit Trail</h3>
              <GdprConsentLog logs={gdprData?.consents || []} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </main>
  );
}