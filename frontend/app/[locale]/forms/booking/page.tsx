"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { CalendarCheck } from "lucide-react";

export default function BookingForm() {
  const t = useTranslations("forms.common");
  const tb = useTranslations("forms.booking");
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
      preferredDate: formData.get("preferredDate"),
      preferredTime: formData.get("preferredTime"),
      consent_given: formData.get("consent_given") === "on",
      consent_text: "Acconsento al trattamento dei miei dati personali per organizzare la demo.",
    };

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/forms/booking`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
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
        <CalendarCheck className="h-10 w-10 text-primary mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">{tb("successTitle")}</h2>
        <p className="text-muted-foreground mb-6">{tb("successDesc")}</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">{tb("title")}</h2>
      <p className="text-sm text-muted-foreground mb-6">{tb("subtitle")}</p>

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
          <Input id="companyName" name="companyName" required placeholder="La tua azienda" />
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">{t("email")}</Label>
          <Input id="email" name="email" type="email" required placeholder="mario@azienda.com" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="preferredDate">{tb("preferredDate")}</Label>
            <Input id="preferredDate" name="preferredDate" type="date" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="preferredTime">{tb("timeSlot")}</Label>
            <select
              id="preferredTime"
              name="preferredTime"
              required
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">{tb("selectTime")}</option>
              <option value="morning">{tb("morning")}</option>
              <option value="afternoon">{tb("afternoon")}</option>
            </select>
          </div>
        </div>

        <div className="flex items-start gap-2 mt-4">
          <Checkbox id="consent_given" name="consent_given" required className="mt-0.5" />
          <Label htmlFor="consent_given" className="text-xs text-muted-foreground font-normal leading-relaxed">
            {tb("consent")}
          </Label>
        </div>

        {error && <div className="text-destructive text-sm mt-2">{error}</div>}

        <Button type="submit" className="w-full mt-6" disabled={loading}>
          {loading ? t("confirming") : tb("submit")}
        </Button>
      </form>
    </div>
  );
}