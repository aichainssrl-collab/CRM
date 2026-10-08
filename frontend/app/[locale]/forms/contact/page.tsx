"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { CheckCircle } from "lucide-react";

export default function ContactForm() {
  const t = useTranslations("forms.common");
  const tc = useTranslations("forms.contact");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new FormData(e.currentTarget);
    const data = {
      firstName: formData.get("firstName"),
      lastName: formData.get("lastName"),
      companyName: formData.get("companyName"),
      email: formData.get("email"),
      phone: formData.get("phone"),
      message: formData.get("message"),
      consent_given: formData.get("consent_given") === "on",
      consent_text: "Acconsento al trattamento dei miei dati personali per essere ricontattato.",
    };

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/forms/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || t("error"));
      }

      setSuccess(true);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="text-center py-8">
        <CheckCircle className="h-10 w-10 text-primary mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">{tc("successTitle")}</h2>
        <p className="text-muted-foreground mb-6">{tc("successDesc")}</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{tc("title")}</h2>
      <p className="text-sm text-muted-foreground mb-6">{tc("subtitle")}</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="firstName">{t("firstName")}</Label>
            <Input id="firstName" name="firstName" required placeholder="Mario" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="lastName">{t("lastName")}</Label>
            <Input id="lastName" name="lastName" required placeholder="Rossi" />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="companyName">{t("company")}</Label>
          <Input id="companyName" name="companyName" placeholder="La tua azienda" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="email">{t("email")}</Label>
            <Input id="email" name="email" type="email" required placeholder="mario@azienda.com" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">{t("phone")}</Label>
            <Input id="phone" name="phone" type="tel" placeholder="+39 333..." />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="message">{tc("message")}</Label>
          <Textarea
            id="message"
            name="message"
            required
            rows={4}
            placeholder={tc("messagePlaceholder")}
          />
        </div>

        <div className="flex items-start gap-2 mt-4">
          <Checkbox id="consent_given" name="consent_given" required className="mt-0.5" />
          <Label htmlFor="consent_given" className="text-xs text-muted-foreground font-normal leading-relaxed">
            {tc("consent")}
          </Label>
        </div>

        {error && <div className="text-destructive text-sm mt-2">{error}</div>}

        <Button type="submit" className="w-full mt-6" disabled={loading}>
          {loading ? t("sending") : tc("submit")}
        </Button>
      </form>
    </div>
  );
}