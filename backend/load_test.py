import asyncio
import httpx
import time
from concurrent.futures import ThreadPoolExecutor

# Configurazione Load Test (50 req/s come richiesto da task.md)
TARGET_URL = "http://localhost:8000/api/v1/leads"
NUM_REQUESTS = 500
CONCURRENCY = 50

async def fetch(client):
    try:
        response = await client.get(TARGET_URL, params={"limit": 10})
        return response.status_code
    except Exception as e:
        return str(e)

async def run_load_test():
    print(f"🚀 Avvio Load Test su {TARGET_URL}")
    print(f"📊 Richieste totali: {NUM_REQUESTS} | Concorrenza: {CONCURRENCY}")
    
    start_time = time.time()
    
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=CONCURRENCY)) as client:
        tasks = [fetch(client) for _ in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    req_per_sec = NUM_REQUESTS / duration
    
    status_codes = {}
    for r in results:
        status_codes[r] = status_codes.get(r, 0) + 1
        
    print("\n✅ Load Test Completato")
    print(f"⏱️ Tempo totale: {duration:.2f} secondi")
    print(f"⚡ Throughput: {req_per_sec:.2f} req/s")
    print(f"📈 Risultati (Status Codes): {status_codes}")
    
    if req_per_sec >= 45: # Consideriamo un margine di tolleranza
        print("\n🟢 TEST PASSATO: Il sistema regge ~50 req/s")
    else:
        print("\n🔴 TEST FALLITO: Il sistema non regge 50 req/s")

if __name__ == "__main__":
    asyncio.run(run_load_test())
