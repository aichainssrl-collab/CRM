"use client";

import { Lead } from "@/hooks/useLeads";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "./StatusBadge";
import { LeadScoreBadge } from "./LeadScoreBadge";
import { MoreHorizontal, Eye, Edit, Trash } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

interface LeadTableProps {
  leads: Lead[];
  isLoading: boolean;
  onEdit: (lead: Lead) => void;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

export function LeadTable({ leads, isLoading, onEdit, onDelete, onView }: LeadTableProps) {
  if (isLoading) {
    return (
      <div className="border rounded-md p-8 text-center text-muted-foreground animate-pulse">
        Loading leads...
      </div>
    );
  }

  if (!leads.length) {
    return (
      <div className="border rounded-md p-12 text-center">
        <h3 className="text-lg font-medium">No leads found</h3>
        <p className="text-muted-foreground mt-1">Adjust your filters or add a new lead.</p>
      </div>
    );
  }

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Company</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Score</TableHead>
            <TableHead className="w-[80px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {leads.map((lead) => (
            <TableRow key={lead.id}>
              <TableCell className="font-medium">
                {lead.firstName || lead.lastName 
                  ? `${lead.firstName || ""} ${lead.lastName || ""}`.trim() 
                  : "-"}
              </TableCell>
              <TableCell>{lead.email}</TableCell>
              <TableCell>{lead.companyName || "-"}</TableCell>
              <TableCell>
                <StatusBadge status={lead.pipelineStage} />
              </TableCell>
              <TableCell className="text-right">
                <LeadScoreBadge score={lead.leadScore} />
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger className="h-8 w-8 p-0 outline-none focus:ring-2 focus:ring-primary rounded-md flex items-center justify-center">
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onView(lead.id)}>
                      <Eye className="mr-2 h-4 w-4" /> View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEdit(lead)}>
                      <Edit className="mr-2 h-4 w-4" /> Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onDelete(lead.id)} className="text-destructive focus:text-destructive">
                      <Trash className="mr-2 h-4 w-4" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
