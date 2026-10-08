#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Deploy AiChain CRM su GCP Cloud Run
#
# Uso:
#   ./scripts/deploy.sh                    # deploy completo (backend + frontend)
#   ./scripts/deploy.sh --backend-only     # solo backend
#   ./scripts/deploy.sh --frontend-only    # solo frontend
#   ./scripts/deploy.sh --skip-tests       # salta i test
#   ./scripts/deploy.sh --dry-run          # mostra comandi senza eseguirli
#   ./scripts/deploy.sh --tag v1.2.3       # usa tag specifico invece del commit SHA
#
# Prerequisiti:
#   - gcloud CLI autenticato (gcloud auth login)
#   - Docker installato e in esecuzione
#   - ./scripts/setup-gcp.sh già eseguito
# =============================================================================

set -euo pipefail

# ── Colori e helpers ─────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[✓]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }
step()    { echo -e "\n${BOLD}${CYAN}▶ $*${RESET}"; }
run()     {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY-RUN]${RESET} $*"
    else
        eval "$*"
    fi
}

# ── Variabili di configurazione ───────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-level-facility-479122-u4}"
REGION="${GCP_REGION:-europe-west1}"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/crm"

BACKEND_SERVICE="crm-backend"
FRONTEND_SERVICE="crm-frontend"
BACKEND_SA="${BACKEND_SERVICE}@${PROJECT_ID}.iam.gserviceaccount.com"
FRONTEND_SA="${FRONTEND_SERVICE}@${PROJECT_ID}.iam.gserviceaccount.com"

FIREBASE_PROJECT_ID="level-facility-479122-u4"
FIREBASE_STORAGE_BUCKET="${FIREBASE_PROJECT_ID}.appspot.com"

# Variabili frontend (da .env.local)
NEXT_PUBLIC_FIREBASE_API_KEY="${NEXT_PUBLIC_FIREBASE_API_KEY:-AIzaSY_SET_NEXT_PUBLIC_FIREBASE_API_KEY_ENV}"
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="${NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN:-${FIREBASE_PROJECT_ID}.firebaseapp.com}"
NEXT_PUBLIC_FIREBASE_PROJECT_ID="${NEXT_PUBLIC_FIREBASE_PROJECT_ID:-${FIREBASE_PROJECT_ID}}"
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET="${NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET:-${FIREBASE_STORAGE_BUCKET}}"
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID="${NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID:-722754739274}"
NEXT_PUBLIC_FIREBASE_APP_ID="${NEXT_PUBLIC_FIREBASE_APP_ID:-1:722754739274:web:8c52d53d85d38f6b342b33}"

# Root del progetto (directory dove si trova questo script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ── Flag CLI ─────────────────────────────────────────────────────────────────
DEPLOY_BACKEND=true
DEPLOY_FRONTEND=true
SKIP_TESTS=false
DRY_RUN=false
IMAGE_TAG=""

for arg in "$@"; do
    case $arg in
        --backend-only)  DEPLOY_FRONTEND=false ;;
        --frontend-only) DEPLOY_BACKEND=false ;;
        --skip-tests)    SKIP_TESTS=true ;;
        --dry-run)       DRY_RUN=true; warn "DRY-RUN attivo — nessun comando verrà eseguito realmente" ;;
        --tag=*)         IMAGE_TAG="${arg#*=}" ;;
        --help|-h)
            echo "Uso: $0 [--backend-only|--frontend-only] [--skip-tests] [--dry-run] [--tag=v1.2.3]"
            exit 0 ;;
        *) error "Flag sconosciuto: $arg" ;;
    esac
done

# Tag immagine: argomento --tag oppure SHA del commit git
if [[ -z "$IMAGE_TAG" ]]; then
    IMAGE_TAG=$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "latest")
fi

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║       AiChain CRM — Deploy GCP Cloud Run         ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Progetto:   ${BOLD}${PROJECT_ID}${RESET}"
echo -e "  Regione:    ${BOLD}${REGION}${RESET}"
echo -e "  Tag:        ${BOLD}${IMAGE_TAG}${RESET}"
echo -e "  Backend:    $([ "$DEPLOY_BACKEND" = true ] && echo "${GREEN}SI${RESET}" || echo "${YELLOW}SKIP${RESET}")"
echo -e "  Frontend:   $([ "$DEPLOY_FRONTEND" = true ] && echo "${GREEN}SI${RESET}" || echo "${YELLOW}SKIP${RESET}")"
echo -e "  Tests:      $([ "$SKIP_TESTS" = true ] && echo "${YELLOW}SKIP${RESET}" || echo "${GREEN}SI${RESET}")"
echo ""

# ── Prerequisiti ─────────────────────────────────────────────────────────────
step "Controllo prerequisiti"

