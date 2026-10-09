"use client";

import { useActivityFeed, type ActivityItem } from "@/hooks/useNotifications";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  UserPlus, Briefcase, CheckSquare, Calendar, Mail,
  Activity, Star, ArrowRight,
} from "lucide-react";

const ACTION_ICONS: Record<string, React.ElementType> = {
  "lead.created": UserPlus,
  "lead.updated": UserPlus,
  "deal.created": Briefcase,
  "deal.won": Briefcase,
  "deal.lost": Briefcase,
  "task.completed": CheckSquare,
  "task.created": CheckSquare,
  "booking.created": Calendar,
  "sequence.enrolled": Mail,
  "report.generated": Activity,
  "score.updated": Star,
};

const ACTION_COLORS: Record<string, string> = {
  "lead.created": "bg-info-muted text-info",
  "deal.won": "bg-success-muted text-success",
  "deal.lost": "bg-destructive-muted text-destructive",
  "task.completed": "bg-success-muted text-success",
  "booking.created": "bg-status-proposal-muted text-status-proposal",
  "sequence.enrolled": "bg-warning-muted text-warning",
};

function formatTime(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "ora";
  if (diffMin < 60) return `${diffMin}m fa`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h fa`;
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

function FeedItem({ item }: { item: ActivityItem }) {
  const Icon = ACTION_ICONS[item.action] || Activity;
  const colorClass = ACTION_COLORS[item.action] || "bg-muted text-muted-foreground";

  return (
    <div className="flex items-start gap-3 py-2.5">
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${colorClass}`}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm">{item.description || item.action}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          <span className="font-medium">{item.userName}</span> · {formatTime(item.createdAt)}
        </p>
      </div>
    </div>
  );
}

export function ActivityFeed({ limit = 20, showHeader = true }: { limit?: number; showHeader?: boolean }) {
  const { data: activities, isLoading } = useActivityFeed(limit);

  return (
    <Card>
      {showHeader && (
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Attività Recenti</CardTitle>
              <CardDescription>Ultime azioni del team</CardDescription>
            </div>
          </div>
        </CardHeader>
      )}
      <CardContent className={showHeader ? "" : "pt-4"}>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full rounded" />)}
          </div>
        ) : !activities?.length ? (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
            <Activity className="h-8 w-8 text-muted-foreground/30" />
            <p className="text-xs">Nessuna attività recente</p>
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {activities.map((item) => (
              <FeedItem key={item.id} item={item} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}