#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==============================================================================
# AiChain CRM - Setup Infrastruttura Google Cloud
# ==============================================================================
# Questo script automatizza la creazione delle risorse su Google Cloud per il
# backend, frontend, Secret Manager e Artifact Registry.
# 
# Prerequisiti:
# 1. Aver installato gcloud CLI
# 2. Aver effettuato il login: gcloud auth login
# 3. Aver settato il progetto di default: gcloud config set project [PROJECT_ID]
# ==============================================================================

# Variabili (modifica secondo le tue necessità)
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west1"
REPO_NAME="crm-repo"
BACKEND_SERVICE_NAME="crm-backend"
FRONTEND_SERVICE_NAME="crm-frontend"

echo "====================================================================="
echo "🚀 Avvio setup infrastruttura GCP per il progetto: $PROJECT_ID"
echo "🌍 Regione: $REGION"
echo "====================================================================="

# 1. Abilitare le API necessarie
echo "✅ Abilitazione API (Cloud Run, Secret Manager, Artifact Registry, Cloud Build, Monitoring, Logging)..."
gcloud services enable \
    run.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com

# 2. Configurazione Artifact Registry EU
echo "✅ Creazione repository Docker in Artifact Registry ($REGION)..."
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION >/dev/null 2>&1; then
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for AiChain CRM images"
    echo "Repository $REPO_NAME creato."
else
    echo "Il repository $REPO_NAME esiste già."
fi

# 3. Setup Secret Manager (creazione placeholder)
echo "✅ Creazione Secret in Secret Manager..."
SECRETS=("FIREBASE_CREDENTIALS" "RESEND_API_KEY" "APOLLO_API_KEY")

for SECRET in "${SECRETS[@]}"; do
    if ! gcloud secrets describe $SECRET >/dev/null 2>&1; then
        gcloud secrets create $SECRET --replication-policy="automatic"
        echo "Secret $SECRET creato. RICORDATI di aggiungere il valore:"
        echo "   echo -n 'TUO_VALORE' | gcloud secrets versions add $SECRET --data-file=-"
    else
        echo "Il secret $SECRET esiste già."
    fi
done

# Permettere al service account di default di Cloud Run di leggere i secrets
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "✅ Assegnazione ruoli al Service Account di Compute per Secret Manager..."
for SECRET in "${SECRETS[@]}"; do
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:${COMPUTE_SA}" \
        --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true
done

# 4. Creazione Dashboard di Cloud Monitoring
echo "✅ Setup Cloud Monitoring Dashboard (Latency, Error Rate, Instances)..."
gcloud monitoring dashboards create --config-from-file=gcp/dashboard.json || echo "Dashboard già esistente o errore nella creazione."

# 5. Setup Cloud Logging Alert per errori 5xx
echo "✅ Setup Alerting Policy per Errori 5xx..."
gcloud alpha monitoring policies create --policy-from-file=gcp/alert-5xx.json || echo "Policy già esistente o errore nella creazione."

echo "====================================================================="
echo "🎉 Setup Infrastruttura Completato!"
echo "====================================================================="
echo ""
echo "PROSSIMI PASSI:"
echo "1. Popola i secrets in Secret Manager tramite console GCP o gcloud CLI."
echo "2. Lancia le pipeline di CI/CD usando Cloud Build:"
echo "   gcloud builds submit --config cloudbuild.yaml ."
echo "   gcloud builds submit --config cloudbuild-frontend.yaml ."
