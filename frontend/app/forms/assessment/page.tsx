"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function AssessmentForm() {
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
      industry: formData.get("industry"),
      aiMaturity: formData.get("aiMaturity"),
      painPoints: formData.get("painPoints"),
      consent_given: formData.get("consent_given") === "on",
      consent_text: "Acconsento al trattamento dei miei dati personali per ricevere i risultati dell'assessment.",
    };

    try {
      // Endpoint to be created in backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/forms/assessment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        // Fallback or error handling
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Errore durante l'invio del form. Potrebbe non essere ancora implementato sul server.");
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
        <span className="material-symbols-outlined text-4xl text-primary mb-4 block">fact_check</span>
        <h2 className="text-xl font-bold mb-2">Assessment Completato!</h2>
        <p className="text-muted-foreground mb-6">
          Stiamo elaborando le tue risposte. Riceverai un report dettagliato via email a breve.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">AI Readiness Assessment</h2>
      <p className="text-sm text-muted-foreground mb-6">
        Valuta il livello di maturità della tua azienda e scopri dove l&apos;AI può portare più valore.
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

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label htmlFor="companyName" className="text-sm font-medium">Azienda</label>
            <Input id="companyName" name="companyName" required placeholder="La tua azienda" />
          </div>
          <div className="space-y-2">
            <label htmlFor="industry" className="text-sm font-medium">Settore</label>
            <Input id="industry" name="industry" required placeholder="Es. Manifatturiero, Servizi..." />
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">Email lavorativa</label>
          <Input id="email" name="email" type="email" required placeholder="mario@azienda.com" />
        </div>

        <div className="space-y-2">
          <label htmlFor="aiMaturity" className="text-sm font-medium">Livello attuale di adozione AI</label>
          <select 
            id="aiMaturity" 
            name="aiMaturity" 
            required
            className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="">Seleziona...</option>
            <option value="none">Nessun utilizzo attuale</option>
            <option value="exploring">Stiamo esplorando le possibilità</option>
            <option value="pilots">Abbiamo alcuni progetti pilota in corso</option>
            <option value="production">Abbiamo soluzioni AI in produzione</option>
          </select>
        </div>

        <div className="space-y-2">
          <label htmlFor="painPoints" className="text-sm font-medium">Qual è la tua sfida principale oggi?</label>
          <textarea 
            id="painPoints" 
            name="painPoints" 
            required 
            rows={3}
            className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            placeholder="Descrivi brevemente i processi che vorresti ottimizzare..." 
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
            Acconsento al trattamento dei miei dati personali per ricevere il report di valutazione.
          </label>
        </div>

        {error && <div className="text-destructive text-sm mt-2">{error}</div>}

        <Button type="submit" className="w-full mt-6" disabled={loading}>
          {loading ? "Elaborazione in corso..." : "Ottieni Risultati"}
        </Button>
      </form>
    </div>
  );
}
