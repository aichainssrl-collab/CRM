"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Cookie, X } from "lucide-react";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const bannerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const consent = localStorage.getItem("cookie-consent");
    if (!consent) setVisible(true);
  }, []);

  // Riserva lo spazio del banner (body padding + CSS var per le pagine)
  useEffect(() => {
    if (!visible) {
      document.documentElement.style.removeProperty("--cookie-banner-h");
      document.body.style.removeProperty("padding-bottom");
      return;
    }
    const el = bannerRef.current;
    const apply = () => {
      const h = el?.offsetHeight ?? 0;
      document.documentElement.style.setProperty("--cookie-banner-h", `${h}px`);
      document.body.style.paddingBottom = `${h}px`;
    };
    apply();
    const ro = new ResizeObserver(apply);
    if (el) ro.observe(el);
    window.addEventListener("resize", apply);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", apply);
      document.documentElement.style.removeProperty("--cookie-banner-h");
      document.body.style.removeProperty("padding-bottom");
    };
  }, [visible]);

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
    <div
      ref={bannerRef}
      className="fixed bottom-0 left-0 right-0 z-50 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] md:p-6 md:pb-[max(1.5rem,env(safe-area-inset-bottom))]"
    >
      <div className="mx-auto max-w-2xl rounded-xl border bg-card shadow-lg p-3 md:p-5">
        <div className="flex items-start gap-2.5 md:gap-3">
          <div className="hidden sm:flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Cookie className="h-4 w-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium">Cookie e Privacy</p>
              <button
                onClick={decline}
                aria-label="Chiudi"
                className="shrink-0 text-muted-foreground/50 hover:text-foreground transition-colors sm:hidden"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 leading-snug">
              Solo cookie tecnici. Nessun tracciamento senza consenso.
              <a href="/privacy" className="underline ml-1 hover:text-foreground">Privacy</a>
            </p>
          </div>
          <button
            onClick={decline}
            aria-label="Chiudi"
            className="hidden sm:block shrink-0 text-muted-foreground/50 hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="flex flex-wrap justify-end gap-2 mt-2.5 md:mt-3">
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
