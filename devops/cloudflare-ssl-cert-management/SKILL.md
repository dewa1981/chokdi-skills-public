---
name: cloudflare-ssl-cert-management
description: "Use when ordering/fixing Cloudflare SSL certs (DCV stuck)."
---

# Cloudflare SSL Certificate Management (cert packs + DCV + TXT)

Order, fix, dan monitor sertifikat di Cloudflare (advanced cert wildcard, Total TLS, universal backup) via API. TERBUKTI 2026-08-07: wildcard *.sayasuka99.com stuck "Initializing" BERHARI-HARI → active dalam 30 menit setelah root cause ditemukan (190 TXT sampah!).

## Kapan dipakai

- Cert wildcard/advanced stuck "Initializing" / "Timed Out Initializing"
- User minta CA Google Trust Services (GTS) untuk cert
- Perlu order/verify cert pack via Cloudflare API

## API dasar (token requirements!)

- Token butuh izin **Zone → SSL and Certificates → Edit** (token tunnel/zone-DNS/Workers TIDAK cukup — semua gagal 401/9109!)
- Token DNS terpisah (Zone → DNS → Edit) untuk tambah/hapus TXT records
- Zone ID dari `/zones?name=domain.com`
- Endpoints:
  - `GET /zones/{zid}/ssl/certificate_packs?status=all` — list semua cert
  - `GET /zones/{zid}/ssl/certificate_packs/{id}` — detail + validation_records
  - `POST /zones/{zid}/ssl/certificate_packs` — order advanced
  - `DELETE /zones/{zid}/ssl/certificate_packs/{id}` — hapus
  - `POST /zones/{zid}/dns_records` / `DELETE .../dns_records/{id}` — TXT records

## ROOT CAUSE #1: cert stuck "Initializing" = _acme-challenge TXT SAMPAH!

Gejala: advanced wildcard cert status `initializing` berhari-hari, validation_records KOSONG (0!), order baru error `1414: must complete DCV`.

Akar masalah: **ratusan TXT records menumpuk di `_acme-challenge.<domain>`** (bertahun-tahun order cert tanpa cleanup — kasus nyata: 190 records!). CA (Google Trust) bingung → DCV tidak pernah selesai → stuck initializing.

FIX (terbukti!):
1. List semua TXT: `GET /zones/{zid}/dns_records?type=TXT&name=_acme-challenge.<domain>&per_page=200` (loop page!)
2. DELETE SEMUA (wildcard TXT lama aman dihapus — cert wildcard lama sudah tidak aktif)
3. Order ulang advanced cert (validation txt + CA google) — kalau masih `1414`, TUNGGU 5-10 menit (DCV state cooldown) ATAU order via dashboard (UI handle state)
4. CF generate validation_records (2 TXT untuk wildcard+apex) → tambahkan ke DNS (token DNS!)
5. Verifikasi propagate (dns.google/resolve?name=_acme-challenge.<domain>&type=TXT) → CF auto-verify → ACTIVE (30 menit total!)

## Order advanced wildcard (CA Google Trust Services!)

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZID/ssl/certificate_packs" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"advanced","hosts":["*.domain.com","domain.com"],"validation_method":"txt","certificate_authority":"google","cloudflare_branding":false}'
```

- **JANGAN sertakan `validity_days`** untuk advanced cert → error `1424: Validity can only be specified for dedicated certificates` (default 90 hari!)
- CA: `google` (GTS!) / `lets_encrypt` / `digicert` — wildcard butuh advanced cert (bukan universal!)
- Setelah TXT di-add + propagate → cert ACTIVE otomatis (2 cert: ECDSA + RSA — "Managed by Cloudflare" auto-renewal 3 bulan)

## Pitfalls

- Error `1414 must complete DCV on the Dedicated Certificate` — DCV state di-hold (setelah delete cert!) — API tidak bisa paksa; order via DASHBOARD (UI reset state) atau tunggu cooldown
- **Token SSL ≠ token DNS** — satu token tidak cukup; punya 2 (SSL edit + DNS edit) atau token super (Zone → Edit semua)
- `DELETE /zones/{zid}/ssl/certificate_packs/{id}` → `1408: ID is not a dedicated or advanced certificate` kalau ID itu universal — universal cert tidak bisa di-verify/delete via API
- Universal SSL cert (`backup_issued`) = "cert Backup CF" — JANGAN hapus (backup!)
- Total TLS certs (per-subdomain, `total_tls`) ter-order otomatis — semua ACTIVE terpisah dari wildcard
- Wildcard `*.domain.com` cover SEMUA subdomain 1 level + apex — subdomain baru langsung aman (tidak perlu order per-subdomain)
- UI dashboard cache: setelah delete via API, dashboard masih tampil "Initializing" beberapa menit — cek via API (bukan UI) untuk status sebenarnya
- Waktu response cert: setelah TXT propagate, tunggu 2-5 menit sebelum cek status (polling 3x dengan jeda)

## Verifikasi

- `GET /zones/{zid}/ssl/certificate_packs?status=all` → wildcard `active` + CA google
- Dashboard Edge Certificates → badge hijau ACTIVE + expiration 3 bulan
- `curl -sv https://<subdomain>.domain.com` → cert valid (wildcard!)
