---
name: logo-asset-prep
description: Use when a logo must be cleaned or exported for web.
version: 1.0.0
author: chokdi_staging
license: proprietary
metadata:
  tags: [logo, image, webp, potrace, favicon]
  related_skills: [netlify-api-deploy, ai-image-editing, banner-artwork-text-composite]
---

# Logo Asset Prep (client/user logo → web-ready files)

## When to Use

- Bang/klien bilang **"logonya low quality"**, minta "bikin tajam tapi jangan diubah", atau mengirim
  file logo baru (JPG/PNG persegi dengan background) untuk dipasang di situs.
- Butuh set aset lengkap: favicon, `og:image`, logo header/footer, watermark.
- Sebelum swap logo di LP/panel → pakai skill ini dulu supaya file-nya transparan, ringan, dan benar.

Kelas pekerjaan: ada file logo dan hasilnya harus dipakai di situs/panel/banner. Output standar:
**SVG master (kalau bisa), PNG 512, WebP 192 (inline), favicon, OG 1200** — semuanya berlatar transparan.

## Aturan #1 — "logonya sama, jangan diubah" = JANGAN redraw dengan AI

Kalau permintaannya *"bikin kualitasnya bagus tapi logonya tetap sama"*, jalurnya **vector trace**
(bitmap → SVG), bukan image generation. Model gambar mengarang huruf: percobaan pada badge klien
menghasilkan "ANF TRANSPORT / AR RENTAL & VAN SERVICE" — kata **AUTO CAR hilang**, teks terbelah, dan
van-nya lenyap. Logo berisi teks = AI redraw hampir pasti merusak, dan kerusakannya halus (kelihatan
benar di thumbnail).

Urutan pilihan:
1. **Pemilik mengirim desain baru / high-res** → pakai itu apa adanya, cuma di-crop + di-resize (§ circle-crop).
2. **Cuma ada bitmap kecil** → vector trace (§ trace).
3. **Benar-benar bikin logo baru** → AI generate, lalu WAJIB baca ulang teksnya dengan `vision_analyze`
   (minta "read letter by letter") sebelum dipakai. Kalau teksnya penting, lebih aman render teks sendiri
   (PIL/SVG) di atas artwork tanpa teks.

## Lingkaran badge: crop transparan (bukan hapus background manual)

Badge bulat dengan background gelap: jangan tebak dengan magic-wand per piksel — hitung lingkarnya.

```python
bright = np.array(im).max(axis=2)                 # 70 = ring emas/van; background gelap di bawah itu
ys, xs = np.where(bright > 70)
cy, cx = ys.mean(), xs.mean()
r = np.percentile(np.hypot(ys-cy, xs-cx), 99.9)    # radius badge, abaikan glow liar

dist  = np.hypot(xx-cx, yy-cy)
alpha = np.clip((r - dist) / 1.8, 0, 1)           # feather ~2 px: tepi tidak bergerigi
alpha = (alpha * 255).astype(np.uint8)
```

- Crop ke kotak `cx±r, cy±r` lalu resize ke ukuran target — jangan resize dulu baru di-mask (tepinya jadi lunak).
- **Cek margin dulu.** Kalau badge menyentuh tepi frame, percentile radius ≈ ½ lebar gambar → mask memotong
  ring/glow-nya. Gejalanya: logo tampak "gepeng" di satu sisi. Kalau begitu, turunkan persentil (99.5)
  atau pakai deteksi ring emas (warna hangat + brightness tinggi) sebagai acuan.
- Selalu simpan file asli kiriman pemilik (`.jpg` mentah) — semua crop/ukuran dibuat ulang dari situ.

## Latar putih → transparan (lockup persegi/oval, bukan badge bulat)

Logo kiriman pemilik sering JPG di atas putih solid. Di header gelap putihnya harus dibuang — tapi JANGAN
hapus semua piksel terang: teks perak/putih di dalam emblem ikut lenyap.

```python
marked = src.convert("RGB").copy()                    # WAJIB RGB
for seed in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]:
    ImageDraw.floodfill(marked, seed, (255,0,255), thresh=20)
arr = np.array(marked)
bg  = (arr[...,0]>250)&(arr[...,1]<10)&(arr[...,2]>250)   # sentinel = background LUAR saja
alpha = np.where(bg, 0.0, 1.0)
```

