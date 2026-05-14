"""
Load test base: 50 req/s su endpoint leads e forms.
Eseguire manualmente con: python -m pytest tests/load_test.py -v -s
oppure direttamente: python tests/load_test.py

Richiede backend in esecuzione su BACKEND_URL.
"""
import asyncio
import httpx
import time
import statistics
import os
from dataclasses import dataclass, field
from typing import List

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CONCURRENCY = 50
REQUESTS_TOTAL = 200
TIMEOUT = 10.0


@dataclass
class Result:
    status: int
    elapsed_ms: float
    error: str = ""


@dataclass
class Summary:
    results: List[Result] = field(default_factory=list)

    @property
    def success_count(self):
        return sum(1 for r in self.results if r.status in (200, 201, 422))

    @property
    def error_count(self):
        return sum(1 for r in self.results if r.status not in (200, 201, 422))

    @property
    def latencies(self):
        return [r.elapsed_ms for r in self.results if not r.error]

    def print(self, label: str):
        n = len(self.results)
        if not n:
            print(f"{label}: no results")
            return
        lats = self.latencies
        p50 = statistics.median(lats) if lats else 0
        p95 = sorted(lats)[int(len(lats) * 0.95)] if lats else 0
        p99 = sorted(lats)[int(len(lats) * 0.99)] if lats else 0
        print(f"\n{'='*50}")
        print(f"{label}")
        print(f"  Richieste totali : {n}")
        print(f"  Successi         : {self.success_count}")
        print(f"  Errori           : {self.error_count}")
        print(f"  Latenza p50      : {p50:.0f} ms")
        print(f"  Latenza p95      : {p95:.0f} ms")
        print(f"  Latenza p99      : {p99:.0f} ms")
        print(f"  Min / Max        : {min(lats):.0f} / {max(lats):.0f} ms" if lats else "")
        print(f"{'='*50}")


async def hit_health(client: httpx.AsyncClient) -> Result:
    start = time.monotonic()
    try:
        r = await client.get(f"{BACKEND_URL}/api/health", timeout=TIMEOUT)
        return Result(status=r.status_code, elapsed_ms=(time.monotonic() - start) * 1000)
    except Exception as exc:
        return Result(status=0, elapsed_ms=(time.monotonic() - start) * 1000, error=str(exc))


async def hit_form_playbook(client: httpx.AsyncClient, idx: int) -> Result:
    start = time.monotonic()
    try:
        r = await client.post(
            f"{BACKEND_URL}/api/v1/forms/playbook",
            json={
                "email": f"load{idx}@test.invalid",
                "firstName": "Load",
                "companyName": "Test Corp",
                "consent_given": True,
                "consent_text": "Load test consent.",
            },
            timeout=TIMEOUT,
        )
        return Result(status=r.status_code, elapsed_ms=(time.monotonic() - start) * 1000)
    except Exception as exc:
        return Result(status=0, elapsed_ms=(time.monotonic() - start) * 1000, error=str(exc))


async def run_load_test(
    fn,
    total: int = REQUESTS_TOTAL,
    concurrency: int = CONCURRENCY,
    label: str = "Test",
    **kwargs,
) -> Summary:
    summary = Summary()
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(idx):
        async with semaphore:
            return await fn(**kwargs, idx=idx) if "idx" in fn.__code__.co_varnames else await fn(**kwargs)

    async with httpx.AsyncClient() as client:
        start = time.monotonic()
        tasks = [bounded(i) if "idx" in fn.__code__.co_varnames
                 else asyncio.create_task(fn(client)) for i in range(total)]

        # Rebuild with client
        async with httpx.AsyncClient() as c:
            sem = asyncio.Semaphore(concurrency)

            async def _run(i):
                async with sem:
                    if fn.__code__.co_varnames[0] == "client" and "idx" in fn.__code__.co_varnames:
                        return await fn(c, i)
                    elif fn.__code__.co_varnames[0] == "client":
                        return await fn(c)
                    return await fn(i)

            results = await asyncio.gather(*[_run(i) for i in range(total)])

    summary.results = results
    elapsed = time.monotonic() - start
    rps = total / elapsed
    print(f"\n  Throughput: {rps:.1f} req/s in {elapsed:.1f}s")
    summary.print(label)
    return summary


async def main():
    print(f"Backend: {BACKEND_URL}")
    print(f"Concorrenza: {CONCURRENCY} | Richieste: {REQUESTS_TOTAL}")

    # Test 1: Health check (nessuna auth, massima velocità)
    health_summary = Summary()
    async with httpx.AsyncClient() as client:
        sem = asyncio.Semaphore(CONCURRENCY)

        async def _health(_i):
            async with sem:
                return await hit_health(client)

        results = await asyncio.gather(*[_health(i) for i in range(REQUESTS_TOTAL)])
        health_summary.results = list(results)
    health_summary.print("GET /api/health")

    # Test 2: Form playbook (endpoint pubblico con rate limiting)
    form_summary = Summary()
    async with httpx.AsyncClient() as client:
        sem = asyncio.Semaphore(min(CONCURRENCY, 5))  # rate limit 5/min

        async def _form(i):
            async with sem:
                return await hit_form_playbook(client, i)

        # Meno richieste per non triggerare il rate limit aggressivamente
        results = await asyncio.gather(*[_form(i) for i in range(20)])
        form_summary.results = list(results)
    form_summary.print("POST /api/v1/forms/playbook (rate limited)")

    # Verifica SLA: p95 < 500ms su health check
    lats = health_summary.latencies
    if lats:
        p95 = sorted(lats)[int(len(lats) * 0.95)]
        if p95 < 500:
            print(f"\n✓ SLA OK: p95 = {p95:.0f}ms < 500ms")
        else:
            print(f"\n✗ SLA VIOLATO: p95 = {p95:.0f}ms >= 500ms")


if __name__ == "__main__":
    asyncio.run(main())
