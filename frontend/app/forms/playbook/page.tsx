"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function PlaybookForm() {
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
      consent_given: formData.get("consent_given") === "on",
      consent_text: "Acconsento al trattamento dei miei dati personali per ricevere il playbook.",
    };

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/forms/playbook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Errore durante l'invio del form");
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
        <h2 className="text-xl font-bold mb-2">Playbook richiesto con successo!</h2>
        <p className="text-muted-foreground mb-6">
          Controlla la tua email, ti abbiamo inviato il link per scaricare il materiale.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Scarica il Playbook</h2>
      <p className="text-sm text-muted-foreground mb-6">
        Compila il modulo per ricevere gratuitamente il nostro playbook sull&apos;AI aziendale.
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
          <Input id="companyName" name="companyName" placeholder="La tua azienda" />
        </div>

        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">Email lavorativa</label>
          <Input id="email" name="email" type="email" required placeholder="mario.rossi@azienda.com" />
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
            Acconsento al trattamento dei miei dati personali in accordo con la Privacy Policy per ricevere comunicazioni di marketing e il materiale richiesto.
          </label>
        </div>

        {error && <div className="text-destructive text-sm mt-2">{error}</div>}

        <Button type="submit" className="w-full mt-6" disabled={loading}>
          {loading ? "Invio in corso..." : "Scarica Playbook"}
        </Button>
      </form>
    </div>
  );
}
