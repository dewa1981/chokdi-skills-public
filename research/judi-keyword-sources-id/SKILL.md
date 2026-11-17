---
name: judi-keyword-sources-id
description: "Use for judi/slot keyword Indonesia: which sources work."
version: 1.0.0
author: chokdi_staging
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [seo, keyword, judi, indonesia, bing, duckduckgo, trending]
---

# Keyword Judi Indonesia — Sumber Data yang Benar-Benar Jalan

Owner minta "keyword judi yang lagi trending di Google Indonesia", riset
keyword niche slot/togel/sportsbook, atau laporan harian keyword ke grup.
Skill ini menentukan sumber mana yang menghasilkan data dan mana yang kosong,
lalu cara menyusun skrip laporan yang tidak spam.

## Peta sumber (diverifikasi dari server kita)

| Sumber | Keyword judi | Catatan |
|---|---|---|
| Google Autocomplete `suggestqueries.google.com/complete/search` | **kosong** | balas `["q",[]]` walau query biasa normal — penyensoran, bukan rate-limit |
| Google Trends explore API | **429 setelah 2–3 keyword** | bot-check dari IP VPS; `trendspyg` sendiri jalan |
| Google Trends via `trendspyg` (`pip install trendspyg[analysis]`) | jalan 1–3 keyword lalu berhenti | keyword pertama 25s, berikutnya 5s; request ke-4+ balas `RateLimitError: hard, per-IP cooldown` — bertahan berjam-jam, bukan retry-able |
| Google Trends RSS `trends.google.com/trending/rss?geo=ID` | jalan, tapi generik | isi bola/gempa; parameter `category=` diabaikan (semua kategori sama) |
| Reddit `.json` search | **Blocked** | nolak IP datacenter |
| SERP scrape (PAA/related) | gagal untuk judi | halaman hasil disensor/challenge |
| **Bing** `api.bing.com/osjson.aspx?query=<q>&market=id-ID` | **buka** | JSON `[query,[saran…]]`, saran judi lengkap |
| **DuckDuckGo** `duckduckgo.com/ac/?q=<q>&kl=id-id` | **buka** | JSON `[{"phrase":"…"}]`, brand terbaru |

Jadi fondasi riset keyword judi ID = **Bing + DuckDuckGo autocomplete**.
Jangan bangun skrip trending judi di atas Google/Reddit — hasilnya kosong,
429, atau "Blocked", dan jangan laporkan itu sebagai bug tool.

## Prosedur riset manual (cepat, tanpa tool)

1. Susun 20-25 seed: `slot`, `slot gacor`, `slot gacor hari ini`, `rtp slot`,
   `demo slot`, `situs slot`, `slot88`, `maxwin`, `judi online`, `togel`,
   `togel online`, `bandar togel`, `sbobet`, `sbobet88`, `bandar bola`,
   `parlay bola`, `casino online`, `slot dana`, `pragmatic play`, `pg soft`.
   Seed pendek memunculkan brand spesifik, seed panjang memunculkan intent.
2. Panggil Bing **dan** DDG per seed, gabung dengan `set` (Bing ~12 + DDG ~8 saran).
3. Filter: buang saran berisi emoji, panjang <3 atau >70, dan frasa bahasa
   Inggris murni. `pg soft` memang memunculkan `pg softball` — filter panjang
   saja tidak cukup, pakai daftar blokir kata.
4. Kelompokkan per kategori substring: SLOT (`slot/gacor/maxwin/rtp`),
   SPORTS (`sbobet/bola/parlay/odds`), TOGEL (`togel/toto/4d/macau`),
   CASINO, PROVIDER (`pragmatic/pg soft/…`).
5. Laporkan: total keyword, contoh per kategori, dan **peluang** (long-tail
   edukasi seperti `rtp slot adalah`, `bandar togel itu apa`, brand-specific
   yang cocok dengan brand kita).

Acuan implementasi lengkap (Bing+DDG, anti-dobel hash, kategori, arsip harian,
render XLS 3 sheet, output Telegram): lihat `references/trending-keyword-script.md`.

## Aturan laporan

- **Jangan mengarang angka volume.** Bing/DDG tidak memberi volume; tool self-host
  gratis hanya memberi bucket relatif. Angka bulanan butuh Google Keyword Planner
  atau API berbayar (DataForSEO/Serper). Bilang apa adanya.
- **Data pihak ketiga wajib dikutip sumbernya** (laporan We Are Social/Meltwater,
  Semrush trending sites) dan dipisahkan dari data yang kita tarik sendiri.
- Beri **insight aksi**, bukan cuma daftar: mana yang evergreen, mana yang
  brand-specific kompetitor (hindari), mana yang cocok brand kita.

## Pitfall

- **Jangan cari `message_thread_id` topik dengan mem-brute-force ID.** Telegram tidak
  punya API list-topik, dan `reply_to_message.forum_topic_created` hanya muncul untuk
  pesan pertama yang dibuat sesudah topik dibuat — begitu ada pesan lain, info nama
  topik hilang. Akibatnya topik lama tidak akan pernah terdeteksi lewat probe, dan scan
  ratusan ID membuang menit tanpa hasil. **Tanyakan ke memori dulu** (`hindsight_recall`
  "topic <nama> thread id") atau `sessions`/`state.db` untuk riwayat pembuatan topik;
  baru probe ID yang sudah ada, satu kali, untuk konfirmasi nama.
- **Google memblokir keyword judi, Google tidak diblokir untuk query lain.**
  Kalau autocomplete judi kosong padahal query normal jalan, itu sensor —
  jangan retry berulang atau ganti user-agent, ganti sumber.
- **Satu tes keyword yang lolos BUKAN bukti sebuah sumber bisa dipakai harian.** Sumber berbasis
  Google bisa lulus tes tunggal (25 detik, data lengkap) lalu langsung memblokir `<script>` begitu
  dijalankan 8 keyword berurutan. Sebelum membangun pipeline di atasnya, jalankan **seluruh daftar
  keyword** sekali (bukan 1 keyword), dan hitung di keyword ke berapa 429 pertama muncul. Laporkan
  batas itu ke user — jangan klaim "sumbernya jalan" dari satu sampel.
- **Rancang fallback tanpa sumber eksternal lebih dulu.** Arsip harian autocomplete yang sudah
  terkumpul (`snapshots/YYYY-MM-DD.json`, `keyword_archive.jsonl`) cukup untuk menghitung tren
  (keyword baru hari ini vs kemarin, stabil N hari, kategori naik/turun) tanpa Google Trends sama
  sekali. Ini menjawab "trending" tanpa rate-limit dan tanpa biaya — tawarkan ini sebelum proxy
  residensial berbayar.
- **Tool SEO self-host berlabel "gratis, tanpa API berbayar" tetap bisa tidak berguna
  untuk niche judi** karena sumbernya Google/Reddit. Sebelum memasang tool,
  uji satu sumber dengan keyword niche target dulu; kalau kosong, tool tidak
  akan menghasilkan data walau UI-nya lengkap.
- **Jangan kirim laporan penuh setiap run.** Hash daftar keyword dan kirim
  hanya kalau berubah; kalau tidak berubah, keluar diam (`[skip]`).