- 🔴 `ImageDraw.floodfill` pada image mode **`L` tidak melakukan apa pun** — alpha tetap 255 di seluruh kanvas
  dan `getbbox()` mengembalikan ukuran penuh (gejala: "trim tidak memotong apa-apa"). Jalankan di RGB + warna
  sentinel, baru bikin alpha dari sentinel itu.
- **De-fringe jangan pakai `MinFilter`+blur buta** — hasilnya halo putih di background gelap. Hitung alpha hanya
  di **band ~3 px** di sekitar background: `a = clip((255-min(rgb))/(255-120), 0, 1)`, lalu unpremultiply
  `c = (c - 255*(1-a)) / a` hanya di piksel band. Teks perak di dalam emblem tidak ikut transparan karena tidak
  masuk band.
- Verifikasi: composite di atas **putih DAN gelap**, plus versi 40 px diperbesar 3× (halo paling kelihatan di situ).
  Jangan nilai cutout dari latar putih saja.
- Set ekspor minimal: `logo-header.png` tinggi 96 px (untuk slot 40 desktop / 32 mobile), `favicon-32.png`,
  `apple-touch-icon.png` 180, `icon-512.png` (dipakai juga untuk `"logo"` di JSON-LD). Simpan master transparan
  di folder kerja, **jangan** ikut ke folder deploy.
- Pasang semua permukaan sekaligus: `<link rel="icon">`, `<link rel="apple-touch-icon">`, `"logo"` di schema,
  dan drop-shadow CSS (lebih kuat di tema gelap). Sesudah logo masuk header, cek mobile
  `scrollWidth == clientWidth` — emblem + wordmark + 2-3 tombol kontrol gampang meluber di 390 px.

## Trace bitmap → SVG (potrace, dua layer warna)

```bash
apt-get install -y potrace librsvg2-bin      # rsvg-convert untuk render SVG → PNG
```

Pisahkan per warna (badge 3 warna: hitam, oranye, putih), trace masing-masing, lalu tumpuk
(orange di belakang, hitam di depan). Upscale 4× dengan `Image.LANCZOS` **sebelum** trace supaya kurvanya
halus; potrace pakai `-s --flat -u 10 --opttolerance 0.4`. Hasil wajar: 1–3 path per layer, SVG ~80 KB.

- **`potrace` menulis koordinat ×10 dengan `transform="translate(0,H) scale(0.1,-0.1)"`** — pertahankan
  transform itu saat menggabungkan beberapa SVG, kalau tidak layer kedua terbalik/tersebar.
- Bersihkan mask sebelum trace: `MaxFilter`/`MinFilter` (closing/opening) **hanya menerima ukuran GANJIL ≥3**;
  nilai genap → `ValueError: bad filter size`. Bungkus dengan helper `_odd(n)`.
- Verifikasi hasil trace dengan `vision_analyze` (minta "ada huruf pecah/artefak?") — jangan kirim ke user
  berdasarkan asumsi "pathnya banyak berarti bagus".

## Ukuran & berat

| File | Ukuran | Pakai di |
|---|---|---|
| `logo.svg` | vektor | sumber master, cetak, editing |
| `logo-512.png` | 512 px RGBA | kirim ke user, watermark, OG/cetak kecil |
| `logo_192.webp` (q92) | 192 px | **inline** di HTML (favicon + `<img>`); ~18 KB, bukan 180 KB |
| `og_logo.png` | 1200 px | `og:image`, share preview |

WebP mengalahkan palette-PNG untuk badge bergradasi (18 KB vs 51–74 KB, tanpa pecah). Empat salinan inline
× 18 KB ≈ 72 KB masih aman; empat salinan PNG 180 KB membuat halaman 1,7 MB.

## Verifikasi (wajib sebelum lapor)

1. Composite logo di **atas putih DAN di atas gelap** (`Image.alpha_composite`) → simpan dua JPG, lihat
   keduanya. Badge gelap di header putih dan di footer hitam punya masalah berbeda (white box vs hilang).
