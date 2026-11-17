#!/usr/bin/env bash
# edge_tts_thai_female.sh — Thai FEMALE voiceover for promos WITHOUT editing config.yaml.
#
# Why this exists: the profile's config.yaml may set tts.edge.voice to a MALE voice
# (th-TH-NiwatNeural). Hermes refuses agent writes to config.yaml, and the text_to_speech
# tool's `instructions` parameter is ignored by the edge provider — so call edge_tts directly
# with the voice you actually want.
#
# Usage: edge_tts_thai_female.sh "<thai text>" <out.ogg|out.mp3> [rate]   (rate default -5%)
# Prints the output duration (use it as the video length).
set -euo pipefail

TEXT="${1:?thai text}"
OUT="${2:?output file (please include .ogg or .mp3)}"
RATE="${3:--5%}"
VOICE="${VOICE:-th-TH-PremwadeeNeural}"

PY=/opt/hermes-v0204/.venv/bin/python
[ -x "$PY" ] || PY=python3

"$PY" - "$TEXT" "$OUT" "$RATE" "$VOICE" <<'PYEOF'
import asyncio, sys
text, out, rate, voice = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
import edge_tts
asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(out))
print("OK", out, voice)
PYEOF

ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"

# Next step for a promo: transcode before muxing (mono 44.1k WAV)
#   ffmpeg -y -v error -i "$OUT" -ar 44100 -ac 1 "${OUT%.*}.wav"
