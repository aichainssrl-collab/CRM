"use client";

import { Lead } from "@/hooks/useLeads";
import { useTranslations } from "next-intl";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { StatusBadge } from "./StatusBadge";
import { LeadScoreBadge } from "./LeadScoreBadge";
import { MoreHorizontal, Eye, Edit, Trash } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

interface LeadTableProps {
  leads: Lead[];
  isLoading: boolean;
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onToggleAll: () => void;
  onEdit: (lead: Lead) => void;
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

export function LeadTable({ leads, isLoading, selectedIds, onToggleSelect, onToggleAll, onEdit, onDelete, onView }: LeadTableProps) {
  const t = useTranslations("leads");
  const tCommon = useTranslations("common");

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-muted-foreground animate-pulse">
        {tCommon("loading")}
      </div>
    );
  }

  if (!leads.length) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
        <h3 className="text-lg font-medium">{t("noLeads")}</h3>
        <p className="text-muted-foreground mt-1">{t("noLeadsDesc")}</p>
      </div>
    );
  }

  const allSelected = leads.length > 0 && leads.every((l) => selectedIds.has(l.id));
  const someSelected = leads.some((l) => selectedIds.has(l.id));

  return (
    <div className="flex-1 overflow-auto min-w-0">
      <Table className="table-fixed w-full">
        <TableHeader>
          <TableRow>
            <TableHead className="w-10 shrink-0">
              <Checkbox
                checked={allSelected}
                data-state={someSelected && !allSelected ? "indeterminate" : undefined}
                onCheckedChange={onToggleAll}
                aria-label={t("selectAll")}
              />
            </TableHead>
            <TableHead className="w-[170px] max-w-[170px]">{t("name")}</TableHead>
            <TableHead className="w-[200px] max-w-[200px]">{t("email")}</TableHead>
            <TableHead className="w-[160px] max-w-[160px]">{t("company")}</TableHead>
            <TableHead className="w-[120px]">{t("phone")}</TableHead>
            <TableHead className="w-[120px]">{t("sector")}</TableHead>
            <TableHead className="w-[130px]">{t("role")}</TableHead>
            <TableHead className="w-[100px]">{t("status")}</TableHead>
            <TableHead className="w-[70px] text-right">{t("score")}</TableHead>
            <TableHead className="w-10"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {leads.map((lead) => (
            <TableRow
              key={lead.id}
              data-selected={selectedIds.has(lead.id)}
              className={selectedIds.has(lead.id) ? "bg-primary/5" : undefined}
            >
              <TableCell className="shrink-0">
                <Checkbox
                  checked={selectedIds.has(lead.id)}
                  onCheckedChange={() => onToggleSelect(lead.id)}
                  aria-label={`${t("selectLead")} ${lead.firstName ?? lead.email}`}
                />
              </TableCell>
              <TableCell className="max-w-[170px]">
                <span className="block truncate font-medium">
                  {lead.firstName || lead.lastName
                    ? `${lead.firstName || ""} ${lead.lastName || ""}`.trim()
                    : "-"}
                </span>
              </TableCell>
              <TableCell className="max-w-[200px]">
                <span className="block truncate text-muted-foreground">{lead.email.includes("@placeholder") ? "-" : lead.email}</span>
              </TableCell>
              <TableCell className="max-w-[160px]">
                <span className="block truncate">{lead.companyName || "-"}</span>
              </TableCell>
              <TableCell>
                <span className="text-sm text-muted-foreground">{lead.phone || "-"}</span>
              </TableCell>
              <TableCell>
                {lead.industry ? (
                  <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                    {lead.industry}
                  </span>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell>
                <span className="text-sm">{lead.roleTitle || "-"}</span>
              </TableCell>
              <TableCell>
                <StatusBadge status={lead.pipelineStage} />
              </TableCell>
              <TableCell className="text-right">
                <LeadScoreBadge score={lead.leadScore} />
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger className="h-8 w-8 p-0 outline-none focus:ring-2 focus:ring-primary rounded-md flex items-center justify-center">
                    <span className="sr-only">{tCommon("actions")}</span>
                    <MoreHorizontal className="h-4 w-4" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onView(lead.id)}>
                      <Eye className="mr-2 h-4 w-4" /> {tCommon("viewDetails")}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEdit(lead)}>
                      <Edit className="mr-2 h-4 w-4" /> {tCommon("edit")}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onDelete(lead.id)} className="text-destructive focus:text-destructive">
                      <Trash className="mr-2 h-4 w-4" /> {tCommon("delete")}
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