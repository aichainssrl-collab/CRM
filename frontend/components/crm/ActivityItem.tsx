import { Activity } from "@/hooks/useActivities";
import { MessageSquare, Phone, Mail, Calendar, FileText, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

const ICONS: Record<string, React.ElementType> = {
  note: FileText,
  call: Phone,
  email: Mail,
  meeting: Calendar,
  form_submission: MessageSquare,
  system: Bot,
};

export function ActivityItem({ activity }: { activity: Activity }) {
  const Icon = ICONS[activity.type] || FileText;

  return (
    <div className="relative pl-6 sm:pl-8">
      <div className={cn(
        "absolute -left-3 sm:-left-4 top-1 flex h-6 w-6 sm:h-8 sm:w-8 items-center justify-center rounded-full border bg-background",
        activity.type === "system" ? "border-primary text-primary" : "border-muted-foreground text-muted-foreground"
      )}>
        <Icon className="h-3 w-3 sm:h-4 sm:w-4" />
      </div>
      <div className="flex flex-col space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">
            {activity.title || activity.type.charAt(0).toUpperCase() + activity.type.slice(1)}
          </span>
          <span className="text-xs text-muted-foreground">
            {new Date(activity.createdAt).toLocaleString()}
          </span>
        </div>
        {activity.body && (
          <p className="text-sm text-muted-foreground bg-muted/30 p-3 rounded-md mt-2">
            {activity.body}
          </p>
        )}
      </div>
    </div>
  );
}
