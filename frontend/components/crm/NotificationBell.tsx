"use client";

import { useState } from "react";
import { useRouter } from "@/i18n/navigation";
import { Bell, CheckCheck, Check, Info, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNotifications, useUnreadCount, useMarkRead, useMarkAllRead, type Notification } from "@/hooks/useNotifications";

const KIND_ICONS: Record<string, React.ElementType> = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: XCircle,
};

const KIND_COLORS: Record<string, string> = {
  info: "text-info",
  success: "text-success",
  warning: "text-warning",
  error: "text-destructive",
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
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
}

function NotificationItem({ notif, onRead }: { notif: Notification; onRead: (id: string) => void }) {
  const router = useRouter();
  const Icon = KIND_ICONS[notif.kind] || Info;
  const unread = !notif.readAt;

  return (
    <div
      className={`flex gap-3 px-4 py-3 hover:bg-muted/50 transition-colors cursor-pointer border-b border-border/50 last:border-0 ${unread ? "bg-primary/5" : ""}`}
      onClick={() => {
        if (notif.link) router.push(notif.link);
        if (unread) onRead(notif.id);
      }}
    >
      <div className={`mt-0.5 shrink-0 ${KIND_COLORS[notif.kind] || "text-muted-foreground"}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className={`text-sm ${unread ? "font-medium" : ""}`}>{notif.title}</p>
          {unread && <div className="h-2 w-2 shrink-0 rounded-full bg-primary mt-1" />}
        </div>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{notif.body}</p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">{formatTime(notif.createdAt)}</p>
      </div>
    </div>
  );
}

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const { data: notifications = [] } = useNotifications();
  const { data: unreadCount = 0 } = useUnreadCount();
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger
        render={<Button variant="ghost" size="icon" className="relative h-9 w-9" />}
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <Badge
            className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-[10px] bg-destructive text-destructive-foreground"
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </Badge>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="w-80 p-0"
        side="bottom"
        align="end"
        sideOffset={4}
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <p className="text-sm font-semibold">Notifiche</p>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs gap-1"
              onClick={() => markAllRead.mutate()}
            >
              <CheckCheck className="h-3 w-3" />
              Segna tutte
            </Button>
          )}
        </div>
        <div className="max-h-80 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
              <Bell className="h-8 w-8 text-muted-foreground/30" />
              <p className="text-xs">Nessuna notifica</p>
            </div>
          ) : (
            notifications.map((n) => (
              <NotificationItem key={n.id} notif={n} onRead={(id) => markRead.mutate(id)} />
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}