"use client";

import { useState } from "react";
import { login } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function LoginPage() {
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
    } catch (err: unknown) {
      console.error("Login error:", err);
      setError("Login failed. Check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-8">
      <main className="w-full max-w-[420px]">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 bg-primary rounded-xl flex items-center justify-center mb-4 shadow-sm border border-primary">
            <span className="material-symbols-outlined text-on-primary text-[28px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              data_usage
            </span>
          </div>
          <h1 className="font-display text-display text-on-surface">AiChain</h1>
          <p className="font-body text-body text-on-surface-variant mt-1">Enterprise CRM</p>
        </div>

        {/* Login Card */}
        <Card className="bg-surface-container-lowest border-outline-variant shadow-[0_4px_12px_rgba(0,0,0,0.03)]">
          <CardHeader className="pb-6">
            <CardTitle className="font-h2 text-h2 text-on-surface">Sign In</CardTitle>
            <CardDescription className="font-body text-body text-on-surface-variant mt-1">
              Enter your details to access your account.
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {error && <p className="text-error mb-4 font-small text-small">{error}</p>}

            <form onSubmit={handleSubmit} className="flex flex-col gap-stack_gap">
              {/* Email Field */}
              <div className="flex flex-col gap-1.5">
                <label className="font-small-medium text-small-medium text-on-surface" htmlFor="email">Email Address</label>
                <Input 
                  id="email" 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com" 
                  className="h-input_height border-outline-variant bg-surface-container-lowest font-body focus-visible:ring-primary" 
                  required 
                />
              </div>

              {/* Password Field */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <label className="font-small-medium text-small-medium text-on-surface" htmlFor="password">Password</label>
                  <a href="#" className="font-small-medium text-small-medium text-on-surface-variant hover:text-primary transition-colors">Forgot Password?</a>
                </div>
                <Input 
                  id="password" 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••" 
                  className="h-input_height border-outline-variant bg-surface-container-lowest font-body focus-visible:ring-primary" 
                  required 
                />
              </div>

              {/* Primary Submit */}
              <Button 
                type="submit" 
                disabled={isLoading}
                className="h-input_height w-full mt-2 bg-primary text-on-primary font-body-medium hover:bg-primary/90"
              >
                {isLoading ? "Signing In..." : "Sign In"}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative flex items-center py-6">
              <div className="flex-grow border-t border-outline-variant/60"></div>
              <span className="flex-shrink-0 mx-4 font-small text-small text-on-surface-variant uppercase tracking-wider">Or continue with</span>
              <div className="flex-grow border-t border-outline-variant/60"></div>
            </div>

            {/* Secondary Action */}
            <Button variant="outline" type="button" className="h-input_height w-full border-outline-variant text-on-surface font-body-medium flex items-center justify-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"></path>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"></path>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"></path>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"></path>
              </svg>
              Google
            </Button>
          </CardContent>
        </Card>

        {/* Footer Links */}
        <div className="mt-8 text-center">
          <p className="font-small text-small text-on-surface-variant">
            By signing in, you agree to our 
            <a href="#" className="underline hover:text-on-surface transition-colors ml-1">Terms of Service</a> and 
            <a href="#" className="underline hover:text-on-surface transition-colors ml-1">Privacy Policy</a>.
          </p>
        </div>
      </main>
    </div>
  );
}
