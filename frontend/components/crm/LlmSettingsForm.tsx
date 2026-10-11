"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useLlmSettings,
  useUpdateLlmSettings,
  useTestLlmSettings,
} from "@/hooks/useLlmSettings";
import { toast } from "sonner";
import { Loader2, Plug, Save, Trash2 } from "lucide-react";

export function LlmSettingsForm() {
  const t = useTranslations("settings.llm");
  const { data, isLoading } = useLlmSettings();
  const update = useUpdateLlmSettings();
  const testConn = useTestLlmSettings();

  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [localModel, setLocalModel] = useState("");
  const [localBaseUrl, setLocalBaseUrl] = useState("");
  const [clearKey, setClearKey] = useState(false);

  useEffect(() => {
    if (!data) return;
    setProvider(data.provider || "openai");
    setModel(data.model || "");
    setBaseUrl(data.baseUrl || "");
    setLocalModel(data.localModel || "");
    setLocalBaseUrl(data.localBaseUrl || "");
    setApiKey("");
    setClearKey(false);
  }, [data]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    try {
      await update.mutateAsync({
        provider,
        model: model.trim(),
        baseUrl: baseUrl.trim(),
        apiKey: apiKey.trim() || undefined,
        clearApiKey: clearKey,
        localModel: localModel.trim(),
        localBaseUrl: localBaseUrl.trim(),
      });
      toast.success(t("saved"));
    } catch (err) {
      toast.error(t("saveError"), {
        description: err instanceof Error ? err.message : String(err),
      });
    }
  }

  async function handleTest() {
    try {
      const res = await testConn.mutateAsync();
      if (res.ok) {
        toast.success(t("testOk"), { description: res.model ?? "" });
      } else {
        toast.error(t("testFail"), { description: res.error });
      }
    } catch (err) {
      toast.error(t("testFail"), {
        description: err instanceof Error ? err.message : String(err),
      });
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground py-8">
        <Loader2 className="h-4 w-4 animate-spin" />
        {t("loading")}
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="space-y-4">
      <p className="text-sm text-muted-foreground">{t("description")}</p>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="llm-provider">{t("provider")}</Label>
          <Select value={provider} onValueChange={(v) => v && setProvider(v)}>
            <SelectTrigger id="llm-provider">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="openai">OpenAI</SelectItem>
              <SelectItem value="anthropic">Anthropic</SelectItem>
              <SelectItem value="gemini">Google Gemini</SelectItem>
              <SelectItem value="ollama">Ollama (locale)</SelectItem>
              <SelectItem value="custom">Custom (OpenAI-compatible)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="llm-model">{t("model")}</Label>
          <Input
            id="llm-model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="gpt-4o / claude-sonnet / llama3"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="llm-base-url">{t("baseUrl")}</Label>
        <Input
          id="llm-base-url"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          placeholder="https://api.openai.com/v1 o http://localhost:11434/v1"
        />
        <p className="text-xs text-muted-foreground">{t("baseUrlHint")}</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="llm-api-key">{t("apiKey")}</Label>
        <Input
          id="llm-api-key"
          type="password"
          value={apiKey}
          onChange={(e) => {
            setApiKey(e.target.value);
            setClearKey(false);
          }}
          placeholder={
            data?.apiKeySet
              ? t("apiKeyPlaceholderSet", { masked: data.apiKeyMasked ?? "••••" })
              : "sk-…"
          }
          autoComplete="off"
        />
        <div className="flex items-center gap-2">
          {data?.apiKeySet && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground"
              onClick={() => {
                setClearKey(true);
                setApiKey("");
              }}
            >
              <Trash2 className="h-3 w-3" />
              {clearKey ? t("clearKeyPending") : t("clearKey")}
            </Button>
          )}
          <p className="text-xs text-muted-foreground">{t("apiKeyHint")}</p>
        </div>
      </div>

      {(provider === "ollama" || provider === "custom") && (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="llm-local-model">{t("localModel")}</Label>
            <Input
              id="llm-local-model"
              value={localModel}
              onChange={(e) => setLocalModel(e.target.value)}
              placeholder="qwen3:4b"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="llm-local-url">{t("localBaseUrl")}</Label>
            <Input
              id="llm-local-url"
              value={localBaseUrl}
              onChange={(e) => setLocalBaseUrl(e.target.value)}
              placeholder="http://localhost:11434"
            />
          </div>
        </div>
      )}

      <div className="flex justify-between gap-2 pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={handleTest}
          disabled={testConn.isPending || update.isPending}
        >
          {testConn.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Plug className="h-4 w-4" />
          )}
          {t("test")}
        </Button>
        <Button type="submit" disabled={update.isPending}>
          {update.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {t("save")}
        </Button>
      </div>
    </form>
  );
}
