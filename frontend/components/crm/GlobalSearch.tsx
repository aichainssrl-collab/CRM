"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, Users, Briefcase, CheckSquare, Loader2, FileSearch } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useGlobalSearch, type SearchResult } from "@/hooks/useNotifications";

const KIND_META: Record<string, { icon: React.ElementType; label: string; href: (id: string) => string }> = {
  leads: { icon: Users, label: "Lead", href: (id) => `/crm/leads/${id}` },
  deals: { icon: Briefcase, label: "Deal", href: () => "/crm/pipeline" },
  tasks: { icon: CheckSquare, label: "Task", href: () => "/crm/tasks" },
};

export function GlobalSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: results, isLoading } = useGlobalSearch(query);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      }
      if (e.key === "Escape") {
        setOpen(false);
        inputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const totalResults = results
    ? results.leads.length + results.deals.length + results.tasks.length
    : 0;

  function handleSelect(type: string, id: string) {
    const meta = KIND_META[type];
    if (meta) router.push(meta.href(id));
    setOpen(false);
    setQuery("");
  }

  function renderSection(title: string, items: SearchResult["leads"], type: string) {
    if (!items.length) return null;
    const meta = KIND_META[type];
    const Icon = meta?.icon || FileSearch;
    return (
      <div className="py-1">
        <p className="px-4 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
          {title}
        </p>
        {items.map((item) => (
          <button
            key={item.id}
            className="w-full flex items-center gap-2.5 px-4 py-2 hover:bg-muted/50 text-left transition-colors"
            onClick={() => handleSelect(type, item.id)}
          >
            <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-sm truncate">{item.title}</p>
              <p className="text-xs text-muted-foreground truncate">{item.subtitle}</p>
            </div>
            <Badge variant="secondary" className="text-[9px] shrink-0">{item.status}</Badge>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="relative w-full max-w-md">
      <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/50" />
      <Input
        ref={inputRef}
        placeholder="Cerca lead, deal, task... (⌘K)"
        value={query}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 200)}
        className="pl-8 h-9 text-sm"
      />
      {open && query.length >= 2 && (
        <div className="absolute top-full z-50 mt-1 w-full rounded-lg border bg-card shadow-lg overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-6 gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-xs">Ricerca...</span>
            </div>
          ) : totalResults === 0 ? (
            <div className="flex flex-col items-center justify-center py-6 gap-2 text-muted-foreground">
              <FileSearch className="h-6 w-6 text-muted-foreground/30" />
              <p className="text-xs">Nessun risultato per &quot;{query}&quot;</p>
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto">
              {renderSection("Lead", results?.leads ?? [], "leads")}
              {renderSection("Deal", results?.deals ?? [], "deals")}
              {renderSection("Task", results?.tasks ?? [], "tasks")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}