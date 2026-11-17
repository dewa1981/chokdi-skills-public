#!/bin/bash
# Template: monitor resi kurir, notif HANYA kalau status berubah.
# Ganti AWB / URL / ekstraksi sesuai kurir.
# Pasang: cp ke /root/.hermes/scripts/ (SYMLINK DITOLAK cronjob tool), lalu
#   cronjob action=create no_agent=true deliver=local schedule="every 4h"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"
export TZ="Asia/Jakarta"

AWB="MY3737177280"
STATE_FILE="/opt/data/scripts/.resi_track_state"
LOG="/opt/data/scripts/resi_track.log"
URL="https://gdexpress.com/tracking/?consignmentno=${AWB}"

TOK=$(cat /root/scripts/.tg_bayar_token 2>/dev/null | tr -d '\r\n')
TG_CHAT="-1004350623808"

ts() { date '+%F %T'; }

BODY=$(curl -s -4 -L --max-time 25 \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" \
  "$URL" 2>/dev/null)

# gagal fetch -> diam (jangan tulis state, jangan notif error palsu)
if [ -z "$BODY" ]; then
  echo "$(ts) GAGAL: tidak ada respons" >> "$LOG"
  exit 0
fi

STATUS=$(printf '%s' "$BODY" \
  | sed 's/<[^>]*>/ /g' | tr -s ' \t\n' ' ' \
  | grep -oE 'Consignment Number:.*?(Frequently Asked Questions|About Us)' | head -1 \
  | sed 's/Frequently Asked Questions.*//; s/About Us.*//' \
  | sed 's/^ *//; s/ *$//' | cut -c1-600)

[ -z "$STATUS" ] && STATUS="(status tidak terbaca)"

PREV=""
[ -f "$STATE_FILE" ] && PREV=$(cat "$STATE_FILE" 2>/dev/null)
echo "$(ts) | status='$STATUS' | prev='$PREV'" >> "$LOG"

[ "$STATUS" = "$PREV" ] && { echo "$(ts) sama — tidak kirim notif" >> "$LOG"; exit 0; }
printf '%s' "$STATUS" > "$STATE_FILE"

MSG=$(printf '📦 *UPDATE RESI*

`%s`

%s

_%s WIB_' "$AWB" "$STATUS" "$(date '+%d %b %Y %H:%M')")

if [ -n "$TOK" ]; then
  RES=$(curl -s --max-time 15 -X POST "https://api.telegram.org/bot${TOK}/sendMessage" \
    -d "chat_id=${TG_CHAT}" --data-urlencode "text=${MSG}" -d "parse_mode=Markdown" 2>/dev/null)
  echo "$(ts) notif terkirim: $(printf '%s' "$RES" | grep -oE '"ok":(true|false)') " >> "$LOG"
else
  echo "$(ts) GAGAL: token tidak ada" >> "$LOG"
fi
