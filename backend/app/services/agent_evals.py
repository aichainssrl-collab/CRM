"""
Agent evals — suite di intent IT + metriche qualità (Fase C).

Usare in CI o via `python -m app.services.agent_evals`.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvalCase:
    phrase: str
    expected_tool: Optional[str] = None  # tool atteso dal parser (None = solo LLM)
    must_contain: Optional[str] = None   # sottostringa nella reply
    expect_ok: bool = True
    tags: list[str] = field(default_factory=list)


# 30+ frasi IT — regression suite
EVAL_CASES: list[EvalCase] = [
    EvalCase("Crea lead Mario Rossi email mario@studio.it", "create_lead", tags=["lead"]),
    EvalCase("Nuovo lead Anna Bianchi email anna@acme.it", "create_lead", tags=["lead"]),
    EvalCase("Dammi il settore di marioti@gmail.com", "find_lead", tags=["lead"]),
    EvalCase("Quale settore ha marioti@gmail.com?", "find_lead", tags=["lead"]),
    EvalCase("Dammi email di Mock Match", "find_lead", tags=["lead"]),
    EvalCase("Chi è Mock Match", "find_lead", tags=["lead"]),
    EvalCase("Danilo Zanni in quale azienda lavora?", "find_lead", tags=["lead"]),
    EvalCase("Imposta settore marketing sul lead marioti@gmail.com", "update_lead", tags=["lead"]),
    EvalCase("Inserisci media nel lead marioti@gmail.com", "update_lead", tags=["lead"]),
    EvalCase("Crea task Chiama Mario entro 2026-02-01 email mario@studio.it urgente", "create_task", tags=["task"]),
    EvalCase("Mostra i task", "list_tasks", tags=["task"]),
    EvalCase("I miei task", "list_tasks", tags=["task"]),
    EvalCase("Mostra deal in trattativa", "list_deals", tags=["deal"]),
    EvalCase("Mostra deal", "list_deals", tags=["deal"]),
    EvalCase("Sposta deal ZenTratto in proposta", "update_deal", tags=["deal"]),
    EvalCase("Pipeline dei deal", "deal_pipeline", tags=["deal"]),
    EvalCase("Bozza email a mario@studio.it oggetto Demo testo Ciao", "draft_email", tags=["email"]),
    EvalCase("Invia email a mario@studio.it oggetto Demo testo Ciao", "send_email", tags=["email"]),
    EvalCase("Mostra fatture", "list_invoices", tags=["billing"]),
    EvalCase("Mostra proposte", "list_proposals", tags=["billing"]),
    EvalCase("Statistiche fatture", "invoice_stats", tags=["billing"]),
    EvalCase("Mostra prodotti", "list_products", tags=["content"]),
    EvalCase("Mostra report", "list_reports", tags=["ops"]),
    EvalCase("KPI", "crm_kpi", tags=["ops"]),
    EvalCase("Export csv", "export_csv", tags=["ops"]),
    EvalCase("Riepilogo CRM", "crm_summary", tags=["ops"]),
    EvalCase("Scadenze dei prossimi 7 giorni", "list_deadlines", tags=["task"]),
    EvalCase("Prenota demo con Mario Rossi email mario@studio.it il 2026-03-10 alle 15:00", "book_demo", tags=["demo"]),
    EvalCase("Genera report settimanale", "generate_report", tags=["report"]),
    EvalCase("Aiuto", "help", tags=["meta"]),
    EvalCase("Mostra calendario", "list_calendar_events", tags=["ops"]),
    EvalCase("Mostra competitor", "competitor_status", tags=["ops"]),
]


async def run_parser_evals() -> dict:
    """Valuta solo il parser deterministico (no LLM, offline)."""
    from app.services.crm_agent_service import parse_command

    total = len(EVAL_CASES)
    passed = 0
    failures = []
    for case in EVAL_CASES:
        if not case.expected_tool:
            continue
        parsed = parse_command(case.phrase)
        tool = parsed[0] if parsed else None
        if tool == case.expected_tool:
            passed += 1
        else:
            failures.append({
                "phrase": case.phrase,
                "expected": case.expected_tool,
                "got": tool,
            })
    checked = sum(1 for c in EVAL_CASES if c.expected_tool)
    rate = round(passed / checked * 100, 1) if checked else 0.0
    return {
        "total": checked,
        "passed": passed,
        "failed": len(failures),
        "accuracy": rate,
        "failures": failures,
    }


def main() -> None:
    report = asyncio.run(run_parser_evals())
    print(f"Parser evals: {report['passed']}/{report['total']} ({report['accuracy']}%)")
    for f in report["failures"]:
        print(f"  FAIL: {f['phrase']!r} → got={f['got']!r} expected={f['expected']!r}")
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
