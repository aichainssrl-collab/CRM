export default function FormsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-[100dvh] bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-card rounded-lg shadow-lg border border-border p-6">
        <div className="text-center mb-6">
          <h1 className="text-xl font-semibold text-foreground">AiChain</h1>
          <p className="text-sm text-muted-foreground">Enterprise Solutions</p>
        </div>
        {children}
      </div>
    </div>
  );
}