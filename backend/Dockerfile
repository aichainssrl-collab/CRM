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

# Aggiungiamo un utente non root per maggiore sicurezza
RUN groupadd -r crmuser && useradd -r -g crmuser crmuser

COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

RUN pip install --no-cache /wheels/*

COPY app/ ./app/

# Permessi
RUN chown -R crmuser:crmuser /app

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
