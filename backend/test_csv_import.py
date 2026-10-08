"""
Test diagnostico import CSV leads — MongoDB (Motor).

Uso:
    cd backend && source venv/bin/activate
    MONGODB_URI=mongodb://localhost:27017 python test_csv_import.py
    python test_csv_import.py /percorso/alternativo/leads.csv
"""
import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

CSV_PATH = "/Users/fred/dev/CRM-AICHAIN/docs/leads  - LEADS.csv"


# ── Analisi statica del CSV ──────────────────────────────────────────────────

def analyze_csv(path: str) -> None:
    with open(path, "rb") as f:
        raw = f.read()

    text = raw.decode("utf-8")
    lines = text.strip().split("\n")
    header = lines[0]
    cols = [c.strip() for c in header.split(",")]

    print(f"\n{'='*60}")
    print("ANALISI CSV")
    print(f"File  : {path}")
    print(f"{'='*60}")
    print(f"Colonne ({len(cols)}): {cols}")
    print(f"Righe dati: {len(lines) - 1}")

    missing_email = []
    col_mismatch = []

    for i, line in enumerate(lines[1:], start=2):
        fields = line.split(",")
        if len(fields) != len(cols):
            col_mismatch.append((i, len(fields), line.strip()))
        else:
            email_idx = cols.index("email") if "email" in cols else -1
            if email_idx >= 0:
                email_val = fields[email_idx].strip()
                if not email_val:
                    missing_email.append(i)

    if col_mismatch:
        print(f"\n⚠️  {len(col_mismatch)} righe con numero campi errato:")
        for row, n, preview in col_mismatch:
            print(f"   Riga {row}: {n} campi (attesi {len(cols)})")
            print(f"      → {preview}")
    else:
        print(f"\n✅ Tutte le {len(lines)-1} righe hanno {len(cols)} colonne")

    if missing_email:
        print(f"\n⚠️  {len(missing_email)} righe senza email (saranno scartate): righe {missing_email}")
    else:
        print(f"✅ Tutte le righe hanno email")

    return raw


# ── Test import via LeadService con MongoDB mockato ───────────────────────────

async def _run_import_mocked(csv_content: str) -> dict:
    """
    Esegue LeadService.import_csv() con MongoDB completamente mockato.
    Simula: email già presenti = nessuna (DB vuoto).
    """
    from app.services.lead_service import LeadService

    created = []

    async def fake_find_by_email(email: str):
        # Simula DB vuoto — nessun duplicato
        return None

    async def fake_create_lead(data, created_by: str):
        doc = {"id": f"fake-{len(created)}", "email": data.email}
        created.append(doc)
        return doc

    service = LeadService()
    service.find_by_email = fake_find_by_email
    service.create_lead = fake_create_lead

    results = await service.import_csv(csv_content, created_by="test-user")
    results["_created_sample"] = [c["email"] for c in created[:5]]
    return results


async def _run_import_real(csv_content: str) -> dict:
    """
    Esegue LeadService.import_csv() contro MongoDB reale.
    Richiede MONGODB_URI env var o MongoDB locale su 27017.
    """
    from app.services.lead_service import LeadService
    service = LeadService()
    return await service.import_csv(csv_content, created_by="test-import-user")


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else CSV_PATH
    if not os.path.exists(path):
        print(f"File non trovato: {path}")
        sys.exit(1)

    raw = analyze_csv(path)
    csv_content = raw.decode("utf-8")

    # Modalità scelta dalla variabile d'ambiente REAL_DB=1
    use_real = os.environ.get("REAL_DB", "0") == "1"

    print(f"\n{'='*60}")
    if use_real:
        print("IMPORT REALE (MongoDB)")
        print("ATTENZIONE: scriverà dati reali nel database!")
        print(f"{'='*60}")
        results = asyncio.run(_run_import_real(csv_content))
    else:
        print("IMPORT DRY-RUN (MongoDB mockato — DB vuoto simulato)")
        print("Per eseguire su DB reale: REAL_DB=1 python test_csv_import.py")
        print(f"{'='*60}")
        results = asyncio.run(_run_import_mocked(csv_content))

    print("\nRISULTATI:")
    print(f"  Totale elaborati : {results.get('total', '?')}")
    print(f"  ✅ Importati      : {results.get('imported', '?')}")
    print(f"  ⏭️  Saltati        : {results.get('skipped', '?')}")

    if results.get("errors"):
        print(f"\n  Errori ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"    • {err}")

    if results.get("_created_sample"):
        print(f"\n  Esempio email importate: {results['_created_sample']}")

    print(f"{'='*60}")


if __name__ == "__main__":
    main()
