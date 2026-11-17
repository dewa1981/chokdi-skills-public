---
name: onlydogshop88-lp-ops
description: Use when working on onlydogshop88.com (Premium Dog Shop LP).
version: 1.0.0
author: chokdi_staging
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [landing-page, cloudflare-pages, amp, seo, dog-shop]
    category: devops
---

# onlydogshop88.com — Premium Dog Shop Phnom Penh

## When to Use

Pakai skill ini kalau Bang menyebut `onlydogshop88.com`, `premium-dog-shop`, `puppy-khmer`,
"web anjing Phnom Penh", atau minta ubah/QA/SEO/deploy dari LP toko puppy itu.

Landing page toko anak anjing (impor Thailand + breeding lokal) untuk pasar Phnom Penh.
Statis, CF Pages, 3 bahasa (EN/Khmer/中文) via switch JS, CTA WhatsApp.

## Peta aset

| Item | Nilai |
|---|---|
| Domain | https://onlydogshop88.com (+www) · AMP di `/amp` |
| CF Pages project | `premium-dog-shop` |
| CF account / zone | `c70bde71f28fd58bbf799aa2d9478068` / `616d77e3ed405a0da650be8e3d32ea0c` |
| Token | `CF_DEV_FULL_ACCESS` di `/root/.hermes/.env` |
| Sumber | `/opt/data/lp/puppy-khmer` |
| Deploy | `dist/` (hasil `tools/build_dist.sh`) |
| WA bisnis | 85592206547 |

Struktur sumber: `index.html` (sumber utama), `amp.html` (TURUNAN — jangan edit manual),
`tools/make_amp_src.py` (index → amp.src.html), `build-amp.js` (inline CSS → amp.html),
`tools/make_icons.py` (favicon/apple-touch/manifest dari `assets/brand/logo-512.png`),
`tools/build_dist.sh` (semua di atas + susun `dist/`), `404.html`, `sitemap.xml`, `robots.txt`,
`site.webmanifest`, `_headers`.

## Alur kerja (jangan improvisasi)

1. Edit `index.html` / `assets/lp.css` / `assets/lang.js`.
2. `bash tools/build_dist.sh` — generate ikon, amp.src.html, amp.html, lalu dist/ bersih.
3. `npx amphtml-validator dist/amp.html` → wajib **PASS**.
4. Deploy preview: `--branch=preview-fix` → curl URL preview.
5. Deploy produksi: `--branch=main` → purge cache `/`, `/amp`, `/assets/lp.css`.
6. Verifikasi per-path (resep lengkap di `README.md` repo proyek).

## Klien & konteks Telegram

Klien pemilik proyek = **Only dog pets Shop in Cambodia**, user Telegram `1062474922`
(`@onlydogshopincambodia`), administrator grup `-1004427420617`
("Ano333 & chokdi_staging_bot, Only dog pets Shop in Cambodia"). Grup ini supergroup + forum;
ID lama sebelum migrasi `-5551585690` — kalau bot "tidak menjawab" di grup ini, cek dulu allowlist
(lihat skill `hermes-bot-telegram-allowlists`), bukan mengira klien mengabaikan.

- **Bahasa klien: Khmer + English. JANGAN balas dia dalam Bahasa Indonesia.** Bahasa Indonesia
  hanya untuk Bang (Ano333).
- Copy Khmer resmi yang sudah dikoreksi (klien menulis `នឹង`/`កម្មង់`, yang benar `និង`/`កម្ម៉ង់`):
  `មានលក់កូនឆ្កែពូជល្អៗ និងទទួលកម្ម៉ង់គ្រប់ពូជកូនឆ្កែ`
  Versi pendek untuk headline banner: `កូនឆ្កែពូជល្អៗ — ទទួលកម្ម៉ង់គ្រប់ពូជ`

## Teks Khmer di banner (penting)

Model gambar AI **selalu merusak aksara Khmer** (vokal salah tempat, konsonan tumpuk pecah).
Alur yang benar: render artwork/foto tanpa teks → overlay teks Khmer pakai font asli
(**Noto Sans Khmer** atau **Kantumruy Pro**) supaya glyph utuh dan tajam. Jangan pernah menyerahkan
banner yang teks Khmer-nya digenerate model gambar.

## Aturan keras

- **AMP head jangan diedit manual.** Template head ada di `tools/make_amp_src.py`; JSON-LD disalin
  otomatis dari `index.html`. Dulu head AMP tertinggal brand lama + `puppy.example` karena diedit terpisah.
- **Nomor WA harus sama di 4 tempat**: link `wa.me`, JSON-LD `telephone`/`contactPoint`,
  `404.html`, dan blok telepon di hero.
- **Ubah CSS = ubah query versi** di `index.html` (`assets/lp.css?v=YYYYMMDDx`). `_headers` memberi
  `/assets/*` cache 7 hari, jadi URL sama = CSS lama tetap tayang.
- Setelah deploy produksi selalu purge; `dist/` basi adalah penyebab nomor satu "live tidak berubah".

## Pelajaran yang sudah dibayar mahal

- Pages tanpa `404.html` membalas **200 + index.html** untuk URL apa pun (soft-404). Selalu punya `404.html`.
- AMP canonical menunjuk `/` (bukan `/amp`), dan `index.html` punya `<link rel="amphtml" href=".../amp">`.
- Halaman `/amp.html` selalu 308 → `/amp` (Pages membuang ekstensi `.html`) — itu normal.
- **Ukur layout dengan CDP, jangan cuma lihat screenshot.** Di 320px header (logo+brand+language switch)
  meluber 331/320 dan tidak kelihatan di screenshot 390px. Resep: set `Emulation.setDeviceMetricsOverride`
  SETELAH tab dibuat (kalau sebelum `new_tab`, override hilang → viewport balik 780px dan CSS mobile tidak aktif),
  lalu bandingkan `document.documentElement.scrollWidth/clientWidth` di 320/360/390 dan daftar elemen yang
  `right > clientWidth`.
- Tombol CTA yang lebarnya ikut panjang teks selalu terlihat "tidak rata" di HP: pakai
  `display:grid; grid-template-columns:repeat(2,minmax(0,1fr))` untuk 4 tombol (2×2), bukan flex-wrap.
- `vision_analyze` bisa salah soal lebar relatif (pernah bilang tombol kiri lebih lebar padahal
  `getBoundingClientRect()` semua 135px) — angka pengukuran yang menang, screenshot hanya untuk kesan visual.
