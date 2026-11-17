---
name: video-frame-extraction
description: Use when video is too large for vision — extract frames.
---

# Video Frame Extraction (video gede → frame kecil → vision)

**Kapan dipakai:** user kirim video gede (iPhone 4K/1080p, biasanya >50MB) dan
vision model ga bisa proses (413 Request Entity Too Large / "Video too large").
Video 1 menit 1080p ≈ 100-150MB, 4K ≈ 350MB+ — jauh di atas limit Hermes 50MB.

**Kenapa:** Hermes `video_analyze` kirim video UTUH (base64) ke vision model →
video gede = request kebesaran → 413. Extract frame (foto) dulu = hemat
90%+ bandwidth & muat di limit.

## Langkah

1. **Simpan video dulu** (dari platform: download ke lokal):
   - Telegram: file video biasanya sudah di-download oleh Hermes ke cache.
   - Cari di `/opt/data/cache/` atau minta user upload ulang.
2. **Extract frame** pakai script:
   ```bash
   bash /opt/data/scripts/extract_frames.sh <video.mp4> [fps] [max_width] [out_dir]
   ```
   - Default: 0.5 fps (1 frame tiap 2 detik), max width 1280px.
   - Video 1 menit → ~30 frame, total ~5-10MB (vs 100MB+ asli).
   - Kalau video panjang banget, turunkan fps (0.2 = 1 frame tiap 5 detik).
3. **Analisis frame** — kirim tiap frame ke `vision_analyze` (atau gabung
   beberapa frame jadi 1 pesan). Frame dijamin muat (resize 1280px, JPG q3).
4. **Sampaikan hasil** ke user: deskripsi video dari frame-frame tsb.

## Pitfalls

- **ffmpeg harus ada**: `/usr/bin/ffmpeg` (Hermes Cloud ada ffmpeg 7.1.5).
  Kalau ga ada: `apt install ffmpeg` atau pakai server lain.
- **Agent tanpa terminal** (pattysnow448 dulu) ga bisa jalanin script —
  perlu `terminal` di-enable di config.yaml (`disabled_toolsets` jangan
  berisi `terminal`), lalu restart gateway.
- **Video iPhone HEVC (H.265)**: ffmpeg bisa baca, tapi kalau error codec,
  tambah `-c:v mjpeg` atau konversi dulu ke mp4 H.264.
- **Frame kebanyakan**: jangan extract semua frame (video 1 menit @30fps =
  1800 frame!). Selalu pakai fps rendah (0.5) + max_width kecil.
- **Scale `-2`**: biar lebar genap (wajib buat codec). Jangan `-1` (error).

## Verify

```bash
ls <out_dir>/frame_*.jpg | wc -l   # jumlah frame > 0
du -sh <out_dir>                    # total kecil (MB, bukan ratusan MB)
```
