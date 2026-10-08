#!/usr/bin/env bash
# =============================================================================
# make_video.sh — Master script: genera e assembla il video ads AiChain
#
# Esegue in sequenza:
#   1. Genera le 5 scene con Veo 2 (Vertex AI)
#   2. Assembla il video finale con ffmpeg + voiceover Google TTS
#
# Uso:
#   ./scripts/video/make_video.sh                    # pipeline completa
#   ./scripts/video/make_video.sh --solo-assembla    # salta generazione scene
#   ./scripts/video/make_video.sh --no-audio         # senza voiceover
#   ./scripts/video/make_video.sh --scena 3          # rigenera solo scena 3
#
# Prerequisiti:
#   - gcloud CLI autenticato: gcloud auth login
#   - jq:     brew install jq
#   - ffmpeg: brew install ffmpeg
#   - Veo 2 abilitato sul progetto GCP (richiede allowlist Google)
#   - Text-to-Speech API abilitata: gcloud services enable texttospeech.googleapis.com
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║   🎬  AiChain Video Ads Generator                ║${RESET}"
echo -e "${BOLD}${CYAN}║       Veo 2  ×  Vertex AI  ×  Instagram 9:16     ║${RESET}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════╝${RESET}"
echo -e "  Progetto GCP:  ${PROJECT_ID}"
echo -e "  Modello video: ${VEO_MODEL}"
echo -e "  Output:        ${OUTPUT_DIR}/"
echo ""

# ── Parametri CLI ─────────────────────────────────────────────────────────────
SOLO_ASSEMBLA=false
NO_AUDIO=false
SCENA_SINGOLA=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --solo-assembla) SOLO_ASSEMBLA=true; shift ;;
        --no-audio)      NO_AUDIO=true; shift ;;
        --scena)         SCENA_SINGOLA="$2"; shift 2 ;;
        --help|-h)
            sed -n '3,20p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) error "Argomento sconosciuto: $1 — usa --help per la guida" ;;
    esac
done

# ── Verifica gcloud auth ──────────────────────────────────────────────────────
step "Verifica autenticazione GCP"
gcloud auth print-access-token >/dev/null 2>&1 || \
    error "Non autenticato — esegui: gcloud auth login"
ACCOUNT=$(gcloud config get-value account 2>/dev/null)
success "Autenticato come: ${ACCOUNT}"
success "Progetto attivo: $(gcloud config get-value project 2>/dev/null)"

# ── Abilita API necessarie ────────────────────────────────────────────────────
step "Verifica API GCP abilitate"
APIS_NEEDED=(
    "aiplatform.googleapis.com"
    "texttospeech.googleapis.com"
    "storage.googleapis.com"
)
for API in "${APIS_NEEDED[@]}"; do
    STATUS=$(gcloud services list --enabled --filter="name:${API}" \
        --format="value(name)" 2>/dev/null)
    if [[ -z "${STATUS}" ]]; then
        info "Abilitazione ${API}..."
        gcloud services enable "${API}" --project="${PROJECT_ID}"
        success "${API} abilitata"
    else
        success "${API} — già abilitata"
    fi
done

# ── Step 1: Genera scene ──────────────────────────────────────────────────────
if [[ "${SOLO_ASSEMBLA}" == "false" ]]; then
    if [[ -n "${SCENA_SINGOLA}" ]]; then
        info "Modalità: rigenera solo Scena ${SCENA_SINGOLA}"
        bash "${SCRIPT_DIR}/01_genera_scene.sh" --scena "${SCENA_SINGOLA}"
    else
        info "Modalità: genera tutte e 5 le scene"
        bash "${SCRIPT_DIR}/01_genera_scene.sh"
    fi
else
    warn "Generazione scene saltata (--solo-assembla)"
fi

# ── Step 2: Assembla ──────────────────────────────────────────────────────────
if [[ "${NO_AUDIO}" == "true" ]]; then
    bash "${SCRIPT_DIR}/02_assembla.sh" --no-audio
else
    bash "${SCRIPT_DIR}/02_assembla.sh"
fi

echo ""
echo -e "${BOLD}${GREEN}  🚀  Pipeline completata!${RESET}"
echo -e "  Video pronto in: ${OUTPUT_DIR}/aichain_ads_instagram_FINAL.mp4"
echo ""
