# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Dipendenze sistema per Playwright/Chromium (Scrapling StealthyFetcher)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium runtime deps
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    libx11-6 libxcb1 libxext6 fonts-liberation \
    # Utility
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Aggiungiamo un utente non root per maggiore sicurezza
RUN groupadd -r crmuser && useradd -r -g crmuser crmuser

COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

RUN pip install --no-cache /wheels/*

# Installa browser Playwright (Chromium) per StealthyFetcher
# PLAYWRIGHT_BROWSERS_PATH indica dove salvare i browser
ENV PLAYWRIGHT_BROWSERS_PATH=/home/crmuser/.cache/ms-playwright
RUN playwright install chromium --with-deps 2>/dev/null || true

COPY app/ ./app/

# Permessi
RUN chown -R crmuser:crmuser /app /home/crmuser 2>/dev/null || true

# Drop to non-root
USER crmuser

ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 2 \
    --loop uvloop \
    --access-log
