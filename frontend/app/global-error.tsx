"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="it">
      <body>
        <div style={{
          display: "flex",
          minHeight: "100vh",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px",
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}>
          <div style={{ textAlign: "center", maxWidth: "400px" }}>
            <h1 style={{ fontSize: "24px", fontWeight: "bold", marginBottom: "8px" }}>Errore Critico</h1>
            <p style={{ color: "#666", marginBottom: "24px" }}>
              Si è verificato un errore critico nell&apos;applicazione.
            </p>
            <button
              onClick={() => reset()}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "1px solid #ccc",
                background: "white",
                cursor: "pointer",
                marginRight: "8px",
              }}
            >
              Riprova
            </button>
            <a
              href="/crm"
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                background: "#1d3173",
                color: "white",
                textDecoration: "none",
              }}
            >
              Dashboard
            </a>
          </div>
        </div>
      </body>
    </html>
  );
}