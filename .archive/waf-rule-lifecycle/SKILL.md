---
name: waf-rule-lifecycle
description: "Use when WAF rules go missing, drift, or need restore."
version: 1.0.0
author: chokdi_staging
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [waf, cloudflare, firewall, backup, restore, drift-detection]
    category: devops
---

# WAF Rule Lifecycle (Cloudflare)

Siklus hidup rule WAF: **backup -> deteksi drift -> restore**. Rule WAF tidak punya
version history di UI dan tidak ikut backup default CF — kalau hilang, hilang tanpa
jejak. Skill ini menutup celah itu.

Untuk token, expression syntax, dan audit log dasar lihat skill
`cloudflare-api-ops`. Skill ini fokus ke **apa yang dilakukan sesudah rule sudah/akan
hilang**.

## 1. Backup semua zone ke R2 (harian)

Yang di-dump per zone: seluruh phase ruleset (`http_request_firewall_custom`,
`http_ratelimit`, `http_request_firewall_managed`) + `firewall/access_rules/rules`
+ security settings (`security_level`, `ssl`, `min_tls_version`, dll).
Struktur di bucket:
```
<bucket>/waf/<zone>_<YYYY-MM-DD>.json
<bucket>/dns/<zone>_<YYYY-MM-DD>.json     # DNS ikut, murah & berguna
<bucket>/index/<YYYY-MM-DD>.json          # ringkasan harian
<bucket>/latest/index.json                 # selalu versi terakhir
```
Upload via `rclone copyto <file> <remote>:<bucket>/<path>` — remote s3 sudah ada
untuk R2. Jadwalkan **sebelum** backup full server (mis. 01:00 vs backup mesin 06:00)
biar versi teks tersedia lebih dulu. Retensi 30 hari: baca listing `rclone lsf`,
hapus yang tanggalnya lebih tua dari cutoff.

Jalankan sebagai script Python (stdlib + rclone), wrapper `.sh` untuk cron dengan
PATH absolut dan rotasi log.

## 2. Restore rule yang hilang

### Sumber data: version history per phase
```bash
GET /zones/{ZONE}/rulesets/phases/{PHASE}/entrypoint/versions?per_page=20
GET /zones/{ZONE}/rulesets/phases/{PHASE}/entrypoint/versions/{N}   # isi lengkap
```
Endpoint list versi mengembalikan `rules[]` **kosong** — hitung jumlah rule dari
`versions/{N}`, jangan dari listnya. Mundur dari versi sekarang sampai ketemu
jumlah rule terbanyak: dua versi berurutan yang lompat jumlahnya = **jendela waktu
rule hilang**.

### MERGE, jangan replace
Versi lama TIDAK memuat rule yang dibuat **setelah** versi itu. Kalau di-PUT apa
adanya, rule baru ikut terhapus. Algoritma:
```python
now_keys = {(r.get("description") or r.get("expression") or "")[:80] for r in rules_sekarang}
final = rules_sekarang[:]                      # rule sekarang di DEPAN (prioritas tetap)
for r in rules_lama:
    k = (r.get("description") or r.get("expression") or "")[:80]
    if k not in now_keys:
        final.append({kk: vv for kk, vv in r.items()
                      if kk in ("action", "expression", "description", "enabled",
                                "action_parameters", "ratelimit", "logging")})
```
Key unik = `description` (fallback `expression`). Buang `id`/`version`/`last_updated`
dari rule lama.

### Urutan eksekusi yang aman
1. **Snapshot dulu**: simpan `rules_sekarang` ke file lokal + upload ke R2 sebagai
   `restore/<zone>_before-restore_<ts>.json`. Ini jalur rollback.
2. PUT ke `.../phases/{PHASE}/entrypoint` (bukan `rulesets/{id}`).
3. **GET balik dan HITUNG.** `success:true` bukan bukti — sukses = jumlah rule hasil
   GET == target. Kalau beda, restore snapshot dan lapor gagal.
4. Baru kirim notif.

## 3. Drift detection (jangan tunggu berbulan-bulan)

Backup harian saja tidak cukup — kerusakan baru ketahuan kalau ada yang sadar.
Monitor membandingkan **jumlah rule per zone** antar-run:
- Tiap run: snapshot `{zone: {custom, ratelimit, managed, ip_access, total}}` ke state JSON.
- Bandingkan dengan run sebelumnya. Turun -> alert. Naik setelah turun -> notif pulih.
- Tidak ada perubahan -> **diam** (anti-spam).

**Jangan asal hapus state file untuk "reset"** — itu menghapus baseline sehingga
semua zone tampak "baru" dan tidak ada pembanding. Kalau perlu reset, tulis ulang
state dari GET saat itu juga.

Cara menguji monitor tanpa merusak apa pun: edit state JSON supaya `total` suatu zone
lebih TINGGI dari kenyataan, jalankan monitor, pastikan alert terkirim, lalu tulis
ulang state dari kenyataan. (Menyetel state lebih RENDAH justru terbaca sebagai
"pulih", bukan "turun".)

## 4. Kirim notif dari script cron

**Discord via `urllib` GAGAL** (HTTP 403, body `error code: 1010`) — CF di depan
Discord memblokir client non-browser. **Pakai `curl`:**
```bash
curl -s -o /dev/null -w '%{http_code}' -X POST \
  -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"pesan"}' \
  "https://discord.com/api/v10/channels/$CHANNEL_ID/messages"
```
Sukses = HTTP `200`. Kirim `content` polos (bukan embed) — lebih sedikit yang gagal.

Cari channel ID dari nama channel:
```bash
curl -s -H "Authorization: Bot $TOK" https://discord.com/api/v10/users/@me/guilds
curl -s -H "Authorization: Bot $TOK" https://discord.com/api/v10/guilds/$GUILD_ID/channels
```

Telegram: `POST https://api.telegram.org/bot$TOKEN/sendMessage` (`chat_id`, `text`,
`parse_mode: HTML`) — juga lewat `curl`, cek HTTP 200.

## 5. Kalau rule hilang tanpa sebab

Cek audit log untuk `action.type = rulesets_update`. Kalau `actor.type = token`
(bukan email manusia), berarti **script/API key** yang melakukannya, bukan orang
lewat dashboard — telusuri script mana yang memegang token itu.

Jebakan klasik: script yang seharusnya `GET` tapi memakai `method` dari variabel,
atau salah mengarahkan PUT ke `entrypoint` — karena **PUT menimpa SELURUH daftar
rule**, satu salah-panggil menghapus semua rule di phase itu dan menyisakan hanya
yang dikirim.

## Checklist

- [ ] Backup WAF+DNS semua zone ke R2, harian, retensi 30 hari
- [ ] Monitor drift tiap beberapa jam, alert hanya saat transisi
- [ ] Restore: MERGE (bukan replace), snapshot sebelum PUT, GET balik untuk verifikasi
- [ ] Notif lewat `curl` (bukan urllib) untuk Discord
- [ ] Audit log dicek kalau ada perubahan tak terduga (`actor.type = token`)
