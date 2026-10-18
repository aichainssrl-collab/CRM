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
    <Card className="group relative overflow-hidden shadow-card border-0 bg-card py-5 transition-transform duration-200 hover:-translate-y-0.5">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 px-5 pb-1">
        <CardTitle className="label-quiet pt-0.5">{title}</CardTitle>
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-xl ${accent ?? "bg-primary/8 text-primary"}`}
        >
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent className="px-5 pt-2">
        {loading ? (
          <Skeleton className="h-10 w-28 mb-1" />
        ) : (
          <div className="text-3xl font-semibold tracking-tight leading-none">{value}</div>
        )}
        {trend !== undefined && !loading && (
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground mt-3">
            <TrendIcon value={trend} />
            <span
              className={
                trend > 0 ? "text-success font-medium" : trend < 0 ? "text-destructive font-medium" : ""
              }
            >
              {trend > 0 ? "+" : ""}
              {trend}%
            </span>
            {trendLabel && <span>{trendLabel}</span>}
          </p>
        )}
      </CardContent>
      <div
        className={`absolute bottom-0 left-0 h-0.5 w-full opacity-0 transition-opacity duration-200 group-hover:opacity-100 ${accent ?? "bg-primary"}`}
      />
    </Card>
  );
}
