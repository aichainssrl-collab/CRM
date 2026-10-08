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
  const tFilters = useTranslations("leadFilters");

  return (
    <div className="flex flex-col sm:flex-row gap-4 mb-6">
      <div className="sm:max-w-xs w-full">
        <Input
          placeholder={t("search")}
          value={filters.search || ""}
          onChange={(e) => onChange("search", e.target.value)}
          aria-label={t("search")}
        />
      </div>
      <Select
        value={filters.status || "all"}
        onValueChange={(val: string | null) => onChange("status", val === "all" || !val ? undefined : val)}
      >
        <SelectTrigger className="w-[180px]" aria-label={t("status")}>
          <SelectValue placeholder={t("status")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{tFilters("allStatuses")}</SelectItem>
          <SelectItem value="new">{tPipeline("new")}</SelectItem>
          <SelectItem value="contacted">{tPipeline("contacted")}</SelectItem>
          <SelectItem value="qualified">{tPipeline("qualified")}</SelectItem>
        </SelectContent>
      </Select>
      <Select
        value={filters.score || "all"}
        onValueChange={(val: string | null) => onChange("score", val === "all" || !val ? undefined : val)}
      >
        <SelectTrigger className="w-[180px]" aria-label={t("score")}>
          <SelectValue placeholder={t("score")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{tFilters("anyScore")}</SelectItem>
          <SelectItem value="high">{tFilters("highScore")}</SelectItem>
          <SelectItem value="medium">{tFilters("mediumScore")}</SelectItem>
          <SelectItem value="low">{tFilters("lowScore")}</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}