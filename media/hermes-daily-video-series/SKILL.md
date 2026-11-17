---
name: hermes-daily-video-series
description: Use when producing scheduled vertical EN+CJK videos.
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [video, ffmpeg, tts, cron, shorts, cjk]
---

# Seri video harian dari bank topik (EN + 中文)

## When to Use

Dua mode berbeda — jangan tertukar:

1. **Video dari YouTube (diminta Bang 10 Nov 2026):** tiap hari 09:00 kirim 4 video English
   + 2 video 中文 dari YouTube tentang Hermes Agent untuk pemula. Pakai `yt_daily.py`
   (+ `/etc/cron.d/hermes-yt-video`). **Bang TIDAK mau video produksi sendiri** untuk job ini.
2. **Video produksi sendiri** (slide + TTS + teks): hanya kalau Bang eksplisit minta dibuatkan.
   Pipeline: `topics.json` / `topics_feature.json` + `make_video.py` + `run_daily.py`
   (+ `/etc/cron.d/hermes-video`, sekarang DISABLED).

## Cari video YouTube (mode utama, tanpa API key)

`yt_search.py` membaca `ytInitialData` dari halaman hasil pencarian
(`youtube.com/results?search_query=…&sp=EgIQAQ%3D%3D`) dengan UA browser — tidak perlu
YouTube Data API key, hasilnya memuat durasi, views, umur video.

`yt_daily.py`:

- 10 kueri English + 8 kueri 中文, **diputar** per hari (`rotate`) supaya cakupan bergerak.
- Filter: durasi 4 menit–4 jam, judul/kanal wajib memuat "hermes", bahasa ditebak dari aksara
  (ada CJK = Mandarin) — dicek terpisah EN vs ZH supaya 4+2 tidak tertukar.
- Skor: kata kunci pemula (beginner/newbie/新手/入门/教程) + popularitas + bonus bila
  menyebut update/versi; kata `official|demo|trailer|shorts|podcast` dikurangi.
- **Anti-dobel permanen** lewat `yt_sent.json` (semua id pernah dikirim).
- **Buffer 3 hari** (`yt_buffer.json`, 12 EN + 6 ZH): pencarian lambat (±2 menit untuk 18
  kandidat), jadi hasil ekstra disimpan; hari berikutnya dikirim dari buffer tanpa cari ulang.
  Kalau buffer kosong baru scraping — jangan naikkan jumlah kueri untuk "mengejar",
  scraping YouTube bisa memakan menit.
- Kirim 1 header + 6 pesan (judul, link, kanal, durasi, views, umur).

## Produksi video sendiri (kalau diminta eksplisit)

| File | Fungsi |
|---|---|
| `topics.json` | bank topik 30 hari; tiap topik punya `what / points[4] / steps[3] / mistake / fix` dalam EN + ZH |
| `make_video.py` | render 1 video: slide PIL → TTS ElevenLabs → ffmpeg segmen → concat |
| `run_daily.py` | pilih topik hari ini (`(hari - START) % 30`), render 6 slot, kirim Telegram |
| `cron_daily.sh` | wrapper cron: cari python ber-PIL, flock, retensi 7 hari |
| `feature_watch.py` | cek rilis baru `NousResearch/hermes-agent` (state: `feature_state.json`) |
| `feature_topics.py` | rilis → topik video (sama schema) lewat DeepSeek; simpan `topics_feature.json` |
| `/etc/cron.d/hermes-video` | `0 9 * * *` WIB |

6 slot per topik = 4 EN (`what`/`why`/`how`/`mistake`) + 2 ZH (`what`/`how`). Satu topik
dipecah jadi sudut berbeda, jadi tidak mengulang topik selama 30 hari.

## Setelah 30 topik habis (aturan Bang)

`resolve_topic()` memilih sumber berdasarkan hari:

| day_index | sumber | perilaku |
|---|---|---|
| < 30 | `topics.json` | normal |
| ≥ 30, ada topik fitur | `topics_feature.json` | video dari fitur rilis Hermes |
| ≥ 30, tidak ada rilis baru | — | **SILENT**: log saja, TIDAK ada pesan Telegram |
| ≥ 30, cek GitHub error | — | satu alert Telegram + exit 1 (bukan spam) |

