---
name: cloudflare-streamline-video
description: Use when evaluating Cloudflare Streamline video pipelines.
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [cloudflare, video, streamline, ffmpeg, containers, durable-objects, stream, promo-video]
    related_skills: [cloudflare-api-ops, product-promo-video-from-image, cartoon-motion-video-ffmpeg, reel-editing-ffmpeg]
---

# Cloudflare Streamline — pipeline video kustom di Cloudflare

## When to Use

Use this skill when:

- Bang kirim link/blog Streamline dan tanya "ini apa / bisa dipakai?"
- Butuh **livestream dengan overlay realtime** (logo bonus, scoreboard, harga) untuk LP judi / Casino.
- Butuh **burn-in subtitle** atau **watermark dinamis** ke video hosted.
- Video promo/editing sudah **kebesaran untuk VPS sendiri** (volume ratusan/hari) dan butuh auto-scale.
- Jadi **referensi arsitektur** saat bikin pipeline media sendiri (Container + Durable Object + FFmpeg).

## When NOT to Use

- **Video promo pendek & jarang** — ffmpeg di VPS sendiri **$0** dan sudah terbukti. Jangan pindah hanya
  karena "baru". Streamline = Container + Cloudflare Stream, **keduanya berbayar**.
- Tidak punya akun Cloudflare Stream / tidak mau biaya per-menit video.

## Ringkasan

**Streamline** (rilis Birthday Week, Okt 2026) = **playground + contoh kode** (bukan produk jadi) untuk
bikin **custom video pipeline** di Cloudflare. Bukan layanan sekali-klik — ini arsitektur yang bisa dideploy.

Open source: `github.com/cloudflare/streamline` (media engine) +
`github.com/cloudflare/streamline-demo` (contoh app: Worker + Astro frontend + Access tooling).

## Arsitektur (2 komponen)

```
[Kontrol: Worker + Durable Object]
        ↓ start/stop/metrics
[Media Engine: Container (Go controller + FFmpeg)]
        ↓
[Input: RTMPS | HLS | Webcam | app-supplied]
[Output: RTMPS ke Stream Live | WebSocket preview | hosted video baru]
```

- **Media Engine** — di **Container**, HTTP server Go + **FFmpeg** untuk proses nyata.
  Menarik RTMPS dari Stream Live input, publish RTMPS ke input lain, pull HLS manifest dari Stream.
- **Application** — **Worker** (UI, auth, policy) + **Durable Object** (orkestrator sesi + container lifecycle).
- **Kunci desain:** sesi media punya **lifecycle independen dari request** — app boleh disconnect,
  container tetap proses sampai di-stop. Diimplementasi dengan override `onActivityExpired()`:
  kalau expiry belum lewat → `renewActivityTimeout()`, kalau sudah → `destroy()`.
  Ada **max duration** agar sesi tidak jalan selamanya.
- Mode lokal: container = Docker lokal, tanpa Durable Object, tanpa access control (single user).

## API (session-based, dari `@cloudflare/streamline/client`)

| Method | Fungsi |
|---|---|
| `createStreamline()` | instance baru |
| `streamline.sessions.create()` | sesi pemrosesan baru |
| `streamline.sessions.resume(id)` | sambung ulang sesi |
| `session.start(config)` | jalankan pipeline |
| `session.ingest(chunk)` | kirim video (mode webcam) |
| `session.annotation(png)` | update overlay anotasi transparan |
| `session.metrics()` | metrik sesi |
| `session.stop()` | hentikan pemrosesan |

Bentuk pipeline (`session.start(config)`):

```javascript
const session = await streamline.sessions.create()
const result = await session.start({
  input: { type: 'rtmp', profile: 'primary-input' },
  pipeline: [
    { op: 'overlay', params: { image: '/app/assets/cf-logo.png', position: 'top-right' } },
    { op: 'encode',  params: { codec: 'h264', preset: 'fast', bitrate: '1500k',
                              resolution: '1280x720', fps: 30 } },
  ],
  output: { mode: 'rtmp', profile: 'primary-output' },
})
```

## Playground publik — demo yang TERBUKTI hidup (dicek 3-Okt-2026)

`https://playground.streamline-video.workers.dev` → **HTTP 200** (0,17 s), frontend **Astro v7.1.3**.
Nav-nya memperlihatkan 6 demo siap coba (nama + use case, dari halaman masing-masing):

| Path | Judul | Use case nyata |
|---|---|---|
| `/` | Video Pass-Through | alirkan input apa adanya (baseline) |
| `/overlay` | Video Overlay | **composite logo/watermark** — cocok buat brand judi |
| `/annotation` | Browser Annotation Overlay | **gambar langsung di preview livestream**, tiap stroke ikut ter-encode |
| `/pip` | Picture-in-Picture | dua sumber video, satu di dalam yang lain |
| `/filters` | Real-Time Video Filters | slider filter, stream restart otomatis |
| `/subtitles` | Subtitle Burn-in | **HLS in → subtitle WebVTT jadi SRT → dibakar ke frame** (video promo ID) |
| `/probe` | Probe | owner-only, diagnosa media |

Catatan tes: `curl` HTML-nya cukup untuk verifikasi (no API endpoint publik — `/api`, `/sessions`, `/health`
→ **404**; playground ini UI demo, bukan REST API). Upload video **belum pernah dites** dari sisi kita —
jangan klaim bisa sebelum dicoba.

## Keputusan biaya (penting sebelum menawarkan)

| | ffmpeg di VPS kita | Streamline (CF) |
|---|---|---|
| Biaya | **$0** (server sendiri) | Container + **Cloudflare Stream** = berbayar |
| Kontrol | penuh | terikat platform CF |
| Skala | batas CPU sendiri | auto-scale |
| Kesiapan | sudah jalan (skill video kita) | perlu deploy + kuota |

**Pola jawab ke Bang:** sebut dulu kalau video promo kita sudah bisa gratis via ffmpeg; tawarkan Streamline
saat kebutuhannya naik kelas (livestream realtime ber-overlay, volume besar, watermark per-user).
Jangan dorong migrasi tanpa alasan beban.

## Pitfall

- Ini **contoh/playground**, bukan SaaS — jangan bilang "Cloudflare punya layanan edit video" tanpa kualifikasi.
- `streamline-demo` memakai **Access tooling** + 1 container identity per user terverifikasi di playground;
  deployment sendiri perlu atur Access + admission control.
- Iterasi sekarang pakai **CPU Container untuk media processing** → bottleneck di kualitas/frame-rate tinggi
  (pengakuan resmi di blog). Jangan janjikan 4K realtime.
- Jangan uji upload ke playground publik dari akun produksi tanpa izin Bang.
