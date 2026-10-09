"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, ArrowLeft } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col items-center bg-background p-6">
      <div className="w-full max-w-3xl">
        <Link href="/">
          <Button variant="ghost" size="sm" className="mb-6 gap-1">
            <ArrowLeft className="h-3.5 w-3.5" />
            Torna alla home
          </Button>
        </Link>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <CardTitle>Privacy Policy</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">Ultimo aggiornamento: Gennaio 2026</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <section>
              <h3 className="font-semibold">1. Titolare del trattamento</h3>
              <p className="text-sm text-muted-foreground">
                AiChain Solutions S.r.l. — Catania, Italia — info@aichainsolutions.net
              </p>
            </section>

            <section>
              <h3 className="font-semibold">2. Dati raccolti</h3>
              <p className="text-sm text-muted-foreground">
                Raccogliamo dati identificativi (nome, email, azienda, telefono), dati di navigazione e
                dati inseriti nei moduli di contatto o prenotazione. I dati sono trattati esclusivamente
                per finalità commerciali e di gestione della relazione con il cliente.
              </p>
            </section>

            <section>
              <h3 className="font-semibold">3. Base giuridica</h3>
              <p className="text-sm text-muted-foreground">
                Il trattamento si basa sul consimento dell&apos;interessato (art. 6.1.a GDPR),
                sull&apos;esecuzione di un contratto (art. 6.1.b) e sul legittimo interesse del
                titolare (art. 6.1.f).
              </p>
            </section>

            <section>
              <h3 className="font-semibold">4. Conservazione</h3>
              <p className="text-sm text-muted-foreground">
                I dati sono conservati per il tempo necessario al raggiungimento delle finalità per cui
                sono stati raccolti, e comunque non oltre 24 mesi dal ultimo contatto, salvo obblighi
                di legge.
              </p>
            </section>

            <section>
              <h3 className="font-semibold">5. Diritti dell&apos;interessato</h3>
              <p className="text-sm text-muted-foreground">
                Ai sensi degli artt. 15-22 GDPR, l&apos;interessato può esercitare i diritti di accesso,
                rettifica, cancellazione, limitazione, portabilità e opposizione contattando
                info@aichainsolutions.net.
              </p>
            </section>

            <section>
              <h3 className="font-semibold">6. Trasferimento dati</h3>
              <p className="text-sm text-muted-foreground">
                I dati sono trattati su infrastrutture europee (Firebase Auth EU, MongoDB EU, Resend EU).
                Nessun dato viene trasferito al di fuori dell&apos;Unione Europea.
              </p>
            </section>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}