#!/bin/bash
# Setup GCP: service account, IAM roles, Secret Manager, Artifact Registry.
# Eseguire una sola volta per ambiente (dev/prod).
# Prerequisito: gcloud CLI autenticato con account owner del progetto.
# Uso: ./setup-gcp.sh dev   oppure   ./setup-gcp.sh prod

set -euo pipefail

ENV=${1:-dev}

if [ "$ENV" = "prod" ]; then
  PROJECT_ID="aichain-crm-prod"
else
  PROJECT_ID="aichain-crm-dev"
fi

REGION="europe-west1"
SA_NAME="crm-backend"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Progetto: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# ── Service Account ──────────────────────────────────────────
echo "==> Creazione service account $SA_NAME..."
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="AiChain CRM Backend" \
  --description="Service account per Cloud Run backend CRM" \
  2>/dev/null || echo "  (già esistente)"

# ── IAM Roles (least privilege) ──────────────────────────────
echo "==> Assegnazione ruoli IAM..."

ROLES=(
  "roles/datastore.user"              # Firestore read/write
  "roles/storage.objectAdmin"         # Firebase Storage
  "roles/cloudtasks.enqueuer"         # Cloud Tasks — crea task
  "roles/cloudtasks.taskRunner"       # Cloud Tasks — esegue task (OIDC)
  "roles/secretmanager.secretAccessor" # Secret Manager — legge segreti
  "roles/logging.logWriter"           # Cloud Logging
  "roles/monitoring.metricWriter"     # Cloud Monitoring
)

for ROLE in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --quiet
  echo "  + $ROLE"
done

# ── Secret Manager — crea segreti ───────────────────────────
echo "==> Creazione segreti in Secret Manager..."

SECRETS=(
  "RESEND_API_KEY"
  "GOOGLE_APPLICATION_CREDENTIALS_JSON"
)

for SECRET in "${SECRETS[@]}"; do
  gcloud secrets create "$SECRET" \
    --replication-policy="user-managed" \
    --locations="$REGION" \
    2>/dev/null || echo "  (segreto $SECRET già esistente)"
done

echo ""
echo "  Per caricare i valori:"
echo "  echo -n 'valore' | gcloud secrets versions add RESEND_API_KEY --data-file=-"

# ── Artifact Registry ────────────────────────────────────────
echo "==> Creazione Artifact Registry EU..."
gcloud artifacts repositories create crm-images \
  --repository-format=docker \
  --location="$REGION" \
  --description="Docker images AiChain CRM" \
  2>/dev/null || echo "  (già esistente)"

# ── Cloud Tasks Queue ────────────────────────────────────────
echo "==> Creazione queue Cloud Tasks..."
gcloud tasks queues create crm-tasks \
  --location="$REGION" \
  2>/dev/null || echo "  (già esistente)"

# ── Chiave service account (SOLO per sviluppo locale) ────────
if [ "$ENV" = "dev" ]; then
  KEY_FILE="service-account-dev.json"
  echo "==> Generazione chiave per sviluppo locale → $KEY_FILE"
  gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL"
  echo "  Aggiungi al .env:"
  echo "  GOOGLE_APPLICATION_CREDENTIALS_JSON=\$(cat $KEY_FILE | jq -c .)"
  echo ""
  echo "  ATTENZIONE: non committare $KEY_FILE nel repository!"
fi

echo ""
echo "==> Setup $ENV completato."
echo "    Progetto: $PROJECT_ID"
echo "    Service account: $SA_EMAIL"
