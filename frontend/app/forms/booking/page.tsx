"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function BookingForm() {
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
      // Endpoint to be created in backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/forms/booking`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Errore durante la prenotazione. Potrebbe non essere ancora implementato sul server.");
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
        <span className="material-symbols-outlined text-4xl text-primary mb-4 block">event_available</span>
        <h2 className="text-xl font-bold mb-2">Prenotazione Confermata!</h2>
        <p className="text-on-surface-variant mb-6">
          Riceverai a breve un&apos;email con il link per accedere alla videocall e i dettagli dell&apos;incontro.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Prenota una Demo</h2>
      <p className="text-sm text-on-surface-variant mb-6">
        Scegli una data e un orario per parlare con uno dei nostri esperti.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label htmlFor="firstName" className="text-sm font-medium">Nome</label>
            <Input id="firstName" name="firstName" required placeholder="Mario" />
          </div>
          <div className="space-y-2">
            <label htmlFor="lastName" className="text-sm font-medium">Cognome</label>
            <Input id="lastName" name="lastName" required placeholder="Rossi" />
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="companyName" className="text-sm font-medium">Azienda</label>
          <Input id="companyName" name="companyName" required placeholder="La tua azienda" />
        </div>

        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">Email lavorativa</label>
          <Input id="email" name="email" type="email" required placeholder="mario@azienda.com" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label htmlFor="preferredDate" className="text-sm font-medium">Data Preferita</label>
            <Input id="preferredDate" name="preferredDate" type="date" required />
          </div>
          <div className="space-y-2">
            <label htmlFor="preferredTime" className="text-sm font-medium">Fascia Oraria</label>
            <select 
              id="preferredTime" 
              name="preferredTime" 
              required
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">Seleziona...</option>
              <option value="morning">Mattina (09:00 - 12:00)</option>
              <option value="afternoon">Pomeriggio (14:00 - 18:00)</option>
            </select>
          </div>
        </div>

        <div className="flex items-start gap-2 mt-4">
          <input 
            type="checkbox" 
            id="consent_given" 
            name="consent_given" 
            required 
            className="mt-1"
          />
          <label htmlFor="consent_given" className="text-xs text-on-surface-variant">
            Acconsento al trattamento dei miei dati personali per gestire la prenotazione.
          </label>
        </div>

        {error && <div className="text-error text-sm mt-2">{error}</div>}

        <Button type="submit" className="w-full mt-6" disabled={loading}>
          {loading ? "Conferma in corso..." : "Conferma Prenotazione"}
        </Button>
      </form>
    </div>
  );
}
