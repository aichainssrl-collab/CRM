import "./globals.css";
import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { cn } from "@/lib/utils";
import { CookieConsent } from "@/components/crm/CookieConsent";

export const metadata: Metadata = {
  title: "AiChain CRM",
  description: "Enterprise CRM for AiChain Solutions",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it" className={cn("light", GeistSans.variable, GeistMono.variable)} suppressHydrationWarning>
      <body
        className={`${GeistSans.variable} ${GeistMono.variable} antialiased bg-background selection:bg-primary/10 selection:text-primary`}
      >
        {children}
        <CookieConsent />
      </body>
    </html>
  );
}