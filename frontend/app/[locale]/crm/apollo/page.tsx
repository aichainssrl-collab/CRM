"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Checkbox } from "@/components/ui/checkbox";
import {
  useApolloSearch,
  useApolloImport,
  useApolloUsage,
  type ApolloProspect,
  type ApolloSearchFilters,
} from "@/hooks/useApollo";
import { toast } from "sonner";
import {
  Search, Download, Loader2, Users, Building2, MapPin, Briefcase,
} from "lucide-react";

export default function ApolloPage() {
  const t = useTranslations("apollo");
  const [filters, setFilters] = useState<ApolloSearchFilters>({});
  const [draft, setDraft] = useState<ApolloSearchFilters>({});
  const [searched, setSearched] = useState(false);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [importing, setImporting] = useState(false);

  const { data: usage } = useApolloUsage();
  const { data, isLoading, isFetching } = useApolloSearch(filters, 1, searched);
  const importMutation = useApolloImport();

  const people = data?.people ?? [];
  const selectedList = useMemo(
    () => people.filter((p) => selected[p.apolloId || p.email]),
    [people, selected]
  );

  function runSearch() {
    setFilters({ ...draft });
    setSearched(true);
    setSelected({});
  }

  async function handleImport() {
    if (selectedList.length === 0) return;
    setImporting(true);
    try {
      const result = await importMutation.mutateAsync(selectedList);
      const lines = [
        `${t("imported")}: ${result.importedCount}`,
        result.skippedCount ? `${t("skipped")}: ${result.skippedCount}` : null,
        result.errors.length ? `${t("errors")}: ${result.errors.length}` : null,
      ].filter(Boolean).join(" · ");
      toast.success(t("importSuccess"), { description: lines });
      setSelected({});
    } catch (e) {
      toast.error(t("importError"), {
        description: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setImporting(false);
    }
  }

  function toggle(id: string, checked: boolean) {
    setSelected((s) => ({ ...s, [id]: checked }));
  }

  function toggleAll(checked: boolean) {
    const next: Record<string, boolean> = {};
    if (checked) {
      for (const p of people) {
        if (p.emailStatus !== "invalid") next[p.apolloId || p.email] = true;
      }
    }
    setSelected(next);
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1200px] mx-auto w-full">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t("subtitle")}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={usage?.mode === "live" ? "default" : "secondary"}>
            {usage?.mode === "live" ? t("modeLive") : t("modeMock")}
          </Badge>
          <Button
            onClick={handleImport}
            disabled={selectedList.length === 0 || importing}
          >
            {importing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            {t("importSelected")} ({selectedList.length})
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("searchTitle")}</CardTitle>
          <CardDescription>{t("searchDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="apollo-q">{t("filterQ")}</Label>
              <Input
                id="apollo-q"
                value={draft.q ?? ""}
                onChange={(e) => setDraft((d) => ({ ...d, q: e.target.value }))}
                placeholder={t("filterQPlaceholder")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="apollo-title">{t("filterTitle")}</Label>
              <Input
                id="apollo-title"
                value={draft.title ?? ""}
                onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
                placeholder={t("filterTitlePlaceholder")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="apollo-industry">{t("filterIndustry")}</Label>
              <Input
                id="apollo-industry"
                value={draft.industry ?? ""}
                onChange={(e) => setDraft((d) => ({ ...d, industry: e.target.value }))}
                placeholder={t("filterIndustryPlaceholder")}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="apollo-location">{t("filterLocation")}</Label>
              <Input
                id="apollo-location"
                value={draft.location ?? ""}
                onChange={(e) => setDraft((d) => ({ ...d, location: e.target.value }))}
                placeholder={t("filterLocationPlaceholder")}
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={runSearch} disabled={isFetching}>
              {isFetching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              {t("searchCta")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-base">{t("resultsTitle")}</CardTitle>
            <CardDescription>
              {searched
                ? t("resultsCount", { count: data?.total ?? 0 })
                : t("resultsEmpty")}
            </CardDescription>
          </div>
          {people.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox
                id="apollo-select-all"
                checked={selectedList.length > 0 && selectedList.length === people.filter((p) => p.emailStatus !== "invalid").length}
                onCheckedChange={(v) => toggleAll(v === true)}
              />
              <Label htmlFor="apollo-select-all">{t("selectAll")}</Label>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {isLoading || isFetching ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : people.length === 0 ? (
            <div className="py-10 text-center text-sm text-muted-foreground">
              {searched ? t("noResults") : t("promptSearch")}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="py-2 w-8" />
                    <th className="py-2 px-2">{t("colName")}</th>
                    <th className="py-2 px-2">{t("colTitle")}</th>
                    <th className="py-2 px-2">{t("colCompany")}</th>
                    <th className="py-2 px-2">{t("colEmail")}</th>
                    <th className="py-2 px-2">{t("colLocation")}</th>
                    <th className="py-2 px-2 text-right">{t("colScore")}</th>
                  </tr>
                </thead>
                <tbody>
                  {people.map((p) => {
                    const id = p.apolloId || p.email;
                    const invalid = p.emailStatus === "invalid";
                    return (
                      <tr
                        key={id}
                        className={`border-b border-border/50 ${invalid ? "opacity-50" : ""}`}
                      >
                        <td className="py-3">
                          <Checkbox
                            checked={!!selected[id]}
                            disabled={invalid}
                            onCheckedChange={(v) => toggle(id, v === true)}
                            aria-label={`${p.firstName} ${p.lastName}`}
                          />
                        </td>
                        <td className="py-3 px-2">
                          <div className="font-medium">
                            {p.firstName} {p.lastName}
                          </div>
                          {p.seniority && (
                            <div className="text-xs text-muted-foreground">{p.seniority}</div>
                          )}
                        </td>
                        <td className="py-3 px-2">
                          <div className="flex items-center gap-1">
                            <Briefcase className="h-3.5 w-3.5 text-muted-foreground" />
                            {p.title || "—"}
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          <div className="flex items-center gap-1">
                            <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                            {p.companyName || "—"}
                          </div>
                          {p.industry && (
                            <div className="text-xs text-muted-foreground">{p.industry}</div>
                          )}
                        </td>
                        <td className="py-3 px-2">
                          <div>{p.email || "—"}</div>
                          {p.emailStatus && (
                            <Badge
                              variant={p.emailStatus === "verified" ? "default" : "secondary"}
                              className="mt-1 text-[10px]"
                            >
                              {p.emailStatus}
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-2">
                          <div className="flex items-center gap-1">
                            <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                            {[p.city, p.country].filter(Boolean).join(", ") || "—"}
                          </div>
                        </td>
                        <td className="py-3 px-2 text-right">
                          {p.apolloScore != null ? (
                            <Badge variant="outline">{p.apolloScore}</Badge>
                          ) : (
                            "—"
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Users className="h-3.5 w-3.5" />
        {t("gdprNote")}
      </div>
    </div>
  );
}
