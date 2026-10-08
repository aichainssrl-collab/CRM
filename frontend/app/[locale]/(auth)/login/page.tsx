"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { login } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Zap, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const t = useTranslations("auth");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      await login(email, password);
      router.push("/crm");
    } catch {
      setError(t("invalidCredentials"));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid min-h-svh lg:grid-cols-[1.1fr_1fr]">
      {/* Left panel — brand */}
      <div className="relative hidden lg:flex flex-col bg-primary text-primary-foreground p-10 overflow-hidden">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 opacity-[0.04]" style={{
          backgroundImage: "linear-gradient(rgba(255,255,255,.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.4) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }} />
        {/* Gradient orb */}
        <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute top-20 -right-20 h-64 w-64 rounded-full bg-white/5 blur-2xl" />

        <div className="relative flex items-center gap-2.5 font-semibold text-lg">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/15 backdrop-blur-sm">
            <Zap className="size-5" />
          </div>
          AiChain CRM
        </div>

        <div className="relative mt-auto space-y-8">
          <div className="space-y-3">
            <h2 className="text-3xl font-bold tracking-tight leading-tight">
              {t("heroTitle")}
            </h2>
            <p className="text-base text-primary-foreground/70 leading-relaxed max-w-sm">
              {t("heroSubtitle")}
            </p>
          </div>

          <div className="flex items-center gap-4">
            {[
              { value: "3x", label: t("statConversion") },
              { value: "40%", label: t("statFaster") },
              { value: "100%", label: t("statGdpr") },
            ].map((stat) => (
              <div key={stat.label} className="flex-1 rounded-lg bg-white/8 backdrop-blur-sm px-3 py-2.5">
                <div className="text-lg font-bold">{stat.value}</div>
                <div className="text-[11px] text-primary-foreground/50">{stat.label}</div>
              </div>
            ))}
          </div>

          <footer className="text-xs text-primary-foreground/40">
            {t("brandLocation")}
          </footer>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-col items-center justify-center gap-6 p-6 md:p-10 bg-background">
        <div className="flex w-full max-w-sm flex-col gap-7">
          {/* Mobile logo */}
          <div className="flex items-center gap-2.5 self-center font-semibold lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Zap className="size-5" />
            </div>
            <span className="text-lg">AiChain CRM</span>
          </div>

          <div className="flex flex-col gap-2 text-center lg:text-left">
            <h1 className="text-2xl font-bold tracking-tight">{t("welcomeBack")}</h1>
            <p className="text-sm text-muted-foreground">
              {t("loginSubtitle")}
            </p>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="grid gap-2">
              <Label htmlFor="email">{t("email")}</Label>
              <Input
                id="email"
                type="email"
                placeholder="nome@azienda.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                disabled={isLoading}
              />
            </div>

            <div className="grid gap-2">
              <div className="flex items-center">
                <Label htmlFor="password">{t("password")}</Label>
                <a
                  href="#"
                  className="ml-auto text-xs text-muted-foreground underline-offset-4 hover:underline"
                >
                  {t("forgotPassword")}
                </a>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={isLoading}
              />
            </div>

            <Button
              type="submit"
              className={cn("w-full mt-2", isLoading && "opacity-80")}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t("loggingIn")}
                </>
              ) : (
                t("login")
              )}
            </Button>
          </form>

          <p className="text-center text-xs text-muted-foreground">
            {t("termsAccept")}{" "}
            <a href="#" className="underline underline-offset-4 hover:text-foreground">
              {t("termsOfService")}
            </a>{" "}
            {t("and")}{" "}
            <a href="#" className="underline underline-offset-4 hover:text-foreground">
              {t("privacyPolicy")}
            </a>
            .
          </p>
        </div>
      </div>
    </div>
  );
}