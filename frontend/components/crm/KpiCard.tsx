import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

function TrendIcon({ value }: { value?: number }) {
  if (value === undefined) return <Minus className="h-3 w-3 text-muted-foreground" />;
  if (value > 0) return <TrendingUp className="h-3 w-3 text-success" />;
  if (value < 0) return <TrendingDown className="h-3 w-3 text-destructive" />;
  return <Minus className="h-3 w-3 text-muted-foreground" />;
}

export function KpiCard({
  title,
  value,
  trend,
  trendLabel,
  icon: Icon,
  loading,
  accent,
}: {
  title: string;
  value: string;
  trend?: number;
  trendLabel?: string;
  icon: React.ElementType;
  loading: boolean;
  accent?: string;
}) {
  return (
    <Card className="group relative overflow-hidden transition-shadow duration-200 hover:shadow-md hover:shadow-primary/5">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-[13px] font-medium text-muted-foreground">{title}</CardTitle>
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${accent ?? "bg-primary/8 text-primary"}`}>
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-28 mb-1" />
        ) : (
          <div className="text-2xl font-bold tracking-tight">{value}</div>
        )}
        {trend !== undefined && !loading && (
          <p className="flex items-center gap-1 text-xs text-muted-foreground mt-1.5">
            <TrendIcon value={trend} />
            <span className={trend > 0 ? "text-success font-medium" : trend < 0 ? "text-destructive font-medium" : ""}>
              {trend > 0 ? "+" : ""}{trend}%
            </span>
            {trendLabel && <span>{trendLabel}</span>}
          </p>
        )}
      </CardContent>
      <div className={`absolute bottom-0 left-0 h-0.5 w-full opacity-0 transition-opacity duration-200 group-hover:opacity-100 ${accent ?? "bg-primary"}`} />
    </Card>
  );
}