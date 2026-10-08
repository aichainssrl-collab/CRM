"use client";

import { Lead } from "@/hooks/useLeads";
import { useEnrichLead } from "@/hooks/useEnrichment";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { StatusBadge } from "./StatusBadge";
import { LeadScoreBadge } from "./LeadScoreBadge";
import {
  Mail, Phone, Building, Calendar, User,
  Link2, Globe, MapPin, Users, Briefcase,
  Sparkles, RefreshCw, CheckCircle2, Code2, Shield, Tag,
} from "lucide-react";

function EnrichmentBadge({ enrichedAt, source }: { enrichedAt?: string; source?: string }) {
  const t = useTranslations("leadDetail");
  if (!enrichedAt) return null;
  const date = new Date(enrichedAt).toLocaleDateString("it-IT", {
    day: "2-digit", month: "short", year: "numeric",
  });
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <Badge
            variant="secondary"
            className="gap-1 text-[10px] text-success bg-success-muted border border-success/20"
          >
            <CheckCircle2 className="h-3 w-3" />
            {t("enriched")}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p className="text-xs">{t("enrichedOn", { date })}</p>
          {source && <p className="text-xs text-muted-foreground">{t("via", { source })}</p>}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

function InfoRow({
  icon: Icon,
  label,
  value,
  href,
}: {
  icon: React.ElementType;
  label: string;
  value?: string | null;
  href?: string;
}) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2 text-sm">
      <Icon className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <span className="text-[11px] text-muted-foreground uppercase tracking-wide block">{label}</span>
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline truncate block"
          >
            {value}
          </a>
        ) : (
          <span className="text-foreground">{value}</span>
        )}
      </div>
    </div>
  );
}

export function LeadDetail({ lead }: { lead: Lead }) {
  const t = useTranslations("leadDetail");
  const { mutate: enrich, isPending: isEnriching } = useEnrichLead(lead.id);

  const fullName =
    lead.firstName || lead.lastName
      ? `${lead.firstName ?? ""} ${lead.lastName ?? ""}`.trim()
      : t("leadNotFound");
  const initial = lead.firstName
    ? lead.firstName.charAt(0)
    : lead.email.charAt(0).toUpperCase();

  const cf = (lead.customFields ?? {}) as Record<string, unknown>;
  const techStack: string[] = Array.isArray(cf.techStack) ? cf.techStack as string[] : [];
  const tags: string[] = Array.isArray(lead.tags) ? lead.tags : [];
  const companyDesc = cf.companyDescription as string | undefined;
  const location = cf.location as string | undefined;
  const hasPrivacy = cf.hasPrivacyPolicy as boolean | undefined;
  const linkedinFollowers = cf.linkedinFollowers as string | undefined;
  const foundedYear = cf.foundedYear as number | undefined;
  const siteLanguage = cf.siteLanguage as string | undefined;
  const website: string | undefined = lead.website;
  const enrichedAt: string | undefined = lead.enrichedAt;
  const enrichmentSource: string | undefined = lead.enrichmentSource;
  const numEmployeesRange: string | undefined = lead.numEmployeesRange;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between pb-4 gap-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <Avatar className="h-14 w-14 shrink-0">
            <AvatarFallback className="text-xl font-semibold bg-primary/10 text-primary">
              {initial}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <CardTitle className="text-xl truncate">{fullName}</CardTitle>
            {(lead.roleTitle || lead.companyName) && (
              <p className="text-sm text-muted-foreground mt-0.5 truncate">
                {[lead.roleTitle, lead.companyName].filter(Boolean).join(" · ")}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <StatusBadge status={lead.pipelineStage} />
              <LeadScoreBadge score={lead.leadScore} />
              <EnrichmentBadge enrichedAt={enrichedAt} source={enrichmentSource} />
            </div>
          </div>
        </div>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <Button
                variant="outline"
                size="sm"
                onClick={() => enrich()}
                disabled={isEnriching}
                className="shrink-0"
              >
                {isEnriching ? (
                  <RefreshCw className="h-4 w-4 mr-1.5 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4 mr-1.5" />
                )}
                {isEnriching ? t("enrichStarted") : t("enrich")}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p className="text-xs">{t("enrichTooltip")}</p>
              <p className="text-xs text-muted-foreground">{t("enrichTooltipTime")}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </CardHeader>

      <CardContent className="space-y-5">
        {companyDesc && (
          <p className="text-sm text-muted-foreground italic border-l-2 border-border pl-3 leading-relaxed">
            {companyDesc}
          </p>
        )}

        <div>
          <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            {t("contacts")}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <InfoRow icon={Mail} label="Email" value={lead.email} href={`mailto:${lead.email}`} />
            <InfoRow icon={Phone} label={t("phone")} value={lead.phone} href={lead.phone ? `tel:${lead.phone}` : undefined} />
            <InfoRow
              icon={Link2}
              label={t("linkedin")}
              value={lead.linkedinUrl ? t("openProfile") : undefined}
              href={lead.linkedinUrl ?? undefined}
            />
            <InfoRow icon={Globe} label={t("website")} value={website} href={website} />
            <InfoRow icon={MapPin} label={t("location")} value={location} />
            <InfoRow
              icon={Calendar}
              label={t("addedOn")}
              value={new Date(lead.createdAt).toLocaleDateString("it-IT")}
            />
          </div>
        </div>

        <Separator />

        <div>
          <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            {t("companyInfo")}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <InfoRow icon={Building} label={t("companyName")} value={lead.companyName} />
            <InfoRow icon={Briefcase} label={t("industry")} value={lead.industry} />
            <InfoRow icon={Users} label={t("employees")} value={lead.companySize ?? numEmployeesRange} />
            <InfoRow icon={User} label={t("role")} value={lead.roleTitle} />
            <InfoRow icon={User} label={t("seniority")} value={lead.roleSeniority} />
            <InfoRow icon={Calendar} label={t("foundedYear")} value={foundedYear ? String(foundedYear) : undefined} />
            {linkedinFollowers && (
              <InfoRow icon={Link2} label={t("linkedinFollowers")} value={linkedinFollowers} />
            )}
            {siteLanguage && (
              <InfoRow icon={Globe} label={t("siteLanguage")} value={siteLanguage.toUpperCase()} />
            )}
            {hasPrivacy !== undefined && (
              <div className="flex items-start gap-2 text-sm">
                <Shield className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                <div>
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block">
                    {t("privacyPolicy")}
                  </span>
                  <span className={hasPrivacy ? "text-success text-sm" : "text-warning text-sm"}>
                    {hasPrivacy ? t("present") : t("notDetected")}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {techStack.length > 0 && (
          <>
            <Separator />
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Code2 className="h-3.5 w-3.5" />
                {t("techStack")}
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {techStack.map((tech) => (
                  <Badge key={tech} variant="outline" className="text-xs font-normal">
                    {tech}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}

        {tags.length > 0 && (
          <>
            <Separator />
            <div>
              <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <Tag className="h-3.5 w-3.5" />
                {t("tags")}
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs font-normal">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}

        <Separator />
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <User className="h-4 w-4" />
          <span>{t("assignedTo")}</span>
          <span className="text-foreground font-medium">
            {lead.assignedTo ?? t("unassigned")}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}