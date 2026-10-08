#!/usr/bin/env bash
# =============================================================================
# config.sh — Configurazione Video Ads Generator (Veo 2 / Vertex AI)
#
# Usa il progetto GCP esistente di AiChain CRM.
# ⚠️  Veo 2 è disponibile SOLO in us-central1 (requisito Google).
#     Il bucket GCS per i video viene creato lì, separato dall'infra CRM EU.
# =============================================================================

# ── Progetto GCP (stesso del CRM AiChain) ────────────────────────────────────
export PROJECT_ID="${GCP_PROJECT_ID:-level-facility-479122-u4}"
export VEO_REGION="us-central1"          # unica regione supportata da Veo 2
export VEO_MODEL="veo-2.0-generate-001"
export GCS_BUCKET="gs://${PROJECT_ID}-video-ads"
export OUTPUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/output"

# ── Endpoint API ──────────────────────────────────────────────────────────────
export API_BASE="https://${VEO_REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${VEO_REGION}/publishers/google/models/${VEO_MODEL}"

# ── Colori (stesso stile deploy.sh) ───────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[✓]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}${CYAN}▶ $*${RESET}"; }

mkdir -p "${OUTPUT_DIR}"
