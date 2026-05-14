import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  Users, 
  KanbanSquare, 
  CheckSquare, 
  BarChart3, 
  Settings, 
  UserCog 
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/crm", icon: LayoutDashboard },
  { name: "Leads", href: "/crm/leads", icon: Users },
  { name: "Pipeline", href: "/crm/pipeline", icon: KanbanSquare },
  { name: "Tasks", href: "/crm/tasks", icon: CheckSquare },
  { name: "Reports", href: "/crm/reports", icon: BarChart3 },
];

const settingsNav = [
  { name: "Settings", href: "/crm/settings", icon: Settings },
  { name: "User Admin", href: "/crm/user-admin", icon: UserCog },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-card">
      <div className="flex h-14 items-center border-b border-border px-4">
        <span className="text-xl font-bold text-primary">AiChain CRM</span>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  "group flex items-center rounded-md px-2 py-2 text-sm font-medium"
                )}
              >
                <item.icon
                  className={cn(
                    isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
                    "mr-3 h-5 w-5 flex-shrink-0"
                  )}
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
        
        <div className="mt-8">
          <h3 className="px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Configuration
          </h3>
          <nav className="mt-2 space-y-1 px-2">
            {settingsNav.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    "group flex items-center rounded-md px-2 py-2 text-sm font-medium"
                  )}
                >
                  <item.icon
                    className={cn(
                      isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
                      "mr-3 h-5 w-5 flex-shrink-0"
                    )}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}
