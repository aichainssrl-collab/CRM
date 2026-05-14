import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export function LeadScoreBadge({ score }: { score: number }) {
  let colorClass = "bg-muted text-muted-foreground";
  
  if (score >= 80) {
    colorClass = "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
  } else if (score >= 50) {
    colorClass = "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
  } else if (score > 0) {
    colorClass = "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
  }

  return (
    <Badge variant="outline" className={cn("font-bold border-transparent", colorClass)}>
      {score > 0 ? score : "N/A"}
    </Badge>
  );
}
