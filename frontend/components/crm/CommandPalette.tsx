"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
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

const NAV_ITEMS = [
  { group: "Navigazione", items: [
    { label: "Dashboard", icon: LayoutDashboard, href: "/crm" },
    { label: "Leads", icon: Users, href: "/crm/leads" },
    { label: "Pipeline", icon: KanbanSquare, href: "/crm/pipeline" },
    { label: "Tasks", icon: CheckSquare, href: "/crm/tasks" },
    { label: "Reports", icon: BarChart3, href: "/crm/reports" },
    { label: "Marketing", icon: Megaphone, href: "/crm/marketing" },
  ]},
  { group: "Configurazione", items: [
    { label: "Impostazioni", icon: Settings, href: "/crm/settings" },
    { label: "Gestione Utenti", icon: UserCog, href: "/crm/user-admin" },
  ]},
];

const QUICK_ACTIONS = [
  { label: "Nuovo Lead", icon: Plus, href: "/crm/leads?action=new" },
  { label: "Nuovo Deal", icon: Plus, href: "/crm/pipeline?action=new" },
  { label: "Nuovo Task", icon: Plus, href: "/crm/tasks?action=new" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

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
    <CommandDialog open={open} onOpenChange={setOpen} title="Ricerca rapida" description="Cerca pagine e azioni rapide">
      <CommandInput placeholder="Cerca pagina o azione..." />
      <CommandList>
        <CommandEmpty>Nessun risultato trovato.</CommandEmpty>

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

        <CommandGroup heading="Azioni rapide">
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