---
name: stirling-pdf-ops
description: Use when deploying or calling self-hosted Stirling PDF.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [pdf, stirling, mcp, docker]
---

# Stirling PDF — self-host + MCP (proven 12-Nov-2026, `andy-chloe`)

Stirling bukan pengganti pembuat PDF (itu WeasyPrint/`pdf-creator-weasyprint`), tapi lapisan
**pasca-produksi**: compress, merge, watermark, OCR, sign, split, redact, form.

## Deploy (docker, localhost-only + internal docker network)

```bash
docker network create stirling-net   # sekali
docker run -d --name stirling-pdf --restart unless-stopped \
  --network stirling-net -p 127.0.0.1:8080:8080 \
  -v /opt/stirling/data:/data -v /opt/stirling/configs:/configs -v /opt/stirling/logs:/logs \
  -v /opt/stirling/tessdata:/usr/share/tesseract-ocr/5/tessdata \
  -v /opt/stirling/fonts:/usr/share/fonts/truetype/custom:ro \
  -e DOCKER_ENABLE_SECURITY=true -e SECURITY_ENABLELOGIN=true -e SYSTEM_GOOGLEVISIBILITY=false \
  stirlingtools/stirling-pdf:latest
```
- Container agent menyusul: `docker network connect stirling-net <agent-ctr>` (tanpa recreate) → agent akses `http://stirling-pdf:8080`.
- Bridging ke host cukup `127.0.0.1` → **tidak terekspos ke internet**.
- Boot Java ±30-60 dtk; `curl /api/v1/info/status` → `{"version":"3.3.0","status":"UP"}` = siap.
- `/opt/stirling/fonts` dipakai kalau perlu font tambahan (mis. Noto CJK dari container lain:
  `docker cp <ctr>:/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc /opt/stirling/fonts/`).

## Auth + API key (kalau mau MCP)

MCP **butuh akun**: `X-API-KEY` harus milik user aktif. Dengan `DOCKER_ENABLE_SECURITY=true`:
```python
# login default first-run: admin / stirling  (SEGERA ganti)
POST /api/v1/auth/login      {"username":"admin","password":"stirling"}   -> session.access_token
POST /api/v1/user/get-api-key       (Bearer JWT)  -> {"apiKey":"..."}
POST /api/v1/user/update-api-key    (Bearer JWT)  -> rotate key
```
⚠️ `/api/v1/user/generate-api-key` **tidak ada** di 3.3.0 (404 "No endpoint found") — yang benar
`get-api-key` / `update-api-key`.

## Aktifkan MCP

Edit `/opt/stirling/configs/settings.yml`:
```yaml
mcp:
  enabled: true            # default false -> tidak ada /mcp
  auth:
    mode: apikey           # opsi: oauth | apikey (X-API-KEY dari akun)
```
lalu restart container. Log sukses: `McpSecurityConfig - MCP server enabled` +
`McpToolCatalog - MCP tool catalog discovered 64 PDF operation(s)`.

## Sambung ke Hermes

```yaml
mcp_servers:
  stirling:
    url: http://stirling-pdf:8080/mcp
    headers:
      Authorization: Bearer ${STIRLING_API_KEY}   # ← ini yang BERHASIL
    enabled: true
```
- Header `X-API-KEY: ${STIRLING_API_KEY}` **GAGAL 401** di MCP client Hermes (walau curl manual 200).
  Pakai `Authorization: Bearer ...` — Stirling menerima keduanya untuk MCP.
- Verify: `hermes mcp test stirling` → `✓ Connected` + `Tools discovered: 8` (namespace: misc, pages,
  security, upload, download, dll — 64 operasi total).
- REST (`/api/v1/...`) tetap pakai header `X-API-KEY`; `Authorization: Bearer` di REST → `{"error":"Invalid token"}`.

## 🔴 Nama parameter API 3.3.0 (nama lama DIABAIKAN diam-diam)

`watermark` benar: `watermarkType, watermarkText, fontSize, rotation, opacity, customColor` (**hex string**,
BUKAN boolean), `widthSpacer`, `heightSpacer`, `alphabet`.
Salah tapi tidak error: `watermarkFontSize`, `watermarkRotation`, `watermarkColor`, `customColor=true`
→ hasil tetap abu-abu & tegak, tanpa pesan gagal. Selalu cek schema, jangan tebak:
```bash
curl -s http://127.0.0.1:8080/v1/api-docs | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['components']['schemas']['AddWatermarkRequest']['properties'].keys())"
```

