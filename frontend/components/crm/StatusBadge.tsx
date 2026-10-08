import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-info-muted text-info",
  contacted: "bg-warning-muted text-warning",
  qualified: "bg-status-qualified-muted text-status-qualified",
  proposal: "bg-status-proposal-muted text-status-proposal",
  won: "bg-success-muted text-success",
  lost: "bg-destructive/10 text-destructive",
};

export function StatusBadge({ status }: { status?: string }) {
  const t = useTranslations("pipeline.stages");
  const key = (status ?? "new").toLowerCase();
  const color = STATUS_COLORS[key] || "bg-muted text-muted-foreground";

  // Map status key to translation key
  const labelMap: Record<string, string> = {
    new: t("new"),
    contacted: t("contacted"),
    qualified: t("qualified"),
    proposal: t("proposal"),
    won: t("won"),
    lost: t("lost"),
  };

  const label = labelMap[key] || status || "Unknown";

  return (
    <Badge variant="outline" className={cn("border-transparent font-medium", color)}>
      {label}
    </Badge>
  );
}