#!/usr/bin/env bash
# build_promo_video.sh — product photo → vertical 9:16 promo video (Thai text) + voiceover mux.
# Usage: build_promo_video.sh <product_image> <voice.wav> <out.mp4> ["<caption_line1>" ...]
# Requires: ffmpeg, /opt/data/fonts/NotoSansThai.ttf
# Implements steps 5-8 of the product-photo-promo-video skill.
set -euo pipefail

IMG="${1:?product image}"
VO="${2:?voice wav}"
OUT="${3:?output mp4}"
shift 3 || true

FONT=/opt/data/fonts/NotoSansThai.ttf
[ -f "$FONT" ] || { echo "FONT MISSING: $FONT"; exit 1; }

W=1080; H=1920; FPS=30
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VO" | cut -d. -f1)
DUR=${DUR:-15}; FRAMES=$((DUR * FPS))

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# 5) compose one still: blurred bg + product fg centered
ffmpeg -y -v error -i "$IMG" -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=25:3" -frames:v 1 "$TMP/bg.png"
ffmpeg -y -v error -i "$IMG" -vf "scale=900:-1" "$TMP/fg.png"
ffmpeg -y -v error -i "$TMP/bg.png" -i "$TMP/fg.png" -filter_complex "[1:v]scale=900:-1[fg];[0:v][fg]overlay=(W-w)/2:(H-h)/2" -frames:v 1 "$TMP/composed.png"

# 6) ken-burns zoom (no alpha: composed.png is plain RGB)
ffmpeg -y -v error -loop 1 -i "$TMP/composed.png" -vf "zoompan=z='min(zoom+0.0006,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${FRAMES}:s=${W}x${H}:fps=${FPS},format=yuv420p" -frames:v "$FRAMES" -c:v libx264 "$TMP/video.mp4"

# 7) drawtext: title line first arg after IMG/VO/OUT; extra lines appended as more drawtext filters.
# Example with Thai title + yellow price line:
#  drawtext=...title...:y=h*0.03, drawtext=...price...:fontcolor=yellow:y=h*0.03+85
# Build filter dynamically from remaining args (all white; tweak color per line as needed).
VF=""
Y=0.03
for LINE in "$@"; do
  VF+="drawtext=fontfile=${FONT}:text='${LINE}':fontsize=48:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*${Y},"
  Y=$(echo "$Y + 0.07" | bc)
done
VF=${VF%,}

ffmpeg -y -v error -i "$TMP/video.mp4" -vf "$VF" -c:v libx264 -pix_fmt yuv420p "$TMP/video_txt.mp4"

# 8) mux voice
ffmpeg -y -v error -i "$TMP/video_txt.mp4" -i "$VO" -c:v copy -c:a aac -b:a 192k -shortest "$OUT"

echo "OK $OUT"
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
