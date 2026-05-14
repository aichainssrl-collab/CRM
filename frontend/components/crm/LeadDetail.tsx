"use client";

import { Lead } from "@/hooks/useLeads";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { StatusBadge } from "./StatusBadge";
import { LeadScoreBadge } from "./LeadScoreBadge";
import { Mail, Phone, Building, Calendar, User } from "lucide-react";

export function LeadDetail({ lead }: { lead: Lead }) {
  const fullName = lead.firstName || lead.lastName ? `${lead.firstName || ""} ${lead.lastName || ""}`.trim() : "Unknown Name";
  const initial = lead.firstName ? lead.firstName.charAt(0) : (lead.email.charAt(0).toUpperCase());

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between pb-4">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="text-xl">{initial}</AvatarFallback>
          </Avatar>
          <div>
            <CardTitle className="text-2xl">{fullName}</CardTitle>
            <div className="flex items-center gap-2 mt-2">
              <StatusBadge status={lead.pipelineStage} />
              <LeadScoreBadge score={lead.leadScore} />
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Mail className="h-4 w-4" />
            <a href={`mailto:${lead.email}`} className="text-foreground hover:underline">{lead.email}</a>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Phone className="h-4 w-4" />
            <span className="text-foreground">{lead.phone || "No phone"}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Building className="h-4 w-4" />
            <span className="text-foreground">{lead.companyName || "No company"}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <User className="h-4 w-4" />
            <span className="text-foreground">Assignee: {lead.assignedTo || "Unassigned"}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span className="text-foreground">Added: {new Date(lead.createdAt).toLocaleDateString()}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
