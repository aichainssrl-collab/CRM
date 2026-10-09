"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import {
  useConversations, useConversation, useMessages, useInboxStats,
  useCreateConversation, useSendMessage, useMarkRead, useCloseConversation,
  useReopenConversation,
} from "@/hooks/useInbox";
import {
  MessageCircle, Plus, Send, CheckCircle2, XCircle, Loader2, Phone,
} from "lucide-react";

export default function InboxPage() {
  const t = useTranslations("inbox");
  const tSidebar = useTranslations("sidebar");
  const locale = useLocale();
  const { data: conversations, isLoading } = useConversations();
  const { data: stats } = useInboxStats();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: selected } = useConversation(selectedId);
  const { data: messages, isLoading: loadingMsgs } = useMessages(selectedId);
  const createConversation = useCreateConversation();
  const sendMessage = useSendMessage();
  const markRead = useMarkRead();
  const closeConversation = useCloseConversation();
  const reopenConversation = useReopenConversation();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [phone, setPhone] = useState("");
  const [leadName, setLeadName] = useState("");
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedId) {
      markRead.mutate(selectedId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages?.length]);

  const sorted = useMemo(() => conversations ?? [], [conversations]);

  async function handleCreate() {
    if (!phone.trim()) return;
    setSaving(true);
    try {
      const conv = await createConversation.mutateAsync({
        phone: phone.trim(),
        leadName: leadName.trim(),
      });
      setDialogOpen(false);
      setPhone("");
      setLeadName("");
      if (conv?.id) setSelectedId(conv.id);
    } finally {
      setSaving(false);
    }
  }

  async function handleSend() {
    if (!selectedId || !draft.trim()) return;
    const body = draft.trim();
    setDraft("");
    await sendMessage.mutateAsync({ conversationId: selectedId, body });
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{tSidebar("inbox")}</h1>
          <p className="text-sm text-muted-foreground mt-1">{t("subtitle")}</p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t("new")}
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("totalConversations")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.totalConversations ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("openConversations")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.openConversations ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>{t("unreadMessages")}</CardDescription>
            <CardTitle className="text-2xl">{stats?.unreadMessages ?? "—"}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[320px_1fr] min-h-[480px]">
        {/* Conversation list */}
        <Card className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <MessageCircle className="h-4 w-4 text-primary" />
              {t("conversations")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-2 space-y-1">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))
            ) : !sorted.length ? (
              <p className="text-sm text-muted-foreground p-4 text-center">{t("empty")}</p>
            ) : (
              sorted.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setSelectedId(c.id)}
                  className={`w-full text-left rounded-lg border p-3 transition-colors ${
                    selectedId === c.id
                      ? "border-primary bg-primary/5"
                      : "border-border/60 hover:bg-muted/40"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-medium truncate text-sm">
                        {c.leadName || c.phone}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">{c.phone}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {c.unreadCount > 0 && (
                        <Badge className="h-5 min-w-5 justify-center px-1 text-[10px]">
                          {c.unreadCount}
                        </Badge>
                      )}
                      <Badge variant={c.status === "open" ? "default" : "outline"}>
                        {t(`status.${c.status}`)}
                      </Badge>
                    </div>
                  </div>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        {/* Thread */}
        <Card className="flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <CardTitle className="text-base">
                  {selected?.leadName || selected?.phone || t("selectHint")}
                </CardTitle>
                {selected && (
                  <CardDescription className="flex items-center gap-1 mt-1">
                    <Phone className="h-3 w-3" />
                    {selected.phone}
                  </CardDescription>
                )}
              </div>
              {selected && (
                <div className="flex gap-2">
                  {selected.status === "open" ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => closeConversation.mutate(selected.id)}
                    >
                      <XCircle className="mr-1 h-3 w-3" />
                      {t("close")}
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => reopenConversation.mutate(selected.id)}
                    >
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                      {t("reopen")}
                    </Button>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col gap-3 min-h-0">
            {!selectedId ? (
              <div className="flex-1 flex items-center justify-center">
                <p className="text-sm text-muted-foreground">{t("selectHint")}</p>
              </div>
            ) : (
              <>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1 min-h-[240px]">
                  {loadingMsgs ? (
                    Array.from({ length: 3 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-2/3" />
                    ))
                  ) : !messages?.length ? (
                    <p className="text-sm text-muted-foreground text-center py-8">
                      {t("noMessages")}
                    </p>
                  ) : (
                    messages.map((m) => (
                      <div
                        key={m.id}
                        className={`flex ${m.direction === "outbound" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[75%] rounded-2xl px-3 py-2 text-sm ${
                            m.direction === "outbound"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted"
                          }`}
                        >
                          <p className="whitespace-pre-wrap break-words">{m.body}</p>
                          <p
                            className={`text-[10px] mt-1 ${
                              m.direction === "outbound"
                                ? "text-primary-foreground/70"
                                : "text-muted-foreground"
                            }`}
                          >
                            {new Date(m.createdAt).toLocaleString(locale === "en" ? "en-GB" : "it-IT")}
                            {m.direction === "outbound" && m.status ? ` · ${m.status}` : ""}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={bottomRef} />
                </div>
                <div className="flex gap-2 border-t border-border/60 pt-3">
                  <Textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder={t("messagePlaceholder")}
                    className="min-h-[44px] max-h-28 resize-none"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!draft.trim() || sendMessage.isPending}
                    aria-label={t("send")}
                  >
                    {sendMessage.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{t("newTitle")}</DialogTitle>
            <DialogDescription>{t("dialogDescription")}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="wa-phone">{t("phone")}</Label>
              <Input
                id="wa-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+39 333 1234567"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="wa-name">{t("leadName")}</Label>
              <Input
                id="wa-name"
                value={leadName}
                onChange={(e) => setLeadName(e.target.value)}
                placeholder={t("leadNamePlaceholder")}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              {t("cancel")}
            </Button>
            <Button onClick={handleCreate} disabled={saving || !phone.trim()}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {t("create")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
