"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useContentGenerator } from "@/hooks/useMarketingAgent";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Sparkles,
  Copy,
  Check,
  RotateCcw,
  Loader2,
  FileText,
  Mail,
  Megaphone,
  PenTool,
} from "lucide-react";

const CONTENT_TYPES = [
  { value: "social_post", label: "Post Social", icon: Megaphone },
  { value: "email", label: "Email Marketing", icon: Mail },
  { value: "ad_copy", label: "Ad Copy", icon: Sparkles },
  { value: "blog_intro", label: "Introduzione Blog", icon: FileText },
];

const TONE_OPTIONS = [
  { value: "professionale", label: "Professionale" },
  { value: "amichevole", label: "Amichevole" },
  { value: "urgente", label: "Urgente" },
  { value: "educativo", label: "Educativo" },
  { value: "persuasivo", label: "Persuasivo" },
  { value: "ispirazionale", label: "Ispirazionale" },
];

export function ContentGenerator() {
  const t = useTranslations("marketing.content");
  const { content, isStreaming, error, generate, clear } = useContentGenerator();

  const [contentType, setContentType] = useState("social_post");
  const [topic, setTopic] = useState("");
  const [tone, setTone] = useState("professionale");
  const [language, setLanguage] = useState("it");
  const [extra, setExtra] = useState("");
  const [copied, setCopied] = useState(false);

  const handleGenerate = () => {
    if (!topic.trim() || isStreaming) return;
    generate({
      type: contentType,
      topic: topic.trim(),
      tone,
      language,
      extra_context: extra.trim() || undefined,
    });
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    clear();
    setTopic("");
    setExtra("");
  };

  const selectedType = CONTENT_TYPES.find((ct) => ct.value === contentType);

  return (
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      {/* Left panel — form */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <PenTool className="h-4 w-4" />
            {t("title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Content type */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("type")}</Label>
            <div className="grid grid-cols-2 gap-2">
              {CONTENT_TYPES.map((ct) => {
                const Icon = ct.icon;
                return (
                  <Button
                    key={ct.value}
                    variant={contentType === ct.value ? "default" : "outline"}
                    size="sm"
                    className="h-9 text-xs justify-start"
                    onClick={() => setContentType(ct.value)}
                  >
                    <Icon className="h-3.5 w-3.5 mr-1.5" />
                    {ct.label}
                  </Button>
                );
              })}
            </div>
          </div>

          {/* Topic */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("topic")}</Label>
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={t("topicPlaceholder")}
              className="h-9 text-sm"
              onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
            />
          </div>

          {/* Tone */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("tone")}</Label>
            <Select value={tone} onValueChange={(v) => v && setTone(v)}>
              <SelectTrigger className="h-9 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TONE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value} className="text-sm">
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Language */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("language")}</Label>
            <Select value={language} onValueChange={(v) => v && setLanguage(v)}>
              <SelectTrigger className="h-9 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="it" className="text-sm">Italiano</SelectItem>
                <SelectItem value="en" className="text-sm">English</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Extra context */}
          <div className="space-y-1.5">
            <Label className="text-xs">{t("extraContext")} <span className="text-muted-foreground">({t("optional")})</span></Label>
            <Textarea
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
              placeholder={t("extraPlaceholder")}
              className="min-h-[60px] text-sm resize-none"
              rows={2}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <Button
              onClick={handleGenerate}
              disabled={!topic.trim() || isStreaming}
              className="flex-1 h-9"
            >
              {isStreaming ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                  {t("generating")}
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-1.5" />
                  {t("generate")}
                </>
              )}
            </Button>
            <Button variant="outline" size="icon" className="h-9 w-9" onClick={handleReset}>
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Right panel — result */}
      <Card className="flex flex-col">
        <CardHeader className="pb-3 flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            {selectedType && <selectedType.icon className="h-4 w-4 text-muted-foreground" />}
            <CardTitle className="text-base">{t("result")}</CardTitle>
            {content && (
              <Badge variant="secondary" className="text-[10px]">
                {content.length} {t("chars")}
              </Badge>
            )}
          </div>
          {content && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={handleCopy}
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  {t("copied")}
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  {t("copy")}
                </>
              )}
            </Button>
          )}
        </CardHeader>
        <CardContent className="flex-1">
          {error ? (
            <div className="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 text-destructive text-sm">
              ⚠️ {error}
            </div>
          ) : content ? (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed bg-muted/50 rounded-lg p-4 border">
                {content}
              </pre>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center py-16">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
                <Sparkles className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground max-w-[280px]">
                {t("emptyState")}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}