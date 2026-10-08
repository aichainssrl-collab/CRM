export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="flex flex-col items-center gap-4 text-center max-w-md">
        <div className="text-6xl font-bold text-muted-foreground/20">404</div>
        <h2 className="text-xl font-bold tracking-tight">Pagina non trovata</h2>
        <p className="text-sm text-muted-foreground">
          La pagina che stai cercando non esiste o è stata spostata.
        </p>
        <a
          href="/it/crm"
          className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm shadow-primary/25 hover:bg-primary/90 hover:shadow-md hover:shadow-primary/20 active:scale-[0.97] transition-all duration-150 ease-out"
        >
          Torna alla Dashboard
        </a>
      </div>
    </div>
  );
}