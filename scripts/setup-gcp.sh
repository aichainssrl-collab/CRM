#!/usr/bin/env bash
# =============================================================================
# setup-gcp.sh — Setup infrastruttura GCP (eseguire UNA SOLA VOLTA)
#
# Cosa fa:
#   - Abilita le API GCP necessarie
#   - Crea Artifact Registry per le immagini Docker
#   - Crea i service account per backend e frontend
#   - Crea i secret in Secret Manager
#   - Configura i permessi IAM
#
# Uso:
#   chmod +x scripts/setup-gcp.sh
#   ./scripts/setup-gcp.sh
# =============================================================================

set -euo pipefail

# ── Colori ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${BLUE}[INFO]${RESET} $*"; }
success() { echo -e "${GREEN}[OK]${RESET}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET} $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }
step()    { echo -e "\n${BOLD}══ $* ══${RESET}"; }

# ── Configurazione ───────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-level-facility-479122-u4}"
REGION="${GCP_REGION:-europe-west1}"
REGISTRY_REPO="crm"

BACKEND_SA="crm-backend"
FRONTEND_SA="crm-frontend"

# ── Prerequisiti ─────────────────────────────────────────────────────────────
command -v gcloud >/dev/null 2>&1 || error "gcloud CLI non installato. Installa da: https://cloud.google.com/sdk"

# ── Auth e progetto ──────────────────────────────────────────────────────────
step "Autenticazione GCP"
gcloud auth print-access-token >/dev/null 2>&1 || {
    warn "Non autenticato. Avvio login..."
    gcloud auth login
}
gcloud config set project "$PROJECT_ID"
success "Progetto: $PROJECT_ID"

# ── Abilita API ───────────────────────────────────────────────────────────────
step "Abilitazione API GCP"
APIS=(
    "run.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudtasks.googleapis.com"
    "firebase.googleapis.com"
    "iam.googleapis.com"
)
for api in "${APIS[@]}"; do
    info "Abilitando $api..."
    gcloud services enable "$api" --project="$PROJECT_ID" --quiet
done
success "Tutte le API abilitate"

# ── Artifact Registry ─────────────────────────────────────────────────────────
step "Artifact Registry"
if gcloud artifacts repositories describe "$REGISTRY_REPO" \
    --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    warn "Repository '$REGISTRY_REPO' già esistente, skip."
else
    gcloud artifacts repositories create "$REGISTRY_REPO" \
        --repository-format=docker \
        --location="$REGION" \
        --description="AiChain CRM Docker images" \
        --project="$PROJECT_ID"
    success "Repository Artifact Registry creato: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_REPO}"
fi

# ── Service Accounts ──────────────────────────────────────────────────────────
step "Service Accounts"

create_sa() {
    local name="$1" display="$2"
    local email="${name}@${PROJECT_ID}.iam.gserviceaccount.com"
    if gcloud iam service-accounts describe "$email" --project="$PROJECT_ID" >/dev/null 2>&1; then
        warn "SA $email già esistente, skip."
    else
        gcloud iam service-accounts create "$name" \
            --display-name="$display" \
            --project="$PROJECT_ID"
        success "Creato SA: $email"
    fi
    echo "$email"
}

BACKEND_SA_EMAIL=$(create_sa "$BACKEND_SA" "AiChain CRM Backend")
FRONTEND_SA_EMAIL=$(create_sa "$FRONTEND_SA" "AiChain CRM Frontend")

# ── IAM Roles ────────────────────────────────────────────────────────────────
step "IAM Roles"
grant_role() {
    local member="$1" role="$2"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${member}" \
        --role="$role" \
        --condition=None \
        --quiet 2>/dev/null || true
}

# Backend: Firebase Auth (verify tokens), Secret Manager, Cloud Tasks, Storage
grant_role "$BACKEND_SA_EMAIL" "roles/secretmanager.secretAccessor"
grant_role "$BACKEND_SA_EMAIL" "roles/cloudtasks.enqueuer"
grant_role "$BACKEND_SA_EMAIL" "roles/storage.objectAdmin"
grant_role "$BACKEND_SA_EMAIL" "roles/firebase.sdkAdminServiceAgent"

# Frontend: solo lettura Secret Manager (per NEXT_PUBLIC vars se necessario)
grant_role "$FRONTEND_SA_EMAIL" "roles/secretmanager.secretAccessor"

success "Ruoli IAM configurati"

# ── Secret Manager ────────────────────────────────────────────────────────────
step "Secret Manager — Creazione secrets (valori da inserire manualmente)"

create_secret_placeholder() {
    local secret_id="$1" description="$2"
    if gcloud secrets describe "$secret_id" --project="$PROJECT_ID" >/dev/null 2>&1; then
        warn "Secret '$secret_id' già esistente, skip."
    else
        echo "PLACEHOLDER" | gcloud secrets create "$secret_id" \
            --data-file=- \
            --replication-policy="user-managed" \
            --locations="$REGION" \
            --project="$PROJECT_ID"
        warn "⚠️  Secret '$secret_id' creato con valore PLACEHOLDER — aggiornare con il valore reale!"
        info "   $description"
    fi
    # Permesso al backend SA di leggere il secret
    gcloud secrets add-iam-policy-binding "$secret_id" \
        --member="serviceAccount:${BACKEND_SA_EMAIL}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" \
        --quiet 2>/dev/null || true
}

create_secret_placeholder "firebase-credentials" \
    "JSON del service account Firebase Admin SDK (scarica da Firebase Console → Project Settings → Service Accounts)"

create_secret_placeholder "resend-api-key" \
    "API key Resend (da https://resend.com/api-keys)"

create_secret_placeholder "mongodb-uri" \
    "URI MongoDB Atlas (es: mongodb+srv://user:pass@cluster.mongodb.net/crm-aichain-db)"

create_secret_placeholder "meta-access-token" \
    "Meta Ads access token — da Meta for Developers → Graph API Explorer (permessi: ads_read, read_insights)"

create_secret_placeholder "meta-ad-account-id" \
    "Meta Ad Account ID — formato: act_XXXXXXXXX (da Ads Manager → in alto a sinistra)"

echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${YELLOW}  IMPORTANTE: aggiorna i secret prima del deploy!${RESET}"
echo -e "${YELLOW}  Usa:${RESET}"
echo -e "  echo '\$VALUE' | gcloud secrets versions add firebase-credentials --data-file=- --project=$PROJECT_ID"
echo -e "  echo '\$VALUE' | gcloud secrets versions add resend-api-key --data-file=- --project=$PROJECT_ID"
echo -e "  echo '\$VALUE' | gcloud secrets versions add mongodb-uri --data-file=- --project=$PROJECT_ID"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${RESET}"

# ── Cloud Build — permessi per deploy ────────────────────────────────────────
step "Cloud Build Service Account — permessi"

CB_SA_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
CB_SA_EMAIL="${CB_SA_NUMBER}@cloudbuild.gserviceaccount.com"

grant_role "$CB_SA_EMAIL" "roles/run.admin"
grant_role "$CB_SA_EMAIL" "roles/iam.serviceAccountUser"
grant_role "$CB_SA_EMAIL" "roles/artifactregistry.writer"
grant_role "$CB_SA_EMAIL" "roles/secretmanager.secretAccessor"

success "Cloud Build configurato per il deploy"

# ── Cloud Tasks Queue ─────────────────────────────────────────────────────────
step "Cloud Tasks — Creazione queue 'crm-tasks'"
TASKS_QUEUE="crm-tasks"

if gcloud tasks queues describe "$TASKS_QUEUE" \
    --location="$REGION" --project="$PROJECT_ID" >/dev/null 2>&1; then
    warn "Queue '$TASKS_QUEUE' già esistente, skip."
else
    gcloud tasks queues create "$TASKS_QUEUE" \
        --location="$REGION" \
        --project="$PROJECT_ID" \
        --max-attempts=3 \
        --min-backoff=10s \
        --max-backoff=300s \
        --max-dispatches-per-second=100 \
        --max-concurrent-dispatches=10
    success "Cloud Tasks queue '$TASKS_QUEUE' creata in $REGION"
fi

# ── Riepilogo ────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  Setup completato!${RESET}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Project ID:     ${BOLD}${PROJECT_ID}${RESET}"
echo -e "  Region:         ${BOLD}${REGION}${RESET}"
echo -e "  Registry:       ${BOLD}${REGION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_REPO}${RESET}"
echo -e "  Backend SA:     ${BOLD}${BACKEND_SA_EMAIL}${RESET}"
echo -e "  Frontend SA:    ${BOLD}${FRONTEND_SA_EMAIL}${RESET}"
echo ""
echo -e "  Prossimo step:  ${BOLD}./scripts/deploy.sh${RESET}"
echo ""
echo -e "${YELLOW}  ⚠️  STEP MANUALI RIMANENTI:${RESET}"
echo -e "  1. Popola i secrets in Secret Manager (vedi sopra)"
echo -e "  2. Crea cluster MongoDB Atlas → ottieni URI → popola secret 'mongodb-uri'"
echo -e "  3. Aggiungi i domini Cloud Run agli Authorized Domains Firebase Auth:"
echo -e "     https://console.firebase.google.com/project/${PROJECT_ID}/authentication/settings"
echo -e "     → Aggiungi: *.run.app (o URL specifico dopo il primo deploy)"
echo ""