2. Render di ukuran **pemakaian sebenarnya** (header sering cuma 44–48 px) lewat headless browser,
   `deviceScaleFactor: 2`, lalu zoom: ring/teks masih terbaca? ada clipping?
3. **Buktikan logo yang live = file baru** (bukan build/cache lama): decode SEMUA data URI di HTML live,
   md5 byte-nya, bandingkan dengan md5 file sumber — semua titik harus satu hash yang sama.
   ```python
   import re, base64, hashlib
   h = open('/tmp/live.html').read()
   print({hashlib.md5(base64.b64decode(u)).hexdigest() for u in re.findall(r'data:image/\w+;base64,([A-Za-z0-9+/=]+)', h)})
   print(hashlib.md5(open('assets/logo_192.webp','rb').read()).hexdigest())
   ```
   Hash beda = build belum jalan / file belum ditimpa / deploy ke project lain.
4. Baru lapor: sebut file apa yang dipakai di permukaan mana, ukuran KB, dan hasil cek visual.

## Swap logo di situs yang sudah live (+ generator turunan)

Satu titik terlewat = dua versi logo beredar bersamaan. Urutannya:

1. Simpan sumber mentah kiriman pemilik ke folder aset, dan **backup** file lama sebelum ditimpa
   (`cp logo_192.webp logo_192.webp.bak-<stamp>`; sama untuk `logo_ring_512.png`, `og-logo.png`).
2. Jalankan `scripts/prep_logo.py` → 512 PNG / 192 WebP / OG 1200 transparan. Cek margin dulu: alpha di baris/kolom
   tepi ≈ 0 berarti ring tidak terpotong.
3. Timpa file yang dibaca build (sering satu `logo_192.webp` yang di-inline ke N tempat), rebuild, deploy.
4. Verifikasi hash (§ Verifikasi #3) di **semua host** — apex dan www.
5. **Sistem turunan wajib ikut**, bukan cuma web: generator banner/flyer biasanya menyimpan salinan logo sendiri.
   Timpa aset generator (mis. cron banner di container: `docker cp` + `chown hermes:hermes`), lalu bandingkan
   `md5sum` di dalam container dengan file lokal — dan cek hasil render berikutnya dengan `vision_analyze`.
6. Kalau prompt generator menyebut nama/wordmark logo, ubah teksnya juga (mis. 'ANF' → 'ANF88') — kalau tidak,
   model gambar terus mengarang wordmark lama walaupun file logonya sudah baru.

## Pitfalls

- **Jangan memperbesar logo di halaman demi keterbacaan.** Badge detail (ring + kendaraan + 2 baris teks) di
  44–48 px wordmark-nya sudah jadi blok; dinaikkan ke 56 px malah dibalas "kotaknya terlalu besar". Ukuran tampil
  = keputusan pemilik — kalau teks harus terbaca, sediakan teks brand di samping logo, jangan zoom badge.
- **Jangan menyebut bentuk kunci sebagai huruf.** Kepala kunci (key head) sering terbaca seperti "P" oleh
  model vision; itu artefak deskripsi, bukan salah tulis — jangan "memperbaiki" desainnya.
- **Pemilik mengirim beberapa varian tanpa instruksi** (mis. 3 badge berurutan): baca teks tiap varian lebih
  dulu (yang teksnya benar menang), pilih yang paling sesuai merek, **terapkan**, lalu tawarkan switch satu
  baris ("mau A atau B?"). Jangan balas dengan pertanyaan saja.
- **Jangan redesign** saat permintaannya kualitas/ketajaman. Mengganti artwork = perubahan merek yang tidak diminta.
- Ukuran tampil kecil bukan alasan membuat file kecil: sediakan 192–512 px supaya tetap tajam di retina.
- Kalau logo dipakai di banyak tempat (header, CTA, footer, favicon), ganti **semua** permukaan dalam satu
  build dan sebutkan daftarnya di laporan.

Script siap pakai: `scripts/prep_logo.py` (crop lingkaran → 512 PNG + 192 WebP + OG, plus preview putih/gelap).
