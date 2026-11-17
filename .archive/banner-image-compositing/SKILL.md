---
name: banner-image-compositing
description: Use when composing banner art plus text overlay.
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [banner, compositing, overlay, pillow, svg, flux, layout]
    related_skills: [banner-judi-cf, banner-judi-referensi-pattern, nanobanana-image-api]
---

# Banner Compositing — artwork AI + teks overlay yang tidak tertimpa

## QC WAJIB — pakai Gemini Decisions (JANGAN Jev)

Hasil composite **WAJIB** di-QC pakai `gemini-decision-1` (Gemini Decisions API), **BUKAN** TypeSafe
Jev. Terbukti 12-Nov-2026: Gemini 540px + 25 pertanyaan = **0,93 dtk / Rp 4,24 / 5-dari-5 BENAR**;
Jev 200px + 4 pertanyaan = **Rp 20 dan SALAH**, 240px = HTTP 400 `max_tokens_exceeded`.

Resep + cara baca: `skill_view(name='banner-engine-selection', file_path='references/qc-banner-gemini-decisions.md')`.
Pertanyaan wajib untuk kasus ini: `teks_rusak`, `teks_di_tepi`, `kontras_cukup`, `keterbacaan` —
overlay teks yang menimpa artwork adalah cacat nomor satu.

Cara merangkai banner promosi dari **dua sumber**: artwork (AI image) sebagai latar, dan
teks (headline/brand/CTA) digambar di atasnya. Fokus skill ini adalah **layout dan
teknik komposisi**, bukan prompt modelnya — untuk prompt & kanal gambar lihat
`banner-judi-cf` (user-owned).

## When to Use

- Bang minta banner dari satu gambar AI, lalu mengeluh teksnya nutup / "ga kebaca".
- Perlu menggabungkan artwork AI (subjek/karakter/scene) dengan teks tajam.
- Butuh teks **tajam sempurna** — AI image generator sering typo, jadi teksnya harus
  digambar, bukan digenerate.

## Pilih jalur: teks digambar, atau teks digenerate

| Kebutuhan | Jalur | Hasil |
|---|---|---|
| Hanya teks/headline/CTA (tanpa artwork) | **SVG render** (`banner-core.js`, lihat `/opt/data/banner-studio/`) | tajam sempurna, 6-7 KB, <1 dtk, bisa diedit 1 baris |
| Artwork saja (tak ada teks) | CF FLUX / image API | kaya visual, tapi teks sering typo |
| **Artwork + teks** (kasus paling umum) | **FLUX untuk latar → Pillow overlay teks** | visual kaya **dan** ejaan benar |

Jangan pernah meminta model gambar menuliskan headline utama kalau Anda bisa menggambarnya
belakangan — itu sumber typo nomor satu dan tidak bisa diperbaiki tanpa regenerate.

## 🔴 Pitfall terbesar: subjek AI menimpa teks di tengah frame

Model gambar menaruh subjek **tepat di tengah** secara default. Kalau overlay teks diletakkan
di area yang sama, **kepala/rambut/badan menutupi headline** — teks utama terpotong.

| Layout | Hasil |
|---|---|
| Subjek tengah, teks di atasnya | ❌ tertimpa, tidak terbaca |
| Subjek tengah, teks hanya atas+bawah | ⚠️ rawan, tergantung tinggi subjek |
| **Subjek KANAN, panel teks KIRI** | ✅ **paling stabil** — teks tidak pernah tertimpa |

**Prompt wajib menyebut posisi subjek dan area kosong**, karena tanpa itu model akan memusatkan
subjek ke tengah:
```
<subjek> positioned on the RIGHT side of the frame, ...,
the LEFT half of the image is darker empty <scene> interior with a single bright light glow,
left side kept clean and dark for text overlay
```

## Overlay yang terbaca: panel gradient + fade, bukan potongan keras

Prosedur (Pillow, urutan ini):
1. Resize artwork ke ukuran kanvas final.
2. **Panel kiri**: garis vertikal gelap solid dari x=0 sampai ~56% lebar kanvas, lalu
   **fade 200-260 px** ke transparan. Potongan keras (solid lalu langsung 0) terlihat seperti
tempelan; fade-nya yang membuat menyatu.
3. **Vignette atas/bawah** ramping (60-90 px) supaya teks di tepi tetap kontras.
4. Semua teks **rata kiri pada satu margin `X`** — jangan campur rata tengah dengan rata kiri.
5. **Footnote diberi pill gelap semi-transparan** (`rounded_rectangle` alpha ~150). Teks kecil
   di atas background ramai menghilang total tanpa ini.
6. CTA: pill emas penuh + teks gelap di atasnya (kontras tertinggi untuk elemen klik).

Script yang sudah terbukti (jangan tulis ulang):
```
/opt/data/banner-studio/overlay_left.py  <bg.png> <out.png> <BRAND> <HEADLINE> <CTA> [FOOTNOTE]
/opt/data/banner-studio/overlay.py       # subjek di tengah (hanya bila subjek memang bukan di tengah)
```

## "Kurang rame": padatkan dengan daftar elemen, bukan sinonim

Keluhan *"elemennya ga gitu rame"* tidak dijawab dengan kata sifat (`luxury casino`, `premium`).
Jawab dengan **daftar elemen konkret + kata jumlah**:

```
three glowing slot machines with visible reels showing 7s and BAR symbols,
giant roulette wheel spinning with motion blur at top,
green felt table with tall stacks of colorful poker chips,
many playing cards flying through the air (ace of spades, king, queen, joker),
dozens of golden coins and chips raining and floating everywhere,
sparkling gold confetti and light streaks, dice tumbling mid-air,
glowing neon lights and bokeh in background, extremely rich detailed composition
```

Kata penguat yang bekerja: `three`, `giant`, `many`, `dozens`, `tall stacks`, `everywhere`,
`raining`. Terbukti menaikkan elemen terlihat dari 4 → 8 jenis.

## Ukuran kanvas & varian (layout, bukan skala)

Empat preset yang dipakai, tiap preset punya parameter sendiri (pad/font/radius) — di-tune
per format, **bukan** hasil resize satu desain:
```
wide   1200x628   (feed / LP / Discord)
square 1080x1080  (IG post)
story  1080x1920  (IG/TikTok story)
hero   1600x500   (website hero)
```
Ganti ukuran → sesuaikan margin dan ukuran huruf; men-scale desain wide ke story menghasilkan
headline kecil dan ruang kosong besar.

## Verifikasi & pengiriman

- **Render ke PNG, lalu kirim ke user dan minta penilaian** — jangan mengklaim "sudah bagus"
  dari penilaian sendiri. Kalau punya tool vision, pakai untuk cek objektif: (a) teks tidak
  tertutup objek, (b) jumlah jenis elemen, (c) ejaan. Estetika tetap keputusan user.
- **Kirim ke Telegram: sediakan JPEG `quality=92` (~150-200 KB) sebagai jalur utama.**
  PNG hasil komposit bisa >700 KB dan gagal tampil di chat; PNG tetap disimpan untuk arsip.
- SVG→PNG butuh rasterizer. Yang tersedia: `npx -y @resvg/resvg-js-cli <in.svg> <out.png>`
  (unduh sekali, cache). Pillow sendiri tidak bisa meraster SVG.
- `npx -y @resvg/resvg-js-cli` memakai argumen **positional** (input lalu output); `-i/-o`
  tidak dikenali.

## Pitfalls

- **Jangan taruh teks di area yang belum dipastikan kosong** — periksa hasil render, bukan
  asumsikan promptnya dipatuhi.
- **Jangan minta lebih dari satu blok teks ke model gambar** kalau bisa digambar sendiri.
- **Moderation/rate limit**: menambah banyak kata elemen bisa memicu penolakan model; jeda
  ~30 dtk lalu retry dengan kata lebih lembut, jangan langsung ulang cepat.
- **Jangan regenerate seluruh gambar hanya untuk mengubah teks** — teks ada di layer overlay,
  cukup render ulang overlay-nya (detik, bukan menit).

## Related

- `banner-judi-cf` (user-owned) — prompt, kanal gratis, dan aturan moderation.
- `banner-judi-referensi-pattern` (user-owned) — cara meniru referensi yang dikirim user.
