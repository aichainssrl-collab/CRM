"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { type Lead } from "@/hooks/useLeads";
import {
  useApolloBulkEnrich,
  type ApolloBulkEnrichResult,
} from "@/hooks/useApollo";
import { toast } from "sonner";
import { Loader2, Sparkles, CheckCircle2, AlertTriangle } from "lucide-react";

interface BulkEnrichDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Selected leads from the table */
  leads: Lead[];
  /** If true, treat `leads` as the full candidate pool (e.g. all filtered) */
  onlyStaleDefault?: boolean;
}

const CHUNK_SIZE = 10;

function isStale(enrichedAt?: string | null): boolean {
  if (!enrichedAt) return true;
  const then = new Date(enrichedAt).getTime();
  if (Number.isNaN(then)) return true;
  return then < Date.now() - 30 * 24 * 60 * 60 * 1000;
}

export function BulkEnrichDialog({
  open,
  onOpenChange,
  leads,
  onlyStaleDefault = true,
}: BulkEnrichDialogProps) {
  const t = useTranslations("bulkEnrich");
  const bulkEnrich = useApolloBulkEnrich();
  const [onlyStale, setOnlyStale] = useState(onlyStaleDefault);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [summary, setSummary] = useState<ApolloBulkEnrichResult | null>(null);

  const candidates = useMemo(() => {
    return onlyStale ? leads.filter((l) => isStale(l.enrichedAt)) : leads;
  }, [leads, onlyStale]);

  const skippedFresh = leads.length - candidates.length;

  async function handleRun() {
    if (candidates.length === 0) return;
    setRunning(true);
    setSummary(null);
    setProgress(0);

    const ids = candidates.map((l) => l.id);
    const combined: ApolloBulkEnrichResult = {
      results: [],
      enrichedCount: 0,
      missedCount: 0,
      skippedCount: 0,
      errorCount: 0,
      processedCount: 0,
    };

    try {
      for (let i = 0; i < ids.length; i += CHUNK_SIZE) {
        const chunk = ids.slice(i, i + CHUNK_SIZE);
        const chunkResult = await bulkEnrich.mutateAsync({
          leadIds: chunk,
          onlyStale,
        });
        combined.results.push(...chunkResult.results);
        combined.enrichedCount += chunkResult.enrichedCount;
        combined.missedCount += chunkResult.missedCount;
        combined.skippedCount += chunkResult.skippedCount;
        combined.errorCount += chunkResult.errorCount;
        combined.processedCount += chunkResult.processedCount;
        setProgress(Math.min(100, Math.round(((i + chunk.length) / ids.length) * 100)));
      }
      setSummary(combined);
      toast.success(t("doneTitle"), {
        description: t("doneDescription", {
          enriched: combined.enrichedCount,
          missed: combined.missedCount,
          errors: combined.errorCount,
        }),
      });
    } catch (e) {
      toast.error(t("errorTitle"), {
        description: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setRunning(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            {t("title")}
          </DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-start gap-2">
            <Checkbox
              id="bulk-enrich-only-stale"
              checked={onlyStale}
              disabled={running}
              onCheckedChange={(v) => setOnlyStale(v === true)}
            />
            <div className="grid gap-1">
              <Label htmlFor="bulk-enrich-only-stale" className="text-sm">
                {t("onlyStale")}
              </Label>
              <p className="text-xs text-muted-foreground">{t("onlyStaleHint")}</p>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
            <div className="flex items-center justify-between">
              <span>{t("selected")}</span>
              <Badge variant="outline">{leads.length}</Badge>
            </div>
            <div className="mt-1 flex items-center justify-between">
              <span>{t("willEnrich")}</span>
              <Badge>{candidates.length}</Badge>
            </div>
            {onlyStale && skippedFresh > 0 && (
              <div className="mt-1 flex items-center justify-between text-muted-foreground">
                <span>{t("willSkipFresh")}</span>
                <Badge variant="secondary">{skippedFresh}</Badge>
              </div>
            )}
          </div>

          {running && (
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <p className="text-xs text-muted-foreground text-center">
                {t("progress", { percent: progress })}
              </p>
            </div>
          )}

          {summary && !running && (
            <div className="space-y-2 rounded-lg border border-border p-3 text-sm">
              <div className="flex items-center gap-2 font-medium">
                <CheckCircle2 className="h-4 w-4 text-success" />
                {t("summaryTitle")}
              </div>
              <ul className="space-y-1 text-muted-foreground">
                <li className="flex justify-between">
                  <span>{t("enriched")}</span>
                  <span>{summary.enrichedCount}</span>
                </li>
                <li className="flex justify-between">
                  <span>{t("missed")}</span>
                  <span>{summary.missedCount}</span>
                </li>
                {summary.skippedCount > 0 && (
                  <li className="flex justify-between">
                    <span>{t("skipped")}</span>
                    <span>{summary.skippedCount}</span>
                  </li>
                )}
                {summary.errorCount > 0 && (
                  <li className="flex justify-between text-destructive">
                    <span className="flex items-center gap-1">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      {t("errors")}
                    </span>
                    <span>{summary.errorCount}</span>
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={running}
          >
            {t("close")}
          </Button>
          <Button
            onClick={handleRun}
            disabled={running || candidates.length === 0}
          >
            {running ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {t("run")} ({candidates.length})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
