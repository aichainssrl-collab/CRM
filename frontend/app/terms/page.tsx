"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, ArrowLeft } from "lucide-react";

export default function TermsPage() {
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
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <CardTitle>Termini di Servizio</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">Ultimo aggiornamento: Gennaio 2026</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none space-y-4">
            <section>
              <h3 className="font-semibold">1. Oggetto</h3>
              <p className="text-sm text-muted-foreground">
                I presenti Termini disciplinano l&apos;utilizzo della piattaforma AiChain CRM
                (di seguito &quot;Piattaforma&quot;) fornita da AiChain Solutions S.r.l.
              </p>
            </section>

            <section>
              <h3 className="font-semibold">2. Servizio</h3>
              <p className="text-sm text-muted-foreground">
                La Piattaforma offre strumenti di Customer Relationship Management per la gestione di
                lead, opportunità commerciali, attività e comunicazioni aziendali.
              </p>
            </section>

            <section>
              <h3 className="font-semibold">3. Account</h3>
              <p className="text-sm text-muted-foreground">
                L&apos;accesso alla Piattaforma è riservato agli utenti autorizzati. L&apos;utente è
                responsabile della riservatezza delle proprie credenziali e di tutte le attività svolte
                tramite il proprio account.
              </p>
            </section>

            <section>
              <h3 className="font-semibold">4. Uso accettabile</h3>
              <p className="text-sm text-muted-foreground">
                È vietato utilizzare la Piattaforma per attività illecite, spam, violazione della privacy
                altrui o qualsiasi uso che violi normative applicabili.
              </p>
            </section>

            <section>
              <h3 className="font-semibold">5. Limitazione di responsabilità</h3>
              <p className="text-sm text-muted-foreground">
                AiChain Solutions non è responsabile di danni indiretti derivanti dall&apos;uso della
                Piattaforma. Il servizio è fornito &quot;così com&apos;è&quot;.
              </p>
            </section>

            <section>
              <h3 className="font-semibold">6. Modifiche</h3>
              <p className="text-sm text-muted-foreground">
                AiChain Solutions si riserva il diritto di modificare i presenti Termini in qualsiasi
                momento. Le modifiche saranno comunicate tramite la Piattaforma.
              </p>
            </section>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}