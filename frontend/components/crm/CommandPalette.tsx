"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import {
  LayoutDashboard,
  Users,
  KanbanSquare,
  CheckSquare,
  BarChart3,
  Megaphone,
  Settings,
  UserCog,
  Plus,
} from "lucide-react";

export function CommandPalette() {
  const t = useTranslations("cmdk");
  const tSidebar = useTranslations("sidebar");
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const NAV_ITEMS = [
    { group: t("navigation"), items: [
      { label: tSidebar("dashboard"), icon: LayoutDashboard, href: "/crm" },
      { label: tSidebar("leads"), icon: Users, href: "/crm/leads" },
      { label: tSidebar("pipeline"), icon: KanbanSquare, href: "/crm/pipeline" },
      { label: tSidebar("tasks"), icon: CheckSquare, href: "/crm/tasks" },
      { label: tSidebar("reports"), icon: BarChart3, href: "/crm/reports" },
      { label: tSidebar("marketing"), icon: Megaphone, href: "/crm/marketing" },
    ]},
    { group: tSidebar("config"), items: [
      { label: tSidebar("settings"), icon: Settings, href: "/crm/settings" },
      { label: tSidebar("users"), icon: UserCog, href: "/crm/user-admin" },
    ]},
  ];

  const QUICK_ACTIONS = [
    { label: t("newLead"), icon: Plus, href: "/crm/leads?action=new" },
    { label: t("newDeal"), icon: Plus, href: "/crm/pipeline?action=new" },
    { label: t("newTask"), icon: Plus, href: "/crm/tasks?action=new" },
  ];

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const handleSelect = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router]
  );

  return (
    <CommandDialog open={open} onOpenChange={setOpen} title={t("title")} description={t("description")}>
      <CommandInput placeholder={t("placeholder")} />
      <CommandList>
        <CommandEmpty>{t("empty")}</CommandEmpty>

        {NAV_ITEMS.map((group) => (
          <CommandGroup key={group.group} heading={group.group}>
            {group.items.map((item) => (
              <CommandItem
                key={item.href}
                value={item.label}
                onSelect={() => handleSelect(item.href)}
              >
                <item.icon className="mr-2 h-4 w-4" />
                {item.label}
              </CommandItem>
            ))}
          </CommandGroup>
        ))}

        <CommandSeparator />

        <CommandGroup heading={t("quickActions")}>
          {QUICK_ACTIONS.map((action) => (
            <CommandItem
              key={action.label}
              value={action.label}
              onSelect={() => handleSelect(action.href)}
            >
              <action.icon className="mr-2 h-4 w-4" />
              {action.label}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}