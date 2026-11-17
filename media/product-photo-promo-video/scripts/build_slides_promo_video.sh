#!/usr/bin/env bash
# build_slides_promo_video.sh — 2-4 still images → vertical 9:16 slideshow promo
# with Thai captions + voiceover muxed in.
#
# Usage:
#   build_slides_promo_video.sh <voice.wav> <out.mp4> <img1> <img2> [img3] [img4]
#   TOP1="คอลลาเจน Vene Vicenza" TOP2="ALL IN ONE F.I.R." \
#   BOT1="กล่องใหญ่ 12 ซอง เพียง 490฿" BOT2="ซื้อ 2 กล่อง แถมฟรี กล่องเล็ก 6 ซอง" \
#   build_slides_promo_video.sh vo.wav out.mp4 a.png b.png c.png
#
# Requires: ffmpeg + /opt/data/fonts/NotoSansThai.ttf
# Notes: captions are drawtext'd inside text='...' — do NOT put an apostrophe in a caption.
#        Fractional timing is computed with awk (bash arithmetic cannot do floats).
set -euo pipefail

VO="${1:?voice wav}"; OUT="${2:?out mp4}"; shift 2
IMGS=("$@")
N=${#IMGS[@]}
[ "$N" -ge 2 ] || { echo "need >= 2 images"; exit 1; }
[ "$N" -le 4 ] || { echo "max 4 images"; exit 1; }

FONT=${FONT:-/opt/data/fonts/NotoSansThai.ttf}
[ -f "$FONT" ] || { echo "FONT MISSING: $FONT"; exit 1; }
W=1080; H=1920; FPS=30

DUR=$(python3 -c "
import subprocess
print(round(float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1','$VO']).strip())+0.2, 2))")
SEG=$(python3 -c "print(round($DUR/$N, 3))")
SEGFR=$(( $(python3 -c "import math;print(math.ceil($SEG*$FPS))" ) ))

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# 1) compose each still onto a blurred vertical background
for i in "${!IMGS[@]}"; do
  ffmpeg -y -v error -i "${IMGS[$i]}" -vf "scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},boxblur=25:3" -frames:v 1 "$TMP/bg$i.png"
  ffmpeg -y -v error -i "${IMGS[$i]}" -vf "scale=920:-1" "$TMP/fg$i.png"
  ffmpeg -y -v error -i "$TMP/bg$i.png" -i "$TMP/fg$i.png" \
    -filter_complex "[1:v]scale=920:-1[fg];[0:v][fg]overlay=(W-w)/2:(H-h)/2" -frames:v 1 "$TMP/slide$i.png"
  IN+=(-loop 1 -t "$(python3 -c "print(round($SEG+1, 2))")" -i "$TMP/slide$i.png")
done

# 2) filtergraph: per-image ken-burns zoom -> xfade chain -> captions
FC=""
for i in "${!IMGS[@]}"; do
  FC+="[$i:v]zoompan=z='min(1+0.0007*on,1.08)':d=${SEGFR}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},setsar=1[v$i];"
done
PREV="v0"
for ((i=1; i<N; i++)); do
  OFF=$(awk -v s="$SEG" -v i="$i" 'BEGIN{printf "%.3f", i*s-0.5}')
  FC+="[${PREV}][v$i]xfade=transition=fade:duration=0.5:offset=${OFF}[x$i];"
  PREV="x$i"
done
FC+="[${PREV}]"

build_dt () { # $1=text $2=size $3=color $4=y
  [ -n "$1" ] || return 0
  FC+="drawtext=fontfile=${FONT}:text='$1':fontsize=$2:fontcolor=$3:borderw=4:bordercolor=black@0.85:x=(w-text_w)/2:y=$4,"
}
build_dt "${TOP1:-}" 58 white        "h*0.03"
build_dt "${TOP2:-}" 42 "#FFE066"   "h*0.03+80"
build_dt "${BOT1:-}" 48 white        "h*0.80"
build_dt "${BOT2:-}" 42 "#FFE066"   "h*0.80+70"
FC+="format=yuv420p[out]"

ffmpeg -y -v error "${IN[@]}" -filter_complex "$FC" -map "[out]" -t "$DUR" \
  -r "$FPS" -c:v libx264 -preset medium -crf 20 "$TMP/slides.mp4"

# 3) mux the voiceover
ffmpeg -y -v error -i "$TMP/slides.mp4" -i "$VO" -c:v copy -c:a aac -b:a 192k -shortest "$OUT"

echo "OK $OUT"
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height -of default=noprint_wrappers=1 "$OUT"
