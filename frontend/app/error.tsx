"use client";

import { Button } from "@/components/ui/button";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="flex flex-col items-center gap-4 text-center max-w-md">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
          <span className="text-3xl">!</span>
        </div>
        <h2 className="text-xl font-bold tracking-tight">Qualcosa è andato storto</h2>
        <p className="text-sm text-muted-foreground">
          Si è verificato un errore imprevisto. Riprova o torna alla dashboard.
        </p>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => reset()}>
            Riprova
          </Button>
          <Button onClick={() => (window.location.href = "/crm")}>
            Vai alla Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}