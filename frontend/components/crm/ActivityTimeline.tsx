import { Activity } from "@/hooks/useActivities";
import { ActivityItem } from "@/components/crm/ActivityItem";

export function ActivityTimeline({ activities }: { activities: Activity[] }) {
  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground border border-dashed rounded-lg bg-muted/20">
        No activities yet.
      </div>
    );
  }

  return (
    <div className="relative border-l border-muted ml-4 space-y-8 pb-4">
      {activities.map((activity) => (
        <ActivityItem key={activity.id} activity={activity} />
      ))}
    </div>
  );
}
