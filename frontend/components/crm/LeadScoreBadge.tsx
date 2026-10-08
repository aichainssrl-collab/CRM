import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export function LeadScoreBadge({ score }: { score: number }) {
  let colorClass = "bg-muted text-muted-foreground";

  if (score >= 80) {
    colorClass = "bg-success-muted text-success";
  } else if (score >= 50) {
    colorClass = "bg-warning-muted text-warning";
  } else if (score > 0) {
    colorClass = "bg-destructive/10 text-destructive";
  }

  return (
    <Badge variant="outline" className={cn("font-bold border-transparent", colorClass)}>
      {score > 0 ? score : "N/A"}
    </Badge>
  );
}