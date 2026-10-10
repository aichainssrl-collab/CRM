"use client";

import { useLead } from "@/hooks/useLeads";
import { useActivities } from "@/hooks/useActivities";
import { useTasks } from "@/hooks/useTasks";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { apiFetch } from "@/lib/api";
import { LeadDetail } from "@/components/crm/LeadDetail";
import { ActivityTimeline } from "@/components/crm/ActivityTimeline";
import { AddActivityForm } from "@/components/crm/AddActivityForm";
import { TaskList } from "@/components/crm/TaskList";
import { TaskForm } from "@/components/crm/TaskForm";
import { GdprConsentLog } from "@/components/crm/GdprConsentLog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Plus, Users } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { useState } from "react";

function LeadDetailSkeleton() {
  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1200px] mx-auto w-full">
      <Skeleton className="h-5 w-32" />
      <div className="border rounded-lg p-6 space-y-4">
        <div className="flex items-center gap-4">
          <Skeleton className="h-14 w-14 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-md" />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const t = useTranslations("leadDetail");
  const { data: lead, isLoading: isLoadingLead } = useLead(id);
  const { data: activities = [] } = useActivities(id);
  const { data: tasks = [] } = useTasks(id);

  const { data: gdprData } = useQuery({
    queryKey: ["gdpr", id],
    queryFn: async () => {
      return apiFetch(`/api/v1/gdpr/${id}/export`) as Promise<{ consents: Array<{ id: string, leadId: string, action: string, purpose: string, timestamp: string, ipAddress?: string, userAgent?: string }> }>;
    },
    enabled: !!id,
  });

  const [isTaskFormOpen, setIsTaskFormOpen] = useState(false);

  if (isLoadingLead) {
    return <LeadDetailSkeleton />;
  }

  if (!lead) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
        <Users className="h-12 w-12 text-muted-foreground/30" />
        <h2 className="text-lg font-medium">{t("leadNotFound")}</h2>
        <Link href="/crm/leads">
          <Button variant="outline" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" /> {t("backToLeads")}
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1200px] mx-auto w-full">
      <div>
        <Link href="/crm/leads" className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1 mb-4 transition-colors">
          <ArrowLeft className="h-4 w-4" /> {t("backToLeads")}
        </Link>
        <LeadDetail lead={lead} />
      </div>

      <div className="bg-card border rounded-lg p-6">
        <Tabs defaultValue="activity" className="w-full">
          <TabsList className="mb-6 w-full justify-start border-b rounded-none h-auto p-0 bg-transparent">
            <TabsTrigger value="activity" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">
              {t("activity")}
            </TabsTrigger>
            <TabsTrigger value="tasks" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">
              {t("tasks")}
            </TabsTrigger>
            <TabsTrigger value="gdpr" className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent">
              GDPR
            </TabsTrigger>
          </TabsList>

          <TabsContent value="activity" className="space-y-8">
            <AddActivityForm leadId={id} />
            <div className="pt-4">
              <h3 className="text-lg font-medium mb-4">{t("timeline")}</h3>
              <ActivityTimeline activities={activities} />
            </div>
          </TabsContent>

          <TabsContent value="tasks" className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">{t("taskCount", { count: tasks.length })}</h3>
              <Button onClick={() => setIsTaskFormOpen(true)} size="sm" className="gap-2">
                <Plus className="h-4 w-4" /> {t("addTask")}
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
            <h3 className="text-lg font-medium">{t("consentAudit")}</h3>
            <GdprConsentLog logs={gdprData?.consents || []} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}