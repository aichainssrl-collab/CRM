"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  LayoutDashboard,
  Users,
  KanbanSquare,
  CheckSquare,
  BarChart3,
  LineChart,
  Mail,
  Megaphone,
  Calendar,
  Package,
  FileText,
  Receipt,
  GitBranch,
  Settings,
  UserCog,
  Shield,
  Zap,
  ChevronsUpDown,
  LogOut,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { useAuth } from "@/hooks/useAuth";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { logout } from "@/lib/auth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function AppSidebar() {
  const t = useTranslations("sidebar");
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();

  const mainNav = [
    { name: t("dashboard"), href: "/crm", icon: LayoutDashboard },
    { name: t("leads"), href: "/crm/leads", icon: Users },
    { name: t("pipeline"), href: "/crm/pipeline", icon: KanbanSquare },
    { name: t("tasks"), href: "/crm/tasks", icon: CheckSquare },
    { name: t("calendar"), href: "/crm/calendar", icon: Calendar },
    { name: t("products"), href: "/crm/products", icon: Package },
    { name: t("proposals"), href: "/crm/proposals", icon: FileText },
    { name: t("invoices"), href: "/crm/invoices", icon: Receipt },
    { name: t("workflows"), href: "/crm/workflows", icon: GitBranch },
    { name: t("reports"), href: "/crm/reports", icon: BarChart3 },
    { name: t("analytics"), href: "/crm/analytics", icon: LineChart },
    { name: t("emails"), href: "/crm/emails", icon: Mail },
    { name: t("marketing"), href: "/crm/marketing", icon: Megaphone },
  ];

  const settingsNav = [
    { name: t("settings"), href: "/crm/settings", icon: Settings },
    { name: t("users"), href: "/crm/user-admin", icon: UserCog },
    { name: t("system"), href: "/crm/admin", icon: Shield },
  ];

  const isActive = (href: string) =>
    href === "/crm"
      ? pathname === "/crm"
      : pathname === href || pathname?.startsWith(`${href}/`);

  const avatarSrc = user?.photoURL && !user.photoURL.includes("/api/v1/")
    ? user.photoURL
    : undefined;

  return (
    <Sidebar collapsible="icon" className="border-r border-border/60">
      <SidebarHeader className="border-b border-border/40">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" render={<Link href="/crm" />}>
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm shadow-primary/20">
                <Zap className="size-4" />
              </div>
              <div className="flex flex-col gap-0.5 leading-none">
                <span className="font-semibold text-sm tracking-tight">AiChain CRM</span>
                <span className="text-[11px] text-muted-foreground/70">Solutions Platform</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent className="py-2">
        <SidebarGroup>
          <SidebarGroupLabel className="text-[11px] uppercase tracking-wider text-muted-foreground/50 px-3 mb-1">
            {t("main")}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNav.map((item) => (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton
                    render={<Link href={item.href} />}
                    isActive={isActive(item.href)}
                    tooltip={item.name}
                    className="relative transition-all duration-150"
                  >
                    <item.icon className={isActive(item.href) ? "text-primary" : "text-muted-foreground/60"} />
                    <span className={isActive(item.href) ? "font-medium" : ""}>{item.name}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="mt-auto">
          <SidebarGroupLabel className="text-[11px] uppercase tracking-wider text-muted-foreground/50 px-3 mb-1">
            {t("config")}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {settingsNav.map((item) => (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton
                    render={<Link href={item.href} />}
                    isActive={isActive(item.href)}
                    tooltip={item.name}
                    className="transition-all duration-150"
                  >
                    <item.icon className={isActive(item.href) ? "text-primary" : "text-muted-foreground/60"} />
                    <span className={isActive(item.href) ? "font-medium" : ""}>{item.name}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-border/40">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger
                data-slot="sidebar-menu-button"
                data-sidebar="menu-button"
                data-size="lg"
                className="peer/menu-button group/menu-button flex w-full items-center gap-2 overflow-hidden rounded-md p-2 text-left text-sm ring-sidebar-ring outline-hidden transition-[width,height,padding] group-data-[collapsible=icon]:size-8! group-data-[collapsible=icon]:p-0! hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground h-12 [&_svg]:size-4 [&_svg]:shrink-0 data-[popup-open]:bg-sidebar-accent data-[popup-open]:text-sidebar-accent-foreground"
              >
                <Avatar className="h-8 w-8 rounded-lg ring-1 ring-border/40">
                  <AvatarImage src={avatarSrc} />
                  <AvatarFallback className="rounded-lg text-xs bg-primary/10 text-primary font-semibold">
                    {user?.email?.charAt(0).toUpperCase() ?? "U"}
                  </AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
                  <span className="truncate font-medium text-[13px]">
                    {user?.displayName || user?.email?.split("@")[0] || "User"}
                  </span>
                  <span className="truncate text-[11px] text-muted-foreground/60">
                    {user?.email}
                  </span>
                </div>
                <ChevronsUpDown className="ml-auto size-3.5 shrink-0 text-muted-foreground/40 group-data-[collapsible=icon]:hidden" />
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-56"
                side="bottom"
                align="end"
                sideOffset={4}
              >
                <DropdownMenuItem onClick={() => router.push("/crm/settings")}>
                  <Settings className="mr-2 h-4 w-4" />
                  {t("settings")}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => logout()}
                  variant="destructive"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  {t("logout")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}