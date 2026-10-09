"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { GlobalSearch } from "@/components/crm/GlobalSearch";
import { NotificationBell } from "@/components/crm/NotificationBell";

export function Navbar() {
  const t = useTranslations("sidebar");
  const pathname = usePathname();

  const PAGE_LABELS: Record<string, string> = {
    "/crm": t("dashboard"),
    "/crm/leads": t("leads"),
    "/crm/pipeline": t("pipeline"),
    "/crm/tasks": t("tasks"),
    "/crm/reports": t("reports"),
    "/crm/analytics": t("analytics"),
    "/crm/emails": t("emails"),
    "/crm/marketing": t("marketing"),
    "/crm/settings": t("settings"),
    "/crm/user-admin": t("users"),
  };

  // Strip locale prefix for matching (e.g. /it/crm/leads → /crm/leads)
  const pathWithoutLocale = pathname.replace(/^\/(it|en)/, "") || "/crm";
  const label = PAGE_LABELS[pathWithoutLocale] ?? "CRM";
  const isSubpage = pathWithoutLocale.split("/").filter(Boolean).length > 2;

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border/60 bg-card/80 backdrop-blur-sm px-4">
      <div className="flex flex-1 items-center gap-3">
        <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground transition-colors" />
        <Separator orientation="vertical" className="h-4 bg-border/60" />
        <Breadcrumb>
          <BreadcrumbList>
            {isSubpage && (
              <>
                <BreadcrumbItem>
                  <BreadcrumbLink
                    render={<Link href={pathname.substring(0, pathname.lastIndexOf("/"))} />}
                  >
                    {PAGE_LABELS[pathWithoutLocale.substring(0, pathWithoutLocale.lastIndexOf("/"))] ?? "CRM"}
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
              </>
            )}
            <BreadcrumbItem>
              <BreadcrumbPage className="font-medium">{label}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      <GlobalSearch />

      <Separator orientation="vertical" className="h-4 hidden md:block bg-border/60" />

      <NotificationBell />
    </header>
  );
}