## Batasan yang ditemukan
- **Watermark teks CJK gagal**: `No glyph for U+59D0 in font NotoSans-Regular` — Stirling hanya
  memakai font bundled meski `fonts-noto-cjk` terpasang dan `fc-list` melihatnya. Workaround: watermark
  Latin (“CONFIDENTIAL”) atau watermark gambar PNG (teks CJK dibuat dulu di PNG).
- Merge gagal `JPDFium merge failed` = salah satu input BUKAN PDF (sering karena request sebelumnya
  balas JSON error). Cek `head -c 5 file` harus `%PDF`.
- Compress tidak selalu mengecilkan PDF teks tanpa gambar (294→300 KB); efek nyata pada PDF berisi
  gambar: 214 KB → 88 KB (−59%). Ukur, jangan asumsi.

## Helper siap pakai
`/opt/data/scripts/stirling_pdf.sh` (di volume agent) — `status|compress|watermark|merge|ocr|protect`,
key dibaca dari `/opt/data/.env` (`STIRLING_API_KEY`), otomatis tolak output non-PDF.

### Watermark nomor WA + token anti-penyalahgunaan (proven 12-Nov-2026)
```bash
stirling_pdf.sh protect in.pdf out.pdf "+60 12-345 6789" AC-20261112-7F3K 0 "Chloe"
# arg5 flatten: 1 = halaman jadi gambar (teks tak bisa dicopy), 0 = tetap tajam/ringan
```
Tiga lapis yang dipakai: (1) watermark `WA <nomor> · <token>` emas 30° opacity 0.28,
(2) metadata forensik (`/Author`, `/Keywords` berisi token) — tetap bisa dilacak walau
watermark dikrop, (3) flatten opsional untuk dokumen berisi harga/komisi.

🔴 **URUTAN WAJIB: watermark → flatten → metadata.** `convertPDFToImage` me-render ulang halaman
dan **membuang metadata** (Author/Keywords hilang, terbukti). Kalau metadata diset sebelum flatten,
hasil akhirnya tanpa metadata sama sekali. Ukuran setelah flatten ~3x (304 KB → 960 KB untuk 2 halaman)
— jangan flatten dokumen marketing yang dikirim via WhatsApp.
- Teks watermark harus Latin/angka. Nomor WA aman; nama berkarakter China TIDAK (lihat batasan CJK).
- Watermark berulang selalu terpotong di tepi halaman — itu normal untuk pola tiled; kalau mau utuh,
  turunkan `fontSize` atau perbesar `widthSpacer`/`heightSpacer`.

### Dokumen latar PUTIH — default gold hampir hilang
Default `customColor=#C9A227` + `opacity=0.28` hanya cocok untuk kanvas gelap; di atas putih hasilnya
nyaris tak terlihat. Untuk dokumen putih pakai **`#8A6A1E`, `opacity=0.20`, `fontSize=28`,
`widthSpacer=210`, `heightSpacer=210`** — watermark terbaca jelas tanpa menutupi angka (hasil uji:
watermark 9/10, teks body tetap 100% terbaca). Untuk dokumen gelap tetap pakai gold default.

### Verifikasi hasil secara visual (tanpa pdftoppm/pdfinfo)
Server/bot tidak punya PDF rasteriser, tapi Stirling bisa merender halaman ke PNG:
```bash
curl -s -H "X-API-KEY: $KEY" -o /tmp/wm.zip -F fileInput=@out.pdf -F imageFormat=png \
  "$S/api/v1/convert/pdf/img"
python3 -c "import zipfile;z=zipfile.ZipFile('/tmp/wm.zip');print(z.namelist());z.extract(z.namelist()[0],'/tmp/wmpng')"
```
Balasannya **ZIP** berisi `name_1.png`, `name_2.png`, … (container agent sering tidak punya `file`/`unzip` —
pakai `python3 zipfile` dan `head -c5` untuk cek magic `%PDF`). Lalu `vision_analyze` pada PNG-nya dan
tanya spesifik: teks watermark terbaca? menutupi angka? kelihatan profesional?
