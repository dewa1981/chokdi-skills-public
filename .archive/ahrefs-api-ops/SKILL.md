---
name: ahrefs-api-ops
description: Use when pasang/pakai Ahrefs API v3 (key, endpoint, skrip).
version: 1.0.0
author: chokdi_staging
license: proprietary
metadata:
  hermes:
    tags: [ahrefs, seo, api, keyword, backlink, integration]
    related_skills: [openseo-mcp-ops, keyword-research, competitive-landscape, hermes-bot-telegram-allowlists]
---

# Ahrefs API v3 — integrasi data SEO (proven 2026-08-29)

Sumber data SEO (domain rating, keyword volume, backlinks, top pages) buat riset/artikel. Key plan Lite Bang: `AHREFS_API_KEY` — jangan pernah tampilkan nilai key di chat/log (kalau perlu bukti, tampilkan panjang chars saja).

## When to Use
- Bang minta pasang Ahrefs API ke server/bot Hermes baru (key + skrip helper)
- Riset SEO butuh data Ahrefs: DR domain, keyword volume, backlinks, top pages, refdomains
- Cek kenapa skrip Ahrefs gagal / key ga kebaca (path .env beda per unit)

## Aturan penting
- **MCP Ahrefs TIDAK boleh dipakai client custom** (Hermes): docs tegas melarang bridge/custom client → risiko banned. Integrasi sah = **API v3** langsung (`https://api.ahrefs.com/v3`, auth `Authorization: Bearer <key>`).
- Units: min 50/call, plan Lite 100k units/bln, rate 60 req/mnt. Jangan over-query (cek local dulu, baru external).

## Lokasi key (per unit, path beda-beda!)
- Staging: `/root/.hermes/.env` (format plain `KEY=val`)
- Bot Hermes di Docker (tukang_banner1, server 144): `/opt/docker/hermes/<bot>/.env` → di container = `/opt/data/.env`
- Cek tanpa bocor: `grep -c '^AHREFS_API_KEY=.' <env>` → 1; panjang cocok: `grep '^AHREFS_API_KEY=' <env> | cut -d= -f2 | wc -c` → 41 (40 chars + newline)

## Pasang key ke bot Hermes baru (verified workflow)
```bash
# 1. Ambil key dari sumber (jangan print)
KEY=$(grep '^AHREFS_API_KEY=' /root/.hermes/.env | head -1 | cut -d= -f2-)
# 2. Backup .env bot lalu inject
ssh <server> "cp <bot>/.env <bot>/.env.bak-ahrefs-\$(date +%Y%m%d-%H%M%S) && printf '\n# Ahrefs API v3\nAHREFS_API_KEY=%s\n' '$KEY' >> <bot>/.env"
# 3. Verify: grep -c '^AHREFS_API_KEY=.' → 1, panjang value = 41
# 4. Restart container biar env kebaca di gateway process (skrip baca-file sih jalan tanpa restart)
```

## Skrip helper — pattern env-first + fallback baca file (JALAN TANPA RESTART)
Trik kunci: skrip baca key dari env var dulu, fallback `grep` dari file `.env` langsung → bekerja bahkan sebelum gateway direstart (env var baru belum di-load dotenv). Adaptasi path `.env` per unit (jangan hardcode path staging!).
```bash
KEY="${AHREFS_API_KEY:-}"
[ -z "$KEY" ] && KEY=$(grep -oE '^AHREFS_API_KEY=.*' /opt/data/.env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
[ -z "$KEY" ] && echo "ERROR: AHREFS_API_KEY tidak ada" && exit 1
q() { curl -s --max-time 30 -H "Authorization: Bearer $KEY" "https://api.ahrefs.com/v3$1"; }
```
Lokasi skrip: staging `/root/scripts-lp/ahrefs.sh`, bot 144 `/opt/data/scripts-lp/ahrefs.sh` (chown 1000:1000 biar kebaca user container). 11 perintah: `dr|metrics|bl|top|org|ref` (site-explorer) + `kv|ko|match|related|suggest` (keywords-explorer, country default `id`).

