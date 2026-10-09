"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Cookie, X } from "lucide-react";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem("cookie-consent");
    if (!consent) setVisible(true);
  }, []);

  function accept() {
    localStorage.setItem("cookie-consent", "accepted");
    setVisible(false);
  }

  function decline() {
    localStorage.setItem("cookie-consent", "declined");
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6">
      <div className="mx-auto max-w-2xl rounded-xl border bg-card shadow-lg p-4 md:p-5">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Cookie className="h-4 w-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">Cookie e Privacy</p>
            <p className="text-xs text-muted-foreground mt-1">
              Utilizziamo cookie tecnici necessari al funzionamento del CRM.
              Nessun cookie di tracciamento viene installato senza il tuo consenso.
              <a href="/privacy" className="underline ml-1 hover:text-foreground">Privacy Policy</a>
            </p>
          </div>
          <button
            onClick={decline}
            className="shrink-0 text-muted-foreground/50 hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex justify-end gap-2 mt-3">
          <Button variant="ghost" size="sm" onClick={decline} className="text-xs h-8">
            Solo necessari
          </Button>
          <Button size="sm" onClick={accept} className="text-xs h-8">
            Accetta
          </Button>
        </div>
      </div>
    </div>
  );
}