"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Megaphone, Sparkles, PenTool, BarChart3 } from "lucide-react";
import { AgentChat } from "@/components/crm/marketing/AgentChat";
import { ContentGenerator } from "@/components/crm/marketing/ContentGenerator";
import { MetaAdsPanel } from "@/components/crm/marketing/MetaAdsPanel";
import { InsightsPanel } from "@/components/crm/marketing/InsightsPanel";

type TabValue = "meta-ads" | "agent" | "content" | "insights";

export default function MarketingPage() {
  const t = useTranslations("marketing");
  const [activeTab, setActiveTab] = useState<TabValue>("meta-ads");

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)}>
        <TabsList className="h-10">
          <TabsTrigger value="meta-ads" className="gap-1.5 text-xs">
            <Megaphone className="h-3.5 w-3.5" />
            {t("tabs.metaAds")}
          </TabsTrigger>
          <TabsTrigger value="agent" className="gap-1.5 text-xs">
            <Sparkles className="h-3.5 w-3.5" />
            {t("tabs.agent")}
          </TabsTrigger>
          <TabsTrigger value="content" className="gap-1.5 text-xs">
            <PenTool className="h-3.5 w-3.5" />
            {t("tabs.content")}
          </TabsTrigger>
          <TabsTrigger value="insights" className="gap-1.5 text-xs">
            <BarChart3 className="h-3.5 w-3.5" />
            {t("tabs.insights")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="meta-ads" className="mt-6">
          <MetaAdsPanel />
        </TabsContent>

        <TabsContent value="agent" className="mt-6">
          <AgentChat />
        </TabsContent>

        <TabsContent value="content" className="mt-6">
          <ContentGenerator />
        </TabsContent>

        <TabsContent value="insights" className="mt-6">
          <InsightsPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}