Beda "tidak ada fitur" dan "gagal cek" wajib dijaga: silence untuk yang pertama,
alert sekali untuk yang kedua. Kalau keduanya disamakan, pipeline bisa mati berhari-hari
tanpa ada yang tahu.

## Pitfall yang sudah menggigit

1. **Wrap CJK memotong kata latin.** `Hermes Agent` jadi `HermesAgent` dan `AI` pecah jadi
   `A` / `I`. Wrap per karakter hanya untuk aksara CJK; token latin harus utuh — pakai
   regex token (`[A-Za-z0-9][...]*|\s+|\S`), bukan `list(text)`.
2. **Push-back token menghapus teks (bug paling berbahaya).** Kalau token tidak muat dan
   ditolak di awal baris, JANGAN `lines[-1] += tok; cur = ""` — isi `cur` hilang dan satu
   frasa lenyap tanpa error. Yang benar: `cur = trial` (biarkan sedikit melebihi lebar),
   teks utuh dan tetap tidak ada tanda baca di awal baris.
3. **Safe area Shorts/Reels.** UI platform menutup ±150 px atas dan ±400 px bawah. Header
   di y≈152, konten mulai y≈560, dots di `H-400`, footer di `H-352`.
4. **PIL tidak ada di `/usr/bin/python3`.** Jalan lewat wrapper yang memilih venv Hermes
   ber-PIL (jangan `python3` polos, jangan hardcode path venv — berubah tiap update).
5. **TTS Mandarin harus dibuktikan, bukan diasumsikan.** Kirim hasil mp3 ke endpoint STT
   (`/v1/speech-to-text`, `scribe_v1`) dan bandingkan transkripnya dengan teks asli.
6. **ffmpeg zoompan:** pakai `-loop 1` + `zoompan ... d=1` dengan akumulasi `zoom+0.0006`;
   `d=<frames>` pada input loop menghasilkan frame berlipat.
7. **Telegram video:** `sendVideo` maks 50 MB; sediakan fallback `sendDocument` kalau gagal.
   Caption dipakai sebagai judul+deskripsi+tag siap copy ke YouTube.
8. **Model reasoning menghabiskan `max_tokens` → content kosong.** DeepSeek Flash menghitung
   dulu (reasoning_tokens bisa >1500 untuk prompt panjang); dengan `max_tokens` kecil,
   `message.content` pulih kosong dan `json.loads` gagal dengan “line 1 column 1”. Pakai
   `max_tokens` ≥ 9000 dan retry sekali dengan budget 2× kalau content kosong.
9. **Tag rilis campur format.** Repo punya `v0.23.0` dan `v2026.9.24`; mem-parse angka
   membuat `v2026...` dianggap lebih baru dari segala versi. Filter `^v0\.\d+\.\d+$`
   sebelum membandingkan versi.
10. **Header ikut berubah saat mode berganti.** Menulis “30-DAY BEGINNER GUIDE” mati di
    template membuat video hari ke-31 tetap mengaku seri 30 hari (kelihatan seperti template
    asal jadi). Label seri harus parameter: `30-DAY BEGINNER GUIDE` vs `NEW FEATURES · GITHUB`
    / `新功能 · GITHUB 更新`.

## Verifikasi wajib sebelum lapor selesai

- `ffprobe` tiap file: 1080x1920, `aac` ada, durasi wajar (20–40s).
- Contact sheet (`ffmpeg -vf fps=1/5,scale=360:640,tile=4x2`) → `vision_analyze`: cek teks
  tidak kepotong, tidak menabrak tepi, aksara CJK tidak jadi kotak.
- Kirim 1 video uji ke chat target, cek `ok:true` + `message_id`, lalu **hapus file uji**
  supaya cron berikutnya me-render ulang dan tidak mengirim dobel.
- Jalankan runner `--no-send` lebih dulu; render 6 video ≈ 2,5 menit.
