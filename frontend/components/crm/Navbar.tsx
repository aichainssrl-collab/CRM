"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Bell, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { usePathname } from "next/navigation";
import Link from "next/link";

const PAGE_LABELS: Record<string, string> = {
  "/crm": "Dashboard",
  "/crm/leads": "Leads",
  "/crm/pipeline": "Pipeline",
  "/crm/tasks": "Tasks",
  "/crm/reports": "Reports",
  "/crm/marketing": "Marketing",
  "/crm/settings": "Impostazioni",
  "/crm/user-admin": "Gestione Utenti",
};

export function Navbar() {
  const pathname = usePathname();
  const label = PAGE_LABELS[pathname] ?? "CRM";
  const isSubpage = pathname.split("/").filter(Boolean).length > 2;

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
                    {PAGE_LABELS[pathname.substring(0, pathname.lastIndexOf("/"))] ?? "CRM"}
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

      <button
        type="button"
        className="relative hidden md:flex items-center h-8 w-48 rounded-md border border-transparent bg-muted/40 px-3 text-sm text-muted-foreground/60 hover:border-border hover:bg-background transition-all cursor-pointer"
        onClick={() => document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
      >
        <Search className="absolute left-2.5 h-3.5 w-3.5 pointer-events-none" />
        <span className="pl-5">Cerca...</span>
        <kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 hidden lg:inline-flex h-5 select-none items-center gap-0.5 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
          <span className="text-[11px]">⌘</span>K
        </kbd>
      </button>

      <Separator orientation="vertical" className="h-4 hidden md:block bg-border/60" />

      <div className="flex items-center gap-1.5">
        <Button variant="ghost" size="icon" className="relative h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-rose-500 ring-2 ring-card" />
          <span className="sr-only">Notifiche</span>
        </Button>
      </div>
    </header>
  );
}
