"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  useAgentRun,
  useAgentApprovals,
  useAgentApprovalDecision,
  useAgentMemory,
  useAgentRuns,
  type AgentRunResult,
} from "@/hooks/useAgent";
import {
  Bot, Send, Loader2, User, Sparkles, CheckCircle2, XCircle,
  ShieldCheck, Brain, History, Check, X,
} from "lucide-react";

type ChatTurn = {
  role: "user" | "agent";
  text: string;
  mode?: AgentRunResult["mode"];
  steps?: AgentRunResult["steps"];
};

const EXAMPLES = [
  "Crea lead Mario Rossi email mario@studio.it",
  "Dammi email di Mock Match",
  "Danilo Zanni in quale azienda lavora?",
  "Mostra fatture",
  "Mostra i task",
  "Pipeline dei deal",
  "Riepilogo CRM",
  "Workflow inbound per mario@studio.it",
  "Genera contenuto marketing per ZenTratto",
  "Ricorda che il cliente Marco preferisce le email formali",
];

export default function AgentPage() {
  const t = useTranslations("agent");
  const runAgent = useAgentRun();
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [opsTab, setOpsTab] = useState<"approvals" | "memory" | "runs">("approvals");
  const bottomRef = useRef<HTMLDivElement>(null);

  const approvalsQ = useAgentApprovals(true);
  const memoryQ = useAgentMemory(true);
  const runsQ = useAgentRuns(true, 12);
  const decide = useAgentApprovalDecision();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  async function send(text?: string) {
    const message = (text ?? input).trim();
    if (!message || runAgent.isPending) return;
    setInput("");
    setTurns((prev) => [...prev, { role: "user", text: message }]);
    try {
      const result = await runAgent.mutateAsync({ message, sessionId });
      if (result.sessionId) setSessionId(result.sessionId);
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
      const raw = e instanceof Error ? e.message : String(e);
      const isLlm = /llm|openai|anthropic|gemini|ollama/i.test(raw);
      setTurns((prev) => [
        ...prev,
        {
          role: "agent",
          text: raw,
          mode: isLlm ? "llm_error" : "none",
        },
      ]);
    }
  }

  async function decideApproval(id: string, approve: boolean) {
    const res = await decide.mutateAsync({ id, approve });
    if (res.ok && approve && res.tool && res.args) {
      // Esegui il tool approvato con confirm=true
      const label = JSON.stringify(res.args).slice(0, 80);
      setTurns((prev) => [
        ...prev,
        { role: "user", text: `Conferma esecuzione ${res.tool} ${label}` },
        {
          role: "agent",
          text: approve
            ? `✓ Approvazione registrata per ${res.tool}. Riesegui l'azione se necessario.`
            : `✗ Richiesta ${res.tool} respinta.`,
          mode: "parser",
        },
      ]);
    }
  }

  const approvals = approvalsQ.data?.approvals ?? [];
  const facts = memoryQ.data?.facts ?? [];
  const runs = runsQ.data?.runs ?? [];

  return (
    <div className="flex flex-col xl:flex-row gap-4 p-6 w-full h-[calc(100vh-3.5rem)]">
      {/* Chat */}
      <div className="flex flex-col gap-4 flex-1 min-w-0 max-w-[900px]">
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

      {/* Ops panel — approvazioni, memoria, run */}
      <Card className="w-full xl:w-[340px] shrink-0 flex flex-col max-h-[calc(100vh-3.5rem)]">
        <CardHeader className="pb-2">
          <div className="flex gap-1">
            <Button
              variant={opsTab === "approvals" ? "default" : "ghost"}
              size="sm"
              className="h-8 gap-1 text-xs"
              onClick={() => setOpsTab("approvals")}
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              Approvazioni
              {approvals.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-[10px]">{approvals.length}</Badge>
              )}
            </Button>
            <Button
              variant={opsTab === "memory" ? "default" : "ghost"}
              size="sm"
              className="h-8 gap-1 text-xs"
              onClick={() => setOpsTab("memory")}
            >
              <Brain className="h-3.5 w-3.5" />
              Memoria
            </Button>
            <Button
              variant={opsTab === "runs" ? "default" : "ghost"}
              size="sm"
              className="h-8 gap-1 text-xs"
              onClick={() => setOpsTab("runs")}
            >
              <History className="h-3.5 w-3.5" />
              Run
            </Button>
          </div>
        </CardHeader>
        <CardContent className="overflow-y-auto space-y-3 text-sm">
          {opsTab === "approvals" && (
            <>
              {approvals.length === 0 && (
                <p className="text-muted-foreground text-xs">Nessuna richiesta in attesa.</p>
              )}
              {approvals.map((a) => (
                <div key={a.id} className="rounded-md border p-2 space-y-2">
                  <div className="flex items-center gap-2">
                    <code className="text-xs font-medium">{a.tool}</code>
                    <Badge variant="outline" className="text-[9px]">pending</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{a.reason}</p>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      className="h-7 text-xs gap-1"
                      disabled={decide.isPending}
                      onClick={() => void decideApproval(a.id, true)}
                    >
                      <Check className="h-3 w-3" /> Approva
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-xs gap-1"
                      disabled={decide.isPending}
                      onClick={() => void decideApproval(a.id, false)}
                    >
                      <X className="h-3 w-3" /> Rifiuta
                    </Button>
                  </div>
                </div>
              ))}
            </>
          )}

          {opsTab === "memory" && (
            <>
              {facts.length === 0 && (
                <p className="text-muted-foreground text-xs">
                  Nessun fatto memorizzato. Prova «ricorda che…» in chat.
                </p>
              )}
              {facts.map((f) => (
                <div key={f.id} className="rounded-md border p-2">
                  <Badge variant="secondary" className="text-[9px]">{f.kind}</Badge>
                  <p className="mt-1 text-xs">{f.text}</p>
                </div>
              ))}
            </>
          )}

          {opsTab === "runs" && (
            <>
              {runs.length === 0 && (
                <p className="text-muted-foreground text-xs">Nessuna run registrata.</p>
              )}
              {runs.map((r) => (
                <div key={r.id} className="rounded-md border p-2 text-xs space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={r.ok ? "secondary" : "destructive"} className="text-[9px]">
                      {r.mode}
                    </Badge>
                    <span className="text-muted-foreground">{r.durationMs}ms</span>
                  </div>
                  <p className="line-clamp-2">{r.message}</p>
                  {!!r.tools?.length && (
                    <p className="text-muted-foreground">{r.tools.join(", ")}</p>
                  )}
                </div>
              ))}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
