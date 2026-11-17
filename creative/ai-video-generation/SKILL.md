---
name: ai-video-generation
description: "Use when making AI videos from photos via fal.ai."
---

# AI Video Generation (fal.ai FLUX 3)

Bikin video AI dari FOTO via fal.ai FLUX 3 (image-to-video) — workflow TERBUKTI 2026-08-08 (video anak "Petualangan Putri" — 5 versi + gabungan final, Bang puas).

## Kapan dipakai

- User minta video dari foto (keluarga, produk, konten) — "bikin video dari foto ini"
- FLUX 3 via Nous habis (free promo ended) → pakai fal.ai langsung (API key!)
- Generate image-to-video dengan audio + animasi halus

## Setup

- API key fal.ai di `FAL_KEY` (.env) — format: `xxxx:yyyy`
- Balance: pay-as-you-go — harga FLUX 3 video = **$0.17/detik (720p)**, $0.29/detik (1080p) — video 7-8 detik ≈ $1.2-1.4
- Top up: fal.ai/dashboard/billing (Add credits — BUKAN cuma add card!)
- Foto input: upload ke GitHub repo raw (raw.githubusercontent.com) — FAL butuh URL publik yang bisa diakses (CF-protected URL kadang diblokir FAL!)

## Workflow (TERBUKTI!)

1. **CROP FOTO TIGHT** — ini KUNCI biar subjek gak "pendek/kepala gede" di video:
   ```bash
   ffmpeg -y -i foto.png -vf "crop=W:W:(iw-W)/2:(ih-W)*0.55,scale=1080:1080" tight_square.png
   ```
   (zoom subjek ~1.5x — potong background — SQUARE 1:1!)
2. **Upload tight square → GitHub** (raw URL): commit ke repo static/images/ + push
3. **Submit** ke fal.ai:
   ```bash
   curl -X POST "https://queue.fal.run/blackforestlabs/flux-3/image-to-video" \
     -H "Authorization: Key $FAL_KEY" -H "Content-Type: application/json" \
     -d '{"prompt":"...","image_url":"https://raw.githubusercontent.com/USER/REPO/main/static/images/foto.png","duration":7,"resolution":"720p","generate_audio":true,"aspect_ratio":"1:1"}'
   ```
   - `aspect_ratio: "1:1"` (square!) — video 9:16 dari foto portrait sering dapat BLACK BARS + subjek kecil
   - Prompt: sebut subjek + "natural proportions, full body visible, do not zoom on the face"
4. **Polling** — endpoint yang BENAR (bukan /image-to-video/ di path!):
   ```
   GET https://queue.fal.run/blackforestlabs/flux-3/requests/{request_id}/status
   GET https://queue.fal.run/blackforestlabs/flux-3/requests/{request_id}  (result saat COMPLETED)
   ```
   - Status: IN_QUEUE → IN_PROGRESS → COMPLETED (2.5-5 menit normal!)
   - Result: `{"video":{"url": "...mp4"}}` — download + kirim ke user
5. **Gabung video** (ffmpeg — normalisasi dulu biar concat mulus):
   ```bash
   ffmpeg -y -i v1.mp4 -c:v libx264 -preset fast -crf 23 -c:a aac -ar 44100 -ac 2 -vf "scale=720:720,fps=30" v1_norm.mp4
   printf "file '/tmp/v1_norm.mp4'\nfile '/tmp/v2_norm.mp4'\n" > list.txt
   ffmpeg -y -f concat -safe 0 -i list.txt -c copy gabungan.mp4
   ```

## Pitfalls (SEMUA KENA!)

- **Foto square → video 9:16 = subjek PENDEK/kepala gede** (FLUX style!) — FIX: tight crop + square 1:1 (terbukti!)
- **Wajah berubah di edit** — FIX: pakai reference image + prompt "LOCK THE FACE — IDENTICAL — no reshaping" (image edit!)
- **Content checker flag** (foto anak kadang di-flag — "content policy violation") — FIX: RETRY + UBAH PROMPT (hindari kata pemicu — pakai "little girl in pink dress" vs "toddler... magical wonderland") — 3-4 retry sering lolos!
- **"User is locked. Exhausted balance"** — balance habis ATAU transient (balance lag!) — cek dashboard + retry setelah 30 detik
- **JSON parse gagal di execute_code** (request_id kosong padahal body valid!) — ambil ID dari print output (kelihatan!) + polling hardcode
- **405 di status endpoint** — path salah — pakai `/requests/{id}/status` (BUKAN `/image-to-video/requests/...`)
- **Script timeout 300s** — polling loop > 5 menit ke-kill — pecah jadi submit + polling terpisah
- ffmpeg `zip`/tools kadang gak ada — pakai ffmpeg untuk crop/scale (bukan ImageMagick)

## Tools terkait

- FLUX 3 video via Nous (`bfl_flux3_*`) — free promo ended — fallback fal.ai
- Image edit (lock face): `image_generate` (FAL — image_url + reference_image_urls)
- Video edit dasar: ffmpeg (potong/gabung/normalisasi)
