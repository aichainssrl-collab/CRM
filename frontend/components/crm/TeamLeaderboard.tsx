"use client";

import { useLeaderboard, type LeaderboardUser } from "@/hooks/useCalendar";
import { formatEUR } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Trophy, Medal, Users } from "lucide-react";

const RANK_STYLES = [
  "bg-warning/15 text-warning border-warning/30",
  "bg-muted text-muted-foreground border-border",
  "bg-chart-2/15 text-chart-2 border-chart-2/30",
];

function LeaderboardRow({ user, rank }: { user: LeaderboardUser; rank: number }) {
  return (
    <div className="flex items-center gap-3 py-2.5">
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold border ${RANK_STYLES[rank] || "bg-muted text-muted-foreground"}`}>
        {rank + 1}
      </div>
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-semibold">
        {user.userName.charAt(0).toUpperCase()}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium truncate">{user.userName}</p>
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
          <span>{user.dealsWon} deal</span>
          <span>{user.tasksCompleted} task</span>
          <span>{user.leadsAssigned} lead</span>
        </div>
      </div>
      <div className="text-right shrink-0">
        <p className="text-sm font-semibold tabular-nums">{formatEUR(user.revenue)}</p>
        <p className="text-[10px] text-muted-foreground">score {Math.round(user.score)}</p>
      </div>
    </div>
  );
}

export function TeamLeaderboard({ days = 30 }: { days?: number }) {
  const { data: leaderboard, isLoading } = useLeaderboard(days);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Trophy className="h-4 w-4 text-warning" />
              <CardTitle className="text-base">Team Leaderboard</CardTitle>
            </div>
            <CardDescription>Performance ultimi {days} giorni</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full rounded" />)}
          </div>
        ) : !leaderboard?.length ? (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
            <Users className="h-8 w-8 text-muted-foreground/30" />
            <p className="text-xs">Nessun dato performance</p>
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {leaderboard.slice(0, 8).map((user, i) => (
              <LeaderboardRow key={user.userId} user={user} rank={i} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}