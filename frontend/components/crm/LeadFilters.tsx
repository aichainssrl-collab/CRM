"use client";

import { useTranslations } from "next-intl";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface LeadFiltersProps {
  filters: Record<string, string>;
  onChange: (key: string, value: string | undefined) => void;
}

export function LeadFilters({ filters, onChange }: LeadFiltersProps) {
  const t = useTranslations("leads");
  const tPipeline = useTranslations("pipeline.stages");

  return (
    <div className="flex flex-col sm:flex-row gap-4 mb-6">
      <div className="sm:max-w-xs w-full">
        <Input 
          placeholder={t("search")}
          value={filters.search || ""}
          onChange={(e) => onChange("search", e.target.value)}
        />
      </div>
      <Select 
        value={filters.status || "all"} 
        onValueChange={(val: string | null) => onChange("status", val === "all" || !val ? undefined : val)}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder={t("status")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="new">{tPipeline("new")}</SelectItem>
          <SelectItem value="contacted">{tPipeline("contacted")}</SelectItem>
          <SelectItem value="qualified">{tPipeline("qualified")}</SelectItem>
        </SelectContent>
      </Select>
      <Select 
        value={filters.score || "all"} 
        onValueChange={(val: string | null) => onChange("score", val === "all" || !val ? undefined : val)}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder={t("score")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Any Score</SelectItem>
          <SelectItem value="high">High (&gt;80)</SelectItem>
          <SelectItem value="medium">Medium (50-79)</SelectItem>
          <SelectItem value="low">Low (&lt;50)</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}