import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  new: { label: "New", color: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400" },
  contacted: { label: "Contacted", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400" },
  qualified: { label: "Qualified", color: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400" },
  proposal: { label: "Proposal", color: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400" },
  won: { label: "Won", color: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400" },
  lost: { label: "Lost", color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400" },
};

export function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status.toLowerCase()] || {
    label: status,
    color: "bg-muted text-muted-foreground",
  };

  return (
    <Badge variant="outline" className={cn("border-transparent font-medium", config.color)}>
      {config.label}
    </Badge>
  );
}
