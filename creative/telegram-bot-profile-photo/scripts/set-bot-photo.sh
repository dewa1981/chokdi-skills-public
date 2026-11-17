#!/usr/bin/env bash
# set-bot-photo.sh — set foto profil bot Telegram dari file gambar
#
# Pakai:
#   ./set-bot-photo.sh <bot-token> <file-gambar>
#
# Contoh:
#   ./set-bot-photo.sh 123456:AAHxxxx gambar.png
#
# File PNG otomatis dikonversi ke JPG (Telegram static profile photo WAJIB JPG).
set -euo pipefail

TOKEN="${1:-}"
IMG="${2:-}"

if [ -z "$TOKEN" ] || [ -z "$IMG" ]; then
    echo "Usage: $0 <bot-token> <file-gambar>"
    exit 1
fi
[ -f "$IMG" ] || { echo "GAGAL: file tidak ada: $IMG"; exit 1; }

# --- pastikan JPG ---
EXT="${IMG##*.}"
if [ "${EXT,,}" != "jpg" ] && [ "${EXT,,}" != "jpeg" ]; then
    JPG="${IMG%.*}.jpg"
    echo "==> konversi ke JPG: $JPG"
    python3 - "$IMG" "$JPG" <<'PYEOF'
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
im.save(dst, "JPEG", quality=92)
print(f"    {im.size} -> {dst}")
PYEOF
else
    JPG="$IMG"
fi

echo "==> set foto profil bot"
RESP=$(curl -s -m 60 -X POST "https://api.telegram.org/bot${TOKEN}/setMyProfilePhoto" \
  -F 'photo={"type":"static","photo":"attach://file0"};type=application/json' \
  -F "file0=@${JPG};type=image/jpeg")

echo "$RESP"
if echo "$RESP" | grep -q '"ok":true'; then
    echo "BERHASIL ✅"
else
    echo "GAGAL ❌ — cek: file JPG? token benar? (pesan 'photo isn't specified' = payload/format salah)"
    exit 1
fi
