"use client";

import { useState, useRef, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useMarketingAgent, type ChatMessage } from "@/hooks/useMarketingAgent";
import { useConversations } from "@/hooks/useMarketingData";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Send,
  Square,
  Trash2,
  Sparkles,
  Mail,
  Megaphone,
  FileText,
  Copy,
  Check,
  Save,
  History,
  MessageSquare,
  X,
  Loader2,
} from "lucide-react";

// ── Quick actions ─────────────────────────────────────────────────────────────

const QUICK_ACTIONS = [
  { key: "email_sequence", icon: Mail, labelKey: "quickEmailSequence" },
  { key: "social_post", icon: Megaphone, labelKey: "quickSocialPost" },
  { key: "ad_copy", icon: Sparkles, labelKey: "quickAdCopy" },
  { key: "blog_ideas", icon: FileText, labelKey: "quickBlogIdeas" },
];

const QUICK_PROMPTS: Record<string, string> = {
  email_sequence: "Crea una sequenza email di 5 step per nurturing lead freddi nel settore legale. Obiettivo: prenotare una demo di ZenTratto.",
  social_post: "Scrivi 3 post LinkedIn per promuovere ZenTratto a studi legali. Tono professionale ma accessibile.",
  ad_copy: "Crea copy per una campagna Meta Ads che promuove SignSiSure (firma digitale eIDAS 2.0) a notai e avvocati.",
  blog_ideas: "Suggerisci 5 titoli SEO-friendly per articoli blog su AI nel settore legale italiano.",
};

// ── Message bubble ────────────────────────────────────────────────────────────

function MessageBubble({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-muted border rounded-bl-md"
        }`}
      >
        {!isUser && (
          <div className="flex items-center justify-between mb-1.5">
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
              <Sparkles className="h-2.5 w-2.5 mr-1" />
              AI Agent
            </Badge>
            <button
              onClick={handleCopy}
              className="text-muted-foreground hover:text-foreground transition-colors"
              title="Copia"
            >
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </button>
          </div>
        )}
        <div className="whitespace-pre-wrap break-words">
          {message.content || (
            <span className="inline-flex items-center gap-1.5 text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse [animation-delay:150ms]" />
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse [animation-delay:300ms]" />
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Conversation sidebar ──────────────────────────────────────────────────────

function ConversationSidebar({
  open,
  onClose,
  onLoad,
}: {
  open: boolean;
  onClose: () => void;
  onLoad: () => void;
}) {
  const t = useTranslations("marketing.agent");
  const { conversations, loading, loadConversation, deleteConversation } = useConversations();

  if (!open) return null;

  return (
    <div className="w-64 border-r bg-muted/30 flex flex-col shrink-0">
      <div className="flex items-center justify-between px-3 py-2.5 border-b">
        <span className="text-xs font-semibold flex items-center gap-1.5">
          <History className="h-3.5 w-3.5" />
          {t("history")}
        </span>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        ) : conversations.length === 0 ? (
          <p className="text-[10px] text-muted-foreground text-center py-8 px-4">
            {t("noHistory")}
          </p>
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv._id}
                className="group flex items-start gap-2 p-2 rounded-md hover:bg-muted cursor-pointer"
                onClick={async () => {
                  await loadConversation(conv._id);
                  onLoad();
                  onClose();
                }}
              >
                <MessageSquare className="h-3.5 w-3.5 mt-0.5 text-muted-foreground shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-xs truncate">{conv.title}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {new Date(conv.updatedAt).toLocaleDateString("it-IT")}
                  </p>
                </div>
                <button
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                  onClick={async (e) => {
                    e.stopPropagation();
                    await deleteConversation(conv._id);
                  }}
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function AgentChat() {
  const t = useTranslations("marketing.agent");
  const { messages, isStreaming, sendMessage, stopStreaming, clearMessages } = useMarketingAgent();
  const { saveConversation } = useConversations();
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput("");
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = (key: string) => {
    const prompt = QUICK_PROMPTS[key];
    if (prompt) sendMessage(prompt);
  };

  const handleSave = async () => {
    if (messages.length === 0) return;
    setSaving(true);
    const title = messages[0]?.content?.slice(0, 60) || "Conversazione";
    await saveConversation(title, messages);
    setSaving(false);
  };

  const handleLoadConversation = () => {
    // Carica conversazione — ricarica la pagina per resettare lo stato chat
    window.location.reload();
  };

  return (
    <div className="flex h-[calc(100vh-260px)] min-h-[500px]">
      {/* Sidebar cronologia */}
      <ConversationSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onLoad={handleLoadConversation}
      />

      {/* Chat principale */}
      <Card className="flex flex-col flex-1">
        <CardContent className="flex flex-col h-full p-0">
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-2 border-b">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs gap-1.5"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <History className="h-3.5 w-3.5" />
                {t("history")}
              </Button>
            </div>
            <div className="flex items-center gap-1.5">
              {messages.length > 0 && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs gap-1.5"
                    onClick={handleSave}
                    disabled={saving}
                  >
                    {saving ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Save className="h-3.5 w-3.5" />
                    )}
                    {t("save")}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs gap-1.5 text-destructive hover:text-destructive"
                    onClick={clearMessages}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    {t("clear")}
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Quick actions bar */}
          {messages.length === 0 && (
            <div className="px-4 pt-4 pb-2">
              <p className="text-xs text-muted-foreground mb-2.5 font-medium">{t("quickActions")}</p>
              <div className="flex flex-wrap gap-2">
                {QUICK_ACTIONS.map((action) => {
                  const Icon = action.icon;
                  return (
                    <Button
                      key={action.key}
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs rounded-full"
                      onClick={() => handleQuickAction(action.key)}
                      disabled={isStreaming}
                    >
                      <Icon className="h-3.5 w-3.5 mr-1.5" />
                      {t(action.labelKey)}
                    </Button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Sparkles className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold text-sm mb-1">{t("welcomeTitle")}</h3>
                <p className="text-xs text-muted-foreground max-w-[300px]">
                  {t("welcomeDesc")}
                </p>
              </div>
            ) : (
              <div className="py-4">
                {messages.map((msg, i) => (
                  <MessageBubble key={i} message={msg} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input area */}
          <div className="border-t p-3">
            <div className="flex items-end gap-2">
              <div className="relative flex-1">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t("placeholder")}
                  className="min-h-[40px] max-h-[120px] resize-none text-sm"
                  rows={1}
                  disabled={isStreaming}
                />
              </div>
              {isStreaming ? (
                <Button
                  variant="destructive"
                  size="icon"
                  className="h-10 w-10 shrink-0"
                  onClick={stopStreaming}
                >
                  <Square className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  size="icon"
                  className="h-10 w-10 shrink-0"
                  onClick={handleSend}
                  disabled={!input.trim()}
                >
                  <Send className="h-4 w-4" />
                </Button>
              )}
            </div>
            <p className="text-[10px] text-muted-foreground mt-1.5 px-1">
              {t("footer")}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}