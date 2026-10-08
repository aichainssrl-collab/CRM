#!/usr/bin/env bash
# =============================================================================
# 03_aggiungi_testo.sh — Overlay testo professionale con ffmpeg drawtext
#
# Usa drawtext (built-in in tutti i build ffmpeg) + filter_complex_script
# per evitare problemi di escaping sulla shell.
#
# Timecodes (scene Kling 3.0 Turbo da 5s — video totale 25s):
#   Scena 1 — Hook:      0s –  5s
#   Scena 2 — Problema:  5s – 10s
#   Scena 3 — Soluzione: 10s – 15s
#   Scena 4 — Prova:     15s – 20s
#   Scena 5 — CTA:       20s – 25s
# =============================================================================

set -euo pipefail
source "$(dirname "$0")/config.sh"

INPUT="${OUTPUT_DIR}/aichain_ads_raw.mp4"
FILTER_SCRIPT="/tmp/aichain_filter.txt"
FONT_BOLD="/tmp/aichain_ArialBold.ttf"
FONT_REG="/tmp/aichain_Arial.ttf"
VIDEO_TMP="${OUTPUT_DIR}/aichain_ads_testo_raw.mp4"
FINAL="${OUTPUT_DIR}/aichain_ads_instagram_FINAL.mp4"

[[ -f "${INPUT}" ]] || error "Video raw non trovato — esegui prima: bash scripts/video/02_assembla.sh --no-audio"
command -v ffmpeg >/dev/null 2>&1 || error "ffmpeg non trovato"

# ── Copia font in /tmp (path senza spazi — richiesto da drawtext) ─────────────
step "Preparazione font"
cp "/System/Library/Fonts/Supplemental/Arial Bold.ttf" "${FONT_BOLD}"
cp "/System/Library/Fonts/Supplemental/Arial.ttf"      "${FONT_REG}"
success "Font pronti → ${FONT_BOLD}"

# ── Genera filter_complex_script via Python ───────────────────────────────────
step "Generazione filter script"

python3 - << 'PYEOF'
import subprocess, sys

FONT_BOLD = "/tmp/aichain_ArialBold.ttf"
FONT_REG  = "/tmp/aichain_Arial.ttf"
FFMPEG    = "/opt/homebrew/Cellar/ffmpeg-full/8.1.1/bin/ffmpeg"
INPUT     = "/Users/fred/dev/CRM-AICHAIN/scripts/video/output/aichain_ads_raw.mp4"
OUTPUT_TMP= "/Users/fred/dev/CRM-AICHAIN/scripts/video/output/aichain_ads_testo_raw.mp4"

# NOTA: ffmpeg usa 0xRRGGBB (alpha eventualmente in coda con @) — MAI 0xAARRGGBB
WHITE  = "0xFFFFFF"
GOLD   = "0xFFCC00"
GREEN  = "0x66FF88"
RED    = "0xDD3333"
SHADOW = "black@0.8"

def bold(color=WHITE, size=82):
    return (f"fontfile={FONT_BOLD}:fontsize={size}:fontcolor={color}"
            f":bordercolor={SHADOW}:borderw=5:shadowcolor={SHADOW}:shadowx=3:shadowy=3")

def reg(color=WHITE, size=54):
    return (f"fontfile={FONT_REG}:fontsize={size}:fontcolor={color}"
            f":bordercolor={SHADOW}:borderw=3:shadowcolor={SHADOW}:shadowx=2:shadowy=2")

# NOTA: dentro 'virgolette singole' i , sono letterali — nessun \, necessario
def show(ts, te):
    return f"enable='between(t,{ts},{te})'"

def fade(ts, te):
    return (f"alpha='if(lt(t,{ts}+0.4),(t-{ts})/0.4,"
            f"if(gt(t,{te}-0.3),({te}-t)/0.3,1))'")

CX = "(w-text_w)/2"

filters = []

# SCENA 1 — Hook (0–5s) — il cliente si riconosce subito
filters += [
    f"drawtext={bold(WHITE,58)}:text='Quante ore perdi ogni settimana':x={CX}:y=520:{show(0.4,4.8)}:{fade(0.4,4.8)}",
    f"drawtext={bold(GOLD,80)}:text='a cercare documenti?':x={CX}:y=640:{show(0.8,4.8)}:{fade(0.8,4.8)}",
    f"drawtext={reg(WHITE,44)}:text='Se la risposta e troppe...':x={CX}:y=1820:{show(1.6,4.8)}:{fade(1.6,4.8)}",
]

# SCENA 2 — Problema agitato (5–10s) — nomina i rischi reali
filters += [
    f"drawtext={bold(WHITE,56)}:text='Contratti scaduti senza avviso':x={CX}:y=460:{show(5.3,9.8)}:{fade(5.3,9.8)}",
    f"drawtext={bold(RED,56)}:text='Firme digitali non conformi':x={CX}:y=580:{show(5.9,9.8)}:{fade(5.9,9.8)}",
    f"drawtext={bold(RED,56)}:text='Dati su server stranieri':x={CX}:y=700:{show(6.5,9.8)}:{fade(6.5,9.8)}",
    f"drawtext={bold(GOLD,52)}:text='Sanzioni eIDAS fino a 50.000 euro':x={CX}:y=1820:{show(7.3,9.8)}:{fade(7.3,9.8)}",
]

# SCENA 3 — Soluzione (10–15s) — sollievo, l'AI entra in azienda
filters.append(f"drawtext={reg(WHITE,50)}:text='Con AiChain Solutions':x={CX}:y=380:{show(10.3,14.8)}:{fade(10.3,14.8)}")
filters.append(f"drawtext={bold(GOLD,54)}:text='l’AI lavora DENTRO la tua azienda':x={CX}:y=480:{show(10.7,14.8)}:{fade(10.7,14.8)}")
for ts, y, txt in [(11.3,760,">> I tuoi dati non escono mai"),(12.1,880,">> On-premise o cloud privato EU"),(12.9,1000,">> Compliance GDPR ed eIDAS 2.0")]:
    filters.append(f"drawtext={bold(GREEN,50)}:text='{txt}':x=100:y={y}:{show(ts,14.8)}:{fade(ts,14.8)}")
filters.append(f"drawtext={reg(WHITE,44)}:text='Zero rischi. Zero lock-in.':x={CX}:y=1820:{show(13.5,14.8)}:{fade(13.5,14.8)}")

# SCENA 4 — Prova sociale e numeri (15–20s)
filters += [
    f"drawtext={reg(WHITE,48)}:text='I risultati dei nostri clienti':x={CX}:y=420:{show(15.3,19.8)}:{fade(15.3,19.8)}",
    f"drawtext={bold(GOLD,58)}:text='-70% tempo ricerca documenti':x={CX}:y=560:{show(15.8,19.8)}:{fade(15.8,19.8)}",
    f"drawtext={bold(GOLD,68)}:text='ROI in 4 mesi':x={CX}:y=680:{show(16.4,19.8)}:{fade(16.4,19.8)}",
    f"drawtext={bold(GOLD,56)}:text='99.8% precisione di estrazione':x={CX}:y=800:{show(17.0,19.8)}:{fade(17.0,19.8)}",
    f"drawtext={reg(WHITE,42)}:text='Made in Italy - Catania':x={CX}:y=1820:{show(17.6,19.8)}:{fade(17.6,19.8)}",
]

# SCENA 5 — CTA (20–25s) — azione ovvia, zero rischio
filters += [
    f"drawtext={bold(GOLD,92)}:text='ANALISI AI GRATUITA':x={CX}:y=720:{show(20.3,24.9)}:{fade(20.3,24.9)}",
    f"drawtext={reg(WHITE,48)}:text='della tua infrastruttura documentale':x={CX}:y=860:{show(20.8,24.9)}:{fade(20.8,24.9)}",
    f"drawtext={reg(WHITE,44)}:text='Risposta in 24 ore - Zero impegno':x={CX}:y=960:{show(21.3,24.9)}:{fade(21.3,24.9)}",
    f"drawtext={bold(WHITE,60)}:text='Prenota ora':x={CX}:y=1120:{show(21.8,24.9)}:{fade(21.8,24.9)}",
    f"drawtext={reg(GOLD,48)}:text='aichainsolutions.net/ai-readiness':x={CX}:y=1830:{show(22.3,24.9)}:{fade(22.3,24.9)}",
]

# Costruisci filter_complex come singola stringa senza newline
fc = "[0:v]" + ",".join(filters) + "[vout]"

print(f"✅ Filter_complex: {len(filters)} elementi")

# ── Chiama ffmpeg direttamente via subprocess (nessun escaping shell) ─────────
cmd = [
    FFMPEG, "-y",
    "-i", INPUT,
    "-filter_complex", fc,          # <-- stringa passata direttamente, nessun escaping
    "-map", "[vout]",
    "-c:v", "libx264",
    "-preset", "slow",
    "-crf", "16",
    "-r", "24",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    OUTPUT_TMP
]

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("❌ ffmpeg error:")
    print(result.stderr[-2000:])  # ultimi 2000 char del log
    sys.exit(1)

print(f"✅ Video con testo: {OUTPUT_TMP}")
PYEOF

success "ffmpeg eseguito via Python subprocess (nessun escaping shell)"

# ── Aggiungi voiceover (Higgsfield TTS) + ambiente nativo Kling ──────────────
VOICEOVER="${OUTPUT_DIR}/voiceover_hf.m4a"
if [[ -f "${VOICEOVER}" ]]; then
    step "Mix voiceover + audio ambientale"
    # Ambiente nativo (traccia del raw) al 25% + voiceover ritardato di 0.8s
    ffmpeg -y \
        -i "${VIDEO_TMP}" \
        -i "${INPUT}" \
        -i "${VOICEOVER}" \
        -filter_complex "[1:a]volume=0.25[amb];[2:a]adelay=800|800[vo];[amb][vo]amix=inputs=2:duration=first:normalize=0[aout]" \
        -map 0:v -map "[aout]" \
        -c:v copy -c:a aac -b:a 192k \
        -movflags +faststart \
        "${FINAL}" 2>&1 | tail -2
    rm "${VIDEO_TMP}"
else
    mv "${VIDEO_TMP}" "${FINAL}"
fi

# ── Riepilogo ─────────────────────────────────────────────────────────────────
FILESIZE=$(du -h "${FINAL}" | cut -f1)
echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN}  ✅  VIDEO CON TESTO PRONTO${RESET}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${RESET}"
echo -e "  📁  ${FINAL}"
echo -e "  💾  ${FILESIZE}  •  1080×1920  •  MP4 H.264"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${RESET}"
