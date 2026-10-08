#!/usr/bin/env bash
# =============================================================================
# 02_assembla.sh — Assembla le scene nel video finale (ffmpeg)
#
# Uso:
#   ./scripts/video/02_assembla.sh              # assembla + aggiungi voiceover
#   ./scripts/video/02_assembla.sh --no-audio   # solo video, niente voiceover
#
# Prerequisiti:
#   - ffmpeg installato (brew install ffmpeg)
#   - Le 5 scene già generate (01_genera_scene.sh)
# =============================================================================

set -euo pipefail
source "$(dirname "$0")/config.sh"

# ── Parametri CLI ─────────────────────────────────────────────────────────────
NO_AUDIO=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-audio) NO_AUDIO=true; shift ;;
        *) error "Argomento sconosciuto: $1" ;;
    esac
done

# ── Verifica dipendenze ───────────────────────────────────────────────────────
step "Verifica dipendenze"
command -v ffmpeg >/dev/null 2>&1 || error "ffmpeg non trovato — installa: brew install ffmpeg"
success "ffmpeg OK — $(ffmpeg -version 2>&1 | head -1)"

# ── Verifica scene ────────────────────────────────────────────────────────────
step "Verifica scene disponibili"
MANCANTI=0
for i in 1 2 3 4 5; do
    FILE="${OUTPUT_DIR}/scena_${i}.mp4"
    if [[ -f "${FILE}" ]]; then
        success "scena_${i}.mp4 — OK"
    else
        warn "scena_${i}.mp4 — MANCANTE"
        MANCANTI=$((MANCANTI + 1))
    fi
done
[[ $MANCANTI -gt 0 ]] && error "${MANCANTI} scene mancanti — esegui prima: bash scripts/video/01_genera_scene.sh"

# ── Lista scene per ffmpeg ────────────────────────────────────────────────────
LIST_FILE="${OUTPUT_DIR}/lista_scene.txt"
cat > "${LIST_FILE}" << EOF
file 'scena_1.mp4'
file 'scena_2.mp4'
file 'scena_3.mp4'
file 'scena_4.mp4'
file 'scena_5.mp4'
EOF

# ── Nomi file output ──────────────────────────────────────────────────────────
VIDEO_RAW="${OUTPUT_DIR}/aichain_ads_raw.mp4"
VIDEO_FINAL="${OUTPUT_DIR}/aichain_ads_instagram_FINAL.mp4"
VOICEOVER_FILE="${OUTPUT_DIR}/voiceover.mp3"

# ── Step 1: Unisci le scene ───────────────────────────────────────────────────
step "Unione delle 5 scene"
ffmpeg -y \
    -f concat -safe 0 \
    -i "${LIST_FILE}" \
    -vf "scale=1080:1920:force_original_aspect_ratio=decrease,\
         pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,\
         format=yuv420p" \
    -c:v libx264 \
    -preset slow \
    -crf 18 \
    -r 24 \
    -movflags +faststart \
    -an \
    "${VIDEO_RAW}" \
    2>&1 | tail -5
success "Video raw creato → ${VIDEO_RAW}"

# ── Step 2: Voiceover (Google TTS via gcloud) ─────────────────────────────────
if [[ "${NO_AUDIO}" == "false" ]]; then
    step "Generazione Voiceover (Google Text-to-Speech)"

    # Testo voiceover in italiano
    VOICEOVER_TEXT="Quante ore perdi ogni settimana a cercare un contratto, una firma, un documento? Contratti scaduti. Firme non valide. I tuoi dati aziendali su server che non controlli. Sanzioni eIDAS fino a cinquantamila euro per ogni atto non conforme. Con AiChain Solutions, l intelligenza artificiale arriva direttamente nella tua azienda. I tuoi dati non escono mai. On-premise o cloud privato europeo. Compliance GDPR e eIDAS garantita. I nostri clienti riducono del settanta percento il tempo nella ricerca documentale. ROI in quattro mesi. Precisione al novantanove virgola otto percento. Analisi gratuita, risposta in ventiquattro ore, zero impegno. AiChain Solutions, l AI che resta dove deve stare."

    # Payload TTS
    TTS_PAYLOAD=$(jq -n \
        --arg text   "${VOICEOVER_TEXT}" \
        '{
            input: { text: $text },
            voice: {
                languageCode: "it-IT",
                name: "it-IT-Neural2-C",
                ssmlGender: "MALE"
            },
            audioConfig: {
                audioEncoding: "MP3",
                speakingRate: 0.92,
                pitch: -1.0
            }
        }')

    TOKEN=$(gcloud auth print-access-token)
    TTS_RESPONSE=$(curl -sf -X POST \
        "https://texttospeech.googleapis.com/v1/text:synthesize" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "X-Goog-User-Project: ${PROJECT_ID}" \
        -H "Content-Type: application/json" \
        -d "${TTS_PAYLOAD}") || {
        warn "TTS fallito — assemblo senza voiceover (usa --no-audio per saltare)"
        NO_AUDIO=true
    }

    if [[ "${NO_AUDIO}" == "false" ]]; then
        # Decodifica base64 → mp3
        echo "${TTS_RESPONSE}" | jq -r '.audioContent' | base64 --decode > "${VOICEOVER_FILE}"
        success "Voiceover generato → ${VOICEOVER_FILE}"
    fi
fi

# ── Step 3: Assembla video + audio ────────────────────────────────────────────
step "Assemblaggio finale"
if [[ "${NO_AUDIO}" == "false" ]] && [[ -f "${VOICEOVER_FILE}" ]]; then
    info "Unione video + voiceover..."
    ffmpeg -y \
        -i "${VIDEO_RAW}" \
        -i "${VOICEOVER_FILE}" \
        -c:v copy \
        -c:a aac \
        -b:a 192k \
        -shortest \
        -movflags +faststart \
        "${VIDEO_FINAL}" \
        2>&1 | tail -5
else
    warn "Nessun audio — copio video raw come finale"
    cp "${VIDEO_RAW}" "${VIDEO_FINAL}"
fi

# ── Riepilogo ─────────────────────────────────────────────────────────────────
FILESIZE=$(du -h "${VIDEO_FINAL}" | cut -f1)
DURATION=$(ffprobe -v quiet -show_entries format=duration \
    -of csv=p=0 "${VIDEO_FINAL}" 2>/dev/null | xargs printf "%.0f" || echo "?")

echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN}  ✅  VIDEO ADS PRONTO PER INSTAGRAM${RESET}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${RESET}"
echo -e "  📁 File:         ${VIDEO_FINAL}"
echo -e "  📐 Risoluzione:  1080 × 1920  (9:16)"
echo -e "  🎞  Formato:      MP4 H.264 + AAC"
echo -e "  ⏱  Durata:       ~${DURATION} secondi"
echo -e "  💾 Dimensione:   ${FILESIZE}"
echo ""
echo -e "${BOLD}  📱 Meta Ads Manager — impostazioni consigliate:${RESET}"
echo -e "  ├─ Tipo annuncio:  Video singolo"
echo -e "  ├─ Placement:      Instagram Reels + Feed"
echo -e "  ├─ CTA button:     Scopri di più"
echo -e "  ├─ URL:            https://www.aichainsolutions.net/prodotti/su-misura"
echo -e "  └─ Headline:       L'AI che non porta i tuoi dati fuori dall'azienda"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${RESET}"