command -v gcloud >/dev/null 2>&1 || error "gcloud CLI non trovato"
command -v docker  >/dev/null 2>&1 || error "Docker non trovato"

if [[ "$DRY_RUN" == "false" ]]; then
    gcloud auth print-access-token >/dev/null 2>&1 || error "Non autenticato. Esegui: gcloud auth login"
    gcloud config set project "$PROJECT_ID" --quiet
    success "Autenticato su progetto $PROJECT_ID"
else
    success "Autenticazione — skippata (dry-run)"
fi

# Configura Docker per Artifact Registry
run "gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet"
success "Docker configurato per Artifact Registry"

# ── Funzione deploy backend ───────────────────────────────────────────────────
deploy_backend() {
    step "BACKEND — Test"
    if [[ "$SKIP_TESTS" == "false" ]]; then
        info "Avvio test backend..."
        (
            cd "$PROJECT_ROOT/backend"
            if [[ "$DRY_RUN" == "false" ]]; then
                source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
                pip install -q -r requirements.txt
                pip install -q pytest httpx
                pytest tests/ -v --tb=short
            else
                echo -e "${YELLOW}[DRY-RUN]${RESET} pytest tests/ -v --tb=short"
            fi
        )
        success "Test backend superati"
    else
        warn "Test saltati (--skip-tests)"
    fi

    local image="${REGISTRY}/backend:${IMAGE_TAG}"
    local image_latest="${REGISTRY}/backend:latest"

    step "BACKEND — Build immagine Docker"
    info "Immagine: $image"
    run "docker build \
        -t \"${image}\" \
        -t \"${image_latest}\" \
        -f \"${PROJECT_ROOT}/backend/Dockerfile\" \
        \"${PROJECT_ROOT}/backend\""
    success "Immagine backend costruita"

    step "BACKEND — Push su Artifact Registry"
    run "docker push \"${image}\""
    run "docker push \"${image_latest}\""
    success "Immagine backend pubblicata"

    step "BACKEND — Deploy su Cloud Run"
    run "gcloud run deploy \"${BACKEND_SERVICE}\" \
        --image=\"${image}\" \
        --region=\"${REGION}\" \
        --platform=managed \
        --no-allow-unauthenticated \
        --service-account=\"${BACKEND_SA}\" \
        --memory=512Mi \
        --cpu=1 \
        --min-instances=0 \
        --max-instances=10 \
        --concurrency=80 \
        --timeout=30 \
        --set-env-vars=\"FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}\" \
        --set-env-vars=\"FIREBASE_STORAGE_BUCKET=${FIREBASE_STORAGE_BUCKET}\" \
        --set-env-vars=\"GCP_LOCATION=${REGION}\" \
        --set-env-vars=\"CLOUD_TASKS_QUEUE=crm-tasks\" \
        --set-env-vars=\"EMAIL_FROM=noreply@aichainsolutions.net\" \
        --set-env-vars=\"DEBUG=false\" \
        --set-env-vars=\"RATE_LIMIT_PER_MINUTE=60\" \
        --set-secrets=\"GOOGLE_APPLICATION_CREDENTIALS_JSON=firebase-credentials:latest\" \
        --set-secrets=\"RESEND_API_KEY=resend-api-key:latest\" \
        --set-secrets=\"MONGODB_URI=mongodb-uri:latest\" \
        --set-secrets=\"META_ACCESS_TOKEN=meta-access-token:latest\" \
        --set-secrets=\"META_AD_ACCOUNT_ID=meta-ad-account-id:latest\" \
        --project=\"${PROJECT_ID}\""

    # Recupera URL del backend deployato
    if [[ "$DRY_RUN" == "false" ]]; then
        BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)")
        export BACKEND_URL
        success "Backend deployato: ${BOLD}${BACKEND_URL}${RESET}"

        # Imposta BACKEND_INTERNAL_URL (usata dai Cloud Tasks per i callback)
        info "Impostazione BACKEND_INTERNAL_URL=$BACKEND_URL..."
        gcloud run services update "$BACKEND_SERVICE" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --set-env-vars="BACKEND_INTERNAL_URL=${BACKEND_URL}" \
            --quiet

        # Aggiorna ALLOWED_ORIGINS includendo l'URL del frontend (se già deployato)
        FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" \
            --region="$REGION" --project="$PROJECT_ID" \
            --format="value(status.url)" 2>/dev/null || echo "")
        if [[ -n "$FRONTEND_URL" ]]; then
            info "Aggiornamento ALLOWED_ORIGINS con URL frontend..."
            gcloud run services update "$BACKEND_SERVICE" \
                --region="$REGION" \
                --project="$PROJECT_ID" \
                --set-env-vars="ALLOWED_ORIGINS=[\"${FRONTEND_URL}\",\"https://crm.aichainsolutions.net\"]" \
                --quiet
        fi
    else
        BACKEND_URL="https://crm-backend-xxxx-ew.a.run.app"
        export BACKEND_URL
        echo -e "${YELLOW}[DRY-RUN]${RESET} BACKEND_URL=$BACKEND_URL"
    fi
}

