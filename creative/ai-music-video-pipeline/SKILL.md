---
name: ai-music-video-pipeline
description: "Use when making an AI music video (song + video + merge)."
platforms: [linux]
---

# AI Music Video Pipeline

Workflow end-to-end: bikin lagu AI (Suno) → artwork (FLUX) → video (Kling) → gabung jadi video musik utuh (ffmpeg).

## Alur lengkap
1. **Lagu**: Suno Pro (Custom Mode) — Style field + Lyrics field dengan metatags `[Intro] [Verse] [Chorus] [Bridge] [Outro]`. Prompt craft lihat skill `songwriting-and-ai-music`. Setelah jadi → Suno Library → Download MP3 → kirim file ke agent.
2. **Artwork**: image_generate (FLUX 2) — landscape 16:9, NO TEXT di prompt (FLUX typo!). Simpan ke /opt/data/.
3. **Video**: Kling APP (klingai.com/app → Video Generation → Image-to-Video) — upload artwork sebagai start frame, paste prompt, 1080p 5-10s, Native Audio ON. Atau Kling API (lihat pitfall balance).
4. **Merge** (ffmpeg): concat 2+ klip video → loop sampai durasi lagu → tambah audio lagu:

```bash
# 1. concat list
printf "file '/path/v1.mp4'\nfile '/path/v2.mp4'\n" > /tmp/vlist.txt
# 2. merge: video loop + audio lagu, potong persis durasi lagu
ffprobe -v error -show_entries format=duration -of csv=p=0 LAGU.mp3   # dapat DUR
ffmpeg -y -f concat -safe 0 -i /tmp/vlist.txt -stream_loop -1 -i LAGU.mp3 \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -t DUR -shortest /opt/data/video_musik_final.mp4
```

## Pitfalls Kling (penting!)
- **Plan subscription ≠ API balance**: plan Standard $6.99 (660 credits utk APP) TIDAK memberi API credits. API pakai "My Balance" terpisah di Quotas page — error `429 code 1102 "Account balance not enough"`.
- **Top-up API online TIDAK tersedia** (Kling): harus Contact Customer Service (Business Inquiry form). Jalan pintas: pakai APP Kling (plan credits langsung jalan!).
- **Kling MCP** (`https://kling.ai/mcp`): butuh OAuth authorization, BUKAN API key header — semua format header (Bearer/X-API-Key/raw) → 401. Hermes native MCP hanya support header Bearer → perlu OAuth token dulu.
- **Watermark**: output APP Kling ada watermark "KlingAI 1.0/3.0" pojok kanan bawah (hilang di paket berbayar tertentu).
- **API endpoint**: `https://api.klingai.com/v1/videos/image2video` — POST {model_name:"kling-v1", image: base64, prompt, duration:"5", cfg_scale:0.5, mode:"std"} → task_id; poll GET /v1/videos/image2video/{task_id}.
- Video 2.6/3.0: native audio + multi-shot. Prompt pakai tanda kutip utk speaking/singing content.

## Pitfalls ffmpeg merge
- `-stream_loop -1` harus SEBELUM `-i` (input flag).
- `-t DUR` persis durasi lagu biar video berakhir bareng lagu.
- Output mp4: wajib `-pix_fmt yuv420p` biar playable di semua player/Telegram.
- Video Kling = 5s per klip → concat 2 = 10s → loop ×20 utk lagu 3:17 (196s).
- Kirim hasil via `MEDIA:/abs/path.mp4` (Telegram inline player).

## Verifikasi
- `ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4` → harus ≈ durasi lagu.
- `ls -la` cek ukuran; vision_analyze frame (`ffmpeg -ss 1 -frames:v 1`) utk cek isi klip.
