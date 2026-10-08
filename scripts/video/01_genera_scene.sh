#!/usr/bin/env bash
# =============================================================================
# 01_genera_scene.sh — Genera le 5 scene video con Veo 2 (Vertex AI)
#
# Uso:
#   ./scripts/video/01_genera_scene.sh              # tutte e 5 le scene
#   ./scripts/video/01_genera_scene.sh --scena 3    # solo scena specifica
#
# Prerequisiti:
#   - gcloud CLI autenticato (gcloud auth login)
#   - jq installato (brew install jq)
#   - gsutil disponibile (incluso in gcloud SDK)
# =============================================================================

set -euo pipefail
source "$(dirname "$0")/config.sh"

# ── Parametri CLI ─────────────────────────────────────────────────────────────
SCENA_SINGOLA=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --scena) SCENA_SINGOLA="$2"; shift 2 ;;
        *) error "Argomento sconosciuto: $1" ;;
    esac
done

# ── Verifica dipendenze ───────────────────────────────────────────────────────
step "Verifica dipendenze"
command -v jq     >/dev/null 2>&1 || error "jq non trovato — installa: brew install jq"
command -v gsutil >/dev/null 2>&1 || error "gsutil non trovato — installa gcloud SDK"
success "Dipendenze OK"

# ── Auth token ────────────────────────────────────────────────────────────────
step "Autenticazione Vertex AI"
TOKEN=$(gcloud auth print-access-token) || error "Impossibile ottenere token — esegui: gcloud auth login"
success "Token OK — Progetto: ${PROJECT_ID}"

# ── Bucket GCS ────────────────────────────────────────────────────────────────
step "Verifica bucket GCS"
if ! gsutil ls "${GCS_BUCKET}" >/dev/null 2>&1; then
    warn "Bucket non trovato — creazione in corso..."
    gsutil mb -p "${PROJECT_ID}" -l "${VEO_REGION}" "${GCS_BUCKET}"
    success "Bucket creato: ${GCS_BUCKET}"
else
    success "Bucket OK: ${GCS_BUCKET}"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# DATI SCENE — case invece di array associativi (compatibile bash 3.2 macOS)
# ═══════════════════════════════════════════════════════════════════════════════
get_prompt() {
    case $1 in
        1) echo "Cinematic overhead shot of an overwhelmed Italian professional at a messy desk covered in stacked contracts, folders and papers. Their hand rests on a laptop keyboard, face tired and frustrated, rubbing their eyes. Warm tungsten office light casting long shadows over the document chaos. Documentary realism, slow push-in camera move. No text, no words, no labels anywhere in the scene. Vertical 9:16." ;;
        2) echo "Abstract cinematic visualization of business documents and contracts flying chaotically through dark digital space. Red warning glows pulse around scattered papers. A clock accelerates in the background as documents scatter uncontrolled. Dark moody atmosphere conveying urgency and risk. Deep red and dark blue color palette. No text, no words, no labels anywhere in the scene. Vertical 9:16." ;;
        3) echo "Modern elegant Italian company office interior. A powerful glowing blue AI energy shield materializes and envelops the entire office in protective light. Gold data streams flow inside the shield in slow motion never escaping outward. Servers glow softly within the protected space. Premium cinematic look with dark navy background and gold light accents. Absolute sense of safety and control. No text, no words, no labels anywhere in the scene. Vertical 9:16." ;;
        4) echo "Confident smiling Italian professional team in a premium modern office in Sicily. Visual split showing chaotic document pile on one side transforming into organized glowing digital files on the other side. Gold and blue abstract data metrics float softly in background. Warm professional golden lighting. Atmosphere of trust expertise and results. No text, no words, no labels anywhere in the scene. Vertical 9:16." ;;
        5) echo "Premium dark navy background with deep blue gradient and slowly drifting golden light particles. A single glowing golden shield badge pulses gently at center screen radiating warm professional light rays outward. Minimal luxury Italian tech brand aesthetic. Slow elegant cinematic fade. No text, no words, no labels anywhere in the scene. Vertical 9:16." ;;
        *) error "Scena non valida: $1 (usa 1-5)" ;;
    esac
}