# ── Funzione deploy frontend ──────────────────────────────────────────────────
deploy_frontend() {
    # Assicura che BACKEND_URL sia disponibile
    if [[ -z "${BACKEND_URL:-}" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            info "Recupero URL backend esistente..."
            BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" \
                --region="$REGION" \
                --project="$PROJECT_ID" \
                --format="value(status.url)" 2>/dev/null || "")
            [[ -z "$BACKEND_URL" ]] && error "Backend non trovato. Esegui prima il deploy del backend."
        else
            BACKEND_URL="https://crm-backend-xxxx-ew.a.run.app"
        fi
    fi

    local image="${REGISTRY}/frontend:${IMAGE_TAG}"
    local image_latest="${REGISTRY}/frontend:latest"

    step "FRONTEND — Build immagine Docker"
    info "Immagine: $image"
    info "BACKEND_URL (per rewrites): $BACKEND_URL"

    # Passiamo le variabili NEXT_PUBLIC_* come build args
    run "docker build \
        -t \"${image}\" \
        -t \"${image_latest}\" \
        --build-arg NEXT_PUBLIC_FIREBASE_API_KEY=\"${NEXT_PUBLIC_FIREBASE_API_KEY}\" \
        --build-arg NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=\"${NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN}\" \
        --build-arg NEXT_PUBLIC_FIREBASE_PROJECT_ID=\"${NEXT_PUBLIC_FIREBASE_PROJECT_ID}\" \
        --build-arg NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=\"${NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET}\" \
        --build-arg NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=\"${NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID}\" \
        --build-arg NEXT_PUBLIC_FIREBASE_APP_ID=\"${NEXT_PUBLIC_FIREBASE_APP_ID}\" \
        -f \"${PROJECT_ROOT}/frontend/Dockerfile\" \
        \"${PROJECT_ROOT}/frontend\""
    success "Immagine frontend costruita"

    step "FRONTEND — Push su Artifact Registry"
    run "docker push \"${image}\""
    run "docker push \"${image_latest}\""
    success "Immagine frontend pubblicata"

    step "FRONTEND — Deploy su Cloud Run"
    run "gcloud run deploy \"${FRONTEND_SERVICE}\" \
        --image=\"${image}\" \
        --region=\"${REGION}\" \
        --platform=managed \
        --allow-unauthenticated \
        --service-account=\"${FRONTEND_SA}\" \
        --memory=512Mi \
        --cpu=1 \
        --min-instances=0 \
        --max-instances=5 \
        --concurrency=80 \
        --timeout=30 \
        --set-env-vars=\"BACKEND_URL=${BACKEND_URL}\" \
        --set-env-vars=\"NODE_ENV=production\" \
        --project=\"${PROJECT_ID}\""

    if [[ "$DRY_RUN" == "false" ]]; then
        FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)")
        success "Frontend deployato: ${BOLD}${FRONTEND_URL}${RESET}"

        # Aggiorna ALLOWED_ORIGINS nel backend con l'URL del frontend
        info "Aggiornamento ALLOWED_ORIGINS nel backend..."
        gcloud run services update "$BACKEND_SERVICE" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --set-env-vars="ALLOWED_ORIGINS=[\"${FRONTEND_URL}\",\"https://crm.aichainsolutions.net\"]" \
            --quiet
        success "Backend ALLOWED_ORIGINS aggiornato"
    fi
}

# ── Esecuzione ────────────────────────────────────────────────────────────────
START_TIME=$(date +%s)

[[ "$DEPLOY_BACKEND" == "true" ]]  && deploy_backend
[[ "$DEPLOY_FRONTEND" == "true" ]] && deploy_frontend

# ── Riepilogo finale ──────────────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$(( END_TIME - START_TIME ))

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║            Deploy completato! 🚀                 ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Tempo totale: ${BOLD}${ELAPSED}s${RESET}"
echo -e "  Tag:          ${BOLD}${IMAGE_TAG}${RESET}"
if [[ -n "${BACKEND_URL:-}" ]]; then
    echo -e "  Backend:      ${BOLD}${BACKEND_URL}${RESET}"
fi
if [[ "$DEPLOY_FRONTEND" == "true" && "$DRY_RUN" == "false" ]]; then
    FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" \
        --region="$REGION" --project="$PROJECT_ID" \
        --format="value(status.url)" 2>/dev/null || echo "N/A")
    echo -e "  Frontend:     ${BOLD}${FRONTEND_URL}${RESET}"
fi
echo ""
echo -e "  Console GCP:  https://console.cloud.google.com/run?project=${PROJECT_ID}"
echo ""
