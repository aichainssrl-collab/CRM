import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  contacted: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  qualified: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
  proposal: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  won: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  lost: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
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