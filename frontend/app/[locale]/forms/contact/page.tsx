"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

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
        <span className="material-symbols-outlined text-4xl text-primary mb-4 block">check_circle</span>
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
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label htmlFor="firstName" className="text-sm font-medium">{t("firstName")}</label>
            <Input id="firstName" name="firstName" required placeholder="Mario" />
          </div>
          <div className="space-y-2">
            <label htmlFor="lastName" className="text-sm font-medium">{t("lastName")}</label>
            <Input id="lastName" name="lastName" required placeholder="Rossi" />
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="companyName" className="text-sm font-medium">{t("company")}</label>
          <Input id="companyName" name="companyName" placeholder="La tua azienda" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">{t("email")}</label>
            <Input id="email" name="email" type="email" required placeholder="mario@azienda.com" />
          </div>
          <div className="space-y-2">
            <label htmlFor="phone" className="text-sm font-medium">{t("phone")}</label>
            <Input id="phone" name="phone" type="tel" placeholder="+39 333..." />
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="message" className="text-sm font-medium">{tc("message")}</label>
          <textarea 
            id="message" 
            name="message" 
            required 
            rows={4}
            className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            placeholder={tc("messagePlaceholder")}
          />
        </div>

        <div className="flex items-start gap-2 mt-4">
          <input 
            type="checkbox" 
            id="consent_given" 
            name="consent_given" 
            required 
            className="mt-1"
          />
          <label htmlFor="consent_given" className="text-xs text-muted-foreground">
            {tc("consent")}
          </label>
        </div>

        {error && <div className="text-destructive text-sm mt-2">{error}</div>}

        <Button type="submit" className="w-full mt-6" disabled={loading}>
          {loading ? t("sending") : tc("submit")}
        </Button>
      </form>
    </div>
  );
}