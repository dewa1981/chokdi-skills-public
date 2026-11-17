---
name: headless-diagram-png
description: "Use when rendering a diagram to PNG without a browser."
---

# Headless Diagram → PNG (tanpa browser/chromium)

Buat diagram arsitektur / alur (dark-themed) jadi file PNG di Hermes Cloud / VPS
yang **tidak punya browser headless**. Proven 2026-08-14 (diagram JARVIS v2,
`/opt/data/jarvis-architecture-v2.png`).

## Kenapa tidak pakai browser?

- `browser_navigate` ke `file:///opt/data/x.html` → **diblokir** "URL targets a
  private or internal address" (guard Hermes).
- Chromium/puppeteer: cache puppeteer di `/opt/data/.cache/puppeteer/` isinya
  folder KOSONG (binary belum pernah di-download); `npm i puppeteer` di
  `/opt/data` tidak ada node_modules. Jangan buang waktu install browser.
- `wkhtmltoimage` / `rsvg-convert` / `inkscape` / `convert` — tidak ada.
- Yang ADA dan TERBUKTI: **Python PIL (Pillow)** (`import PIL` OK) + fonts
  DejaVu di `/usr/share/fonts/truetype/dejavu/` (+ liberation, freefont).

## Resep PIL (dari sesi JARVIS v2)

1. **Fonts**: `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf` untuk body; mono
   `DejaVuSansMono.ttf` kalau mau gaya code. `ImageFont.truetype(path, size)`.
2. **Gaya dark premium** (sama dengan skill architecture-diagram):
   - BG `(2,6,23)` (#020617), grid 40px `(30,41,59)` (#1e293b) — gambar garis
     manual, jangan pattern.
   - Kotak: `d.rounded_rectangle(xy, radius=10, fill=..., outline=..., width=...)`.
     Fill semi-transparan dari SVG **tidak didukung** — pakai warna solid gelap
     per kategori (contoh: cyan-bg `(8,51,68)`, emerald-bg `(6,78,59)`,
     violet-bg `(76,29,149)`, slate-bg `(30,41,59)`).
   - Teks: `d.text((cx, y), text, font=font, fill=..., anchor="mm")` untuk
     center, `anchor="lm"` untuk kiri. Warna: putih `(229,231,235)`, abu
     `(148,163,184)`, aksen = warna stroke.
3. **Panah + elbow**: hitung sudut `math.atan2(dy, dx)`, gambar polygon
   segitiga di ujung (14px). Elbow = `d.line(points, joint="curve")` lalu
   arrowhead di segmen terakhir. Tandai label di dekat panah.
4. **Emoji TIDAK dirender** oleh DejaVu → ganti dengan teks biasa (contoh:
   "Tony Stark" tanpa 🦾, "JARVIS Web App" tanpa 🔊). Cek NotoColorEmoji ada
   tapi PIL core ga render bitmap color font — jangan andalkan.
5. **Verifikasi visual WAJIB**: `vision_analyze(image_url=<path>)` dengan
   pertanyaan "apakah teks tumpang tindih / keluar kotak / panah masuk akal?"
   Perbaiki koordinat kalau ada yang nabrak (iterasi cepat — render <1s).
6. Simpan PNG + sertakan juga file `.html` source (kalau user mau buka/edit
   di browser).

## Pitfall

- `d.text` anchor PIL cuma 2-karakter (`"mm"`, `"lm"`) — anchor 1 karakter
  (`"m"`) → `ValueError: anchor must be a 2 character string`.
- Layout: hitung koordinat manual. Kotak tengah (HERMES) paling besar, panah
  masuk/keluar harus nyambung ke tepi kotak, bukan ke tengah kotak lain.
- Kalau teks panjang (poin skill), pecah jadi beberapa baris `ctext(...)` per
  baris dengan `y` bertambah ~22-24px.
