---
name: cloudflare-email-sending-ops
description: Use when onboarding or debugging Cloudflare Email Sending.
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [cloudflare, email, sending, dkim, spf, dmarc, transactional]
    related_skills: [email-domain-authentication, cloudflare-cli-mcp-setup, resend-inbound-email-webhook]
---

# Cloudflare Email Sending — onboard domain tanpa merusak email yang sudah jalan

Cloudflare punya fitur **Email Sending** (beta, butuh Workers Paid): kirim email
transaksional lewat Workers binding / REST API / SMTP. Terbukti jalan 10-Okt-2026
(sayasuka99.com, SPF+DKIM pass, masuk inbox).

## When to Use

- Bang minta "bisa kirim email pakai Cloudflare ga?" / kirim link docs email-service.
- Mau domain dengan kuota kirim lebih murah/gratis dari Resend/AgentMail.
- Perlu debug SPF/DKIM/bounce domain Email Sending di CF.

## 🔴 PITFALL TERBESAR: `dns fix` CF MENIMPA DMARC jadi `p=reject`

Setelah `email-sending subdomains create`, CF **menyarankan** record DNS termasuk:
```
_dmarc.<domain>  →  "v=DMARC1; p=reject;"      ← ⚠️⚠️ BAHAYA
```
Dua kerusakan sekaligus:
1. **`rua` HILANG** → laporan DMARC berhenti → cron `dmarc-alert` mati (tidak ada alert palsu).
2. **`p=reject`** memaksa tolak semua email yang gagal SPF/DKIM. Domain lama
   (puluhan subdomain, banyak layanan kirim) hampir pasti punya pengirim sah yang
   belum terdaftar SPF → email sah mereka **hilang**.

**JANGAN jalankan `cf email-sending subdomains dns fix`.** Tambah record sendiri,
kecuali `_dmarc` — biarkan apa adanya.

## Alur yang terbukti (read-only dulu → tambah record sendiri)

```bash
ZID=<zone-id>
# 1) cari zona (PAGINATION! `cf zones list` cuma 20/halaman — domain bisa di hal 3+)
cf zones list --page 1|2|3

# 2) lihat record yang DIMINTA CF (belum diterapkan)
cf email-sending subdomains create -z $ZID --name <domain> --dry-run

# 3) onboard
cf email-sending subdomains create -z $ZID --name <domain>
#    → id, return_path_domain=cf-bounce.<domain>, dkim_selector=cf-bounce

# 4) lihat record yang dibutuhkan
cf email-sending subdomains dns get <subdomain-id> -z $ZID

# 5) TAMBAH SENDIRI (script: /root/cf_sending_dns.py) — semua KECUALI _dmarc
#    MX cf-bounce ×3 | TXT cf-bounce (SPF) | TXT cf-bounce._domainkey (DKIM)

# 6) verifikasi DNS live + kirim test
cf email-sending limits get                    # quota (contoh: 1000/hari)
cf email-sending send --body '{"to":"...","from":"test@domain","subject":"...","text":"..."}'
```

Record yang CF tambahkan sendiri: **MX `cf-bounce`** sering sudah ada otomatis,
jadi script harus **deteksi yang sudah ada** (jangan bikin duplikat).

## Bukti sukses (yang harus dicek, bukan diasumsikan)

Response send:
```json
{"message_id":"<...@domain>", "delivered":["tujuan@x"], "permanent_bounces":[]}
```
Lalu cek **header email yang diterima** (bukan cuma status API):
```
spf=pass (domain of cf-bounce.<domain> designates <ip> as permitted sender)
dkim-signature: s=cf-bounce  d=<domain>
return-path: bounces@cf-bounce.<domain>
```
SPF-nya memakai **envelope domain `cf-bounce.<domain>`**, bukan domain utama — itu normal.

## Kuota & harga

| Plan | Kirim | Terima |
|---|---|---|
| Workers Free | ❌ tidak bisa | unlimited |
| Workers Paid | **3.000/bulan** lalu $0.35/1.000 | unlimited |

Kirim ke **verified destination address** = gratis, tidak masuk kuota.
Batas lain: 50 penerima/email, 5 MiB (25 MiB ke verified address), header 16 KB.

## SMTP / REST untuk aplikasi non-Worker

```
REST : POST https://api.cloudflare.com/client/v4/accounts/{id}/email/sending/send
       (permission: Email Sending: Edit)
SMTP : smtps://smtp.mx.cloudflare.net:465  → user = "api_token", pass = token
```

## Pelajaran umum

- **`p=reject` bukan "lebih aman" secara default** — ia menghapus email sah dari
  pengirim yang belum terdaftar SPF. Untuk domain lama & ramai, mulai `p=none` →
  baca laporan → baru naikkan.
- **Vendor "auto-fix DNS" sering menghapus laporan (rua/ruf) yang kita butuh.**
  Bandingkan record yang diminta vendor dengan yang kita punya sebelum menerapkan.
- **`cf zones list` ber-paginasi 20** — jangan simpulkan domain tidak ada dari halaman 1.