## Endpoint verified (path beda dari v2 — v2 TIDAK punya /overview)
- `GET /site-explorer/domain-rating?target=<domain>&date=<YYYY-MM-DD>` → `{domain_rating: {domain_rating, ahrefs_rank}}` (contoh: amanbos99.com = 6.0)
- `GET /site-explorer/metrics|backlinks-stats|top-pages|organic-keywords|refdomains?target=...&date=...`
- `GET /keywords-explorer/volume-by-country?keyword=...&country=id` (volume 'slot online' id = 42.000/bln)
- `GET /keywords-explorer/overview?keywords=...&country=id&select=keyword,volume,difficulty`
- Path valid lengkap: `docs.ahrefs.com/openapi.json` (jangan tebak dari v2)

## Limits, usage & monitoring (verified live 2026-08-29)
- **Endpoint GRATIS (0 units!)**: `GET /subscription-info/limits-and-usage` → `{limits_and_usage: {subscription, usage_reset_date, units_limit_workspace, units_usage_workspace, units_limit_api_key, units_usage_api_key, api_key_expiration_date}}`. Ini satu-satunya cara cek limit/usage real-time TANPA makan units — WAJIB dipakai buat monitoring, jangan ngetes lewat query data.
- Plan Bang: **Lite 2022** → `units_limit_workspace = 100000`/bln, reset tiap **tanggal 13**, key expire 1 tahun. `units_limit_api_key: null` = key belum di-set limit pribadi (di UI Ahrefs tampil "No limit").
- Aturan biaya (docs resmi): min **50 units/call**, cost = rows × fields, max **100 rows/request** di Lite. Units **non-refundable** & **shared 1 pot** (API v3 + MCP + Connect). Contoh: 1 call 100 rows × 6 fields ≈ 600 units → 100K units cuma cukup ~166 call gede.
- Rate limit: **60 req/mnt** default → HTTP **429** kalau lebih; 429 juga bisa muncul dari throttling dinamis (bukan cuma rate).
- Kalau kena limit: 429 → tunggu ±1 mnt lalu lanjut; units habis → tunggu reset tgl 13 / upgrade plan (Standard 400K) / hemat (field dikit, rows kecil, cache hasil riset, jangan query keyword sama berulang).

## Monitor usage → notif Telegram (proven, cron 6 jam di server 144)
Skrip: `/opt/docker/hermes/tukang_banner1_bot/scripts-lp/ahrefs_monitor.sh` (jalan di HOST 144, crontab root `0 17,23,5,11 * * *` = 00/06/12/18 WIB). Logic yang terbukti:
- Cek endpoint gratis → `PCT = units_usage*100/units_limit`
- State file `.ahrefs_monitor_state` = LEVEL notif terakhir (80/90/95/99). Notif SEKALI per kenaikan level; state di-reset kalau usage TURUN (siklus baru tgl 13) biar bisa notif lagi di siklus berikutnya. Ini anti-spam.
- Kirim pakai token bot yang MEMBER di grup tujuan (baca dari .env bot itu). CEK DULU akses: `curl https://api.telegram.org/bot<TOKEN>/getChat?chat_id=<grup>` → 400 "chat not found" = bot BUKAN member → pilih bot lain (staging ga bisa kirim ke MKT_Diamond99; bot tukang_banner1 bisa karena home channel-nya di situ).
- Log + state di folder scripts-lp (masuk volume /opt/data → ikut backup server 144 tiap 06:00).

## Verify env var di container (pitfall penting)
`docker exec <c> env | grep KEY` dari shell baru = TIDAK nampilin var yang di-load dotenv (shell baru mewarisi env proses LAHIR, bukan dotenv runtime). `/proc/<pid>/environ` juga snapshot saat proses lahir → hasil `count: 0` itu NORMAL, bukan berarti key ga kebaca. Verify yang bener (simulasi mekanisme load Hermes):
```bash
docker exec <container> python3 -c "from dotenv import load_dotenv; import os; load_dotenv('/opt/data/.env'); print(bool(os.environ.get('AHREFS_API_KEY')))"  # → True = key kebaca gateway saat runtime
```

## Test cepat setelah pasang (tanpa print key)
```bash
docker exec <container> bash /opt/data/scripts-lp/ahrefs.sh dr amanbos99.com
# → { "domain_rating": { "domain_rating": 6.0, ... } }  = key valid, API jalan dari unit tsb
```