get_durata() {
    case $1 in
        1) echo 6 ;;
        2) echo 8 ;;
        3) echo 8 ;;
        4) echo 6 ;;
        5) echo 6 ;;
        *) error "Scena non valida: $1 (usa 1-5)" ;;
    esac
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNZIONE: Genera una scena con Veo 2
# ═══════════════════════════════════════════════════════════════════════════════
genera_scena() {
    local NUM=$1
    local PROMPT_TEXT
    local DURATA_SEC
    PROMPT_TEXT=$(get_prompt "$NUM")
    DURATA_SEC=$(get_durata "$NUM")

    local OUTPUT_FILE="${OUTPUT_DIR}/scena_${NUM}.mp4"

    if [[ -f "${OUTPUT_FILE}" ]]; then
        warn "Scena ${NUM} già presente — skip (elimina per rigenerare: rm ${OUTPUT_FILE})"
        return 0
    fi

    step "SCENA ${NUM} — Generazione Veo 2 (${DURATA_SEC}s)"
    info "Prompt: ${PROMPT_TEXT:0:80}..."

    # Costruisci payload — usiamo printf per evitare problemi di escape
    local PAYLOAD
    PAYLOAD=$(printf '%s' "${PROMPT_TEXT}" | jq -Rs \
        --argjson dur "${DURATA_SEC}" \
        --arg storage "${GCS_BUCKET}/scena_${NUM}/" \
        '{
            instances: [{ prompt: . }],
            parameters: {
                aspectRatio:     "9:16",
                durationSeconds: $dur,
                resolution:      "720p",
                sampleCount:     1,
                storageUri:      $storage
            }
        }')

    # Avvia long-running operation
    local RISPOSTA
    RISPOSTA=$(curl -sf -X POST \
        "${API_BASE}:predictLongRunning" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "${PAYLOAD}") || {
        echo "${RISPOSTA:-nessuna risposta}" >&2
        error "Curl fallito per Scena ${NUM}. Verifica che Veo 2 sia abilitato sul progetto."
    }

    local OPERATION
    OPERATION=$(echo "${RISPOSTA}" | jq -r '.name // empty')
    [[ -z "${OPERATION}" ]] && {
        echo "${RISPOSTA}" | jq . >&2
        error "Operazione non avviata per Scena ${NUM}"
    }

    info "Operazione avviata: ${OPERATION}"
    _attendi_e_scarica "${NUM}" "${OPERATION}" "${OUTPUT_FILE}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNZIONE: Poll operation + download
# ═══════════════════════════════════════════════════════════════════════════════
_attendi_e_scarica() {
    local NUM=$1
    local OPERATION=$2
    local OUTPUT_FILE=$3
    # Veo usa fetchPredictOperation (POST) — non il GET standard delle LRO
    local FETCH_URL="https://${VEO_REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${VEO_REGION}/publishers/google/models/${VEO_MODEL}:fetchPredictOperation"
    local FETCH_BODY
    FETCH_BODY=$(jq -n --arg op "${OPERATION}" '{"operationName": $op}')
    local TENTATIVI=0
    local MAX=120   # 120 × 15s = 30 minuti max per scena

    info "In attesa completamento Scena ${NUM}..."

    while [[ $TENTATIVI -lt $MAX ]]; do
        sleep 15
        TENTATIVI=$((TENTATIVI + 1))

        local STATO
        STATO=$(curl -sf -X POST "${FETCH_URL}" \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "Content-Type: application/json" \
            -d "${FETCH_BODY}") || continue

        local DONE
        DONE=$(echo "${STATO}" | jq -r '.done // false')

        if [[ "${DONE}" != "true" ]]; then
            printf "  ⏳ [%d/%d] Generazione in corso...\r" "${TENTATIVI}" "${MAX}"
            continue
        fi

        echo ""

        local ERRORE
        ERRORE=$(echo "${STATO}" | jq -r '.error.message // empty')
        [[ -n "${ERRORE}" ]] && error "Scena ${NUM} fallita: ${ERRORE}"

        local VIDEO_URI
        VIDEO_URI=$(echo "${STATO}" | jq -r '
            .response.videos[0].gcsUri      //
            .response.predictions[0].gcsUri //
            .response.videos[0].uri         //
            empty
        ')

        [[ -z "${VIDEO_URI}" ]] && {
            warn "URI non trovato — struttura risposta:"
            echo "${STATO}" | jq '{done, response}' >&2
            error "Impossibile estrarre URI video Scena ${NUM}"
        }

        success "Scena ${NUM} generata → ${VIDEO_URI}"
        info "Download in corso..."
        gsutil cp "${VIDEO_URI}" "${OUTPUT_FILE}"
        success "Scena ${NUM} salvata → ${OUTPUT_FILE}"
        return 0
    done

    error "Timeout — Scena ${NUM} non completata in 12 minuti"
}

# ── Esecuzione ────────────────────────────────────────────────────────────────
if [[ -n "${SCENA_SINGOLA}" ]]; then
    genera_scena "${SCENA_SINGOLA}"
else
    for i in 1 2 3 4 5; do
        genera_scena "$i"
    done
fi

# ── Riepilogo ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN}  SCENE GENERATE — riepilogo${RESET}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${RESET}"
for i in 1 2 3 4 5; do
    FILE="${OUTPUT_DIR}/scena_${i}.mp4"
    if [[ -f "${FILE}" ]]; then
        SIZE=$(du -h "${FILE}" | cut -f1)
        echo -e "  ${GREEN}✓${RESET}  scena_${i}.mp4  (${SIZE})"
    else
        echo -e "  ${RED}✗${RESET}  scena_${i}.mp4  — mancante"
    fi
done
echo ""
info "Prossimo step → bash scripts/video/02_assembla.sh"
