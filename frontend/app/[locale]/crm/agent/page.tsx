"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAgentRun, type AgentRunResult } from "@/hooks/useAgent";
import {
  Bot, Send, Loader2, User, Sparkles, CheckCircle2, XCircle,
} from "lucide-react";

type ChatTurn = {
  role: "user" | "agent";
  text: string;
  mode?: AgentRunResult["mode"];
  steps?: AgentRunResult["steps"];
};

const EXAMPLES = [
  "Crea lead Mario Rossi email mario@studio.it",
  "Crea task Chiama Mario entro 2026-02-01 urgente",
  "Crea deal ZenTratto da 15000 email demo.cliente@example.com",
  "Mostra i deal",
  "Sposta deal ZenTratto in proposta",
  "Scadenze dei prossimi 7 giorni",
  "Proroga task Call follow-up a 2026-03-01",
  "Bozza email a demo.cliente@example.com oggetto Demo testo Ciao!",
];

export default function AgentPage() {
  const t = useTranslations("agent");
  const runAgent = useAgentRun();
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  async function send(text?: string) {
    const message = (text ?? input).trim();
    if (!message || runAgent.isPending) return;
    setInput("");
    setTurns((prev) => [...prev, { role: "user", text: message }]);
    try {
      const result = await runAgent.mutateAsync(message);
      setTurns((prev) => [
        ...prev,
        {
          role: "agent",
          text: result.reply,
          mode: result.mode,
          steps: result.steps,
        },
      ]);
    } catch (e) {
      setTurns((prev) => [
        ...prev,
        {
          role: "agent",
          text: e instanceof Error ? e.message : String(e),
          mode: "llm_error",
        },
      ]);
    }
  }

  return (
    <div className="flex flex-col gap-4 p-6 max-w-[900px] mx-auto w-full h-[calc(100vh-3.5rem)]">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Bot className="h-6 w-6 text-primary" />
          {t("title")}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">{t("subtitle")}</p>
      </div>

      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{t("chatTitle")}</CardTitle>
          <CardDescription>{t("chatHint")}</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto space-y-4 min-h-0">
          {turns.length === 0 && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">{t("examples")}</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((ex) => (
                  <Button
                    key={ex}
                    variant="outline"
                    size="sm"
                    className="text-xs h-8"
                    onClick={() => send(ex)}
                  >
                    <Sparkles className="h-3 w-3" />
                    {ex}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {turns.map((turn, i) => (
            <div
              key={i}
              className={`flex gap-3 ${turn.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {turn.role === "agent" && (
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                  turn.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted/40 border border-border"
                }`}
              >
                <p className="whitespace-pre-wrap">{turn.text}</p>
                {turn.role === "agent" && turn.mode && (
                  <Badge variant="secondary" className="mt-2 text-[10px]">
                    {t(`mode.${turn.mode}`)}
                  </Badge>
                )}
                {turn.steps?.filter((s) => s.type === "tool").map((s, j) => (
                  <div
                    key={j}
                    className="mt-2 flex items-start gap-1.5 text-xs text-muted-foreground"
                  >
                    {s.result?.ok ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-success mt-0.5" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5 text-destructive mt-0.5" />
                    )}
                    <span>
                      <code className="font-medium">{s.name}</code>
                      {s.result?.message || s.result?.error
                        ? ` — ${s.result.message || s.result.error}`
                        : ""}
                    </span>
                  </div>
                ))}
              </div>
              {turn.role === "user" && (
                <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}

          {runAgent.isPending && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("thinking")}
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>
      </Card>

      <form
        className="flex gap-2 shrink-0"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("placeholder")}
          disabled={runAgent.isPending}
          aria-label={t("placeholder")}
        />
        <Button type="submit" disabled={runAgent.isPending || !input.trim()}>
          {runAgent.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          {t("send")}
        </Button>
      </form>
    </div>
  );
}
