export default function FormsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-surface-dim flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-background rounded-xl shadow-lg border border-outline-variant p-6">
        <div className="text-center mb-6">
          <h1 className="text-h2 font-h2 text-on-background">AiChain</h1>
          <p className="text-body-medium text-on-surface-variant">Enterprise Solutions</p>
        </div>
        {children}
      </div>
    </div>
  );
}
