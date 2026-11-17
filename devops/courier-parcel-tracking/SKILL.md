---
name: courier-parcel-tracking
description: Use when tracking a parcel/resi or making a resi cron.
version: 1.0.0
author: chokdi_staging
license: internal
metadata:
  hermes:
    tags: [tracking, courier, gdex, cron, telegram, notification, cdp]
    related_skills: [headless-browser-ops, telegram-notification-scripts, hermes-cron-scripts]
---

# Courier Parcel Tracking + Resi Monitor Cron

Lacak resi kurir dari server (tanpa browser app), lalu jadikan cron yang notif HANYA saat status berubah.
Berlaku untuk GDEX, J&T, Ninja Van, PosLaju, dan kurir lain dengan halaman tracking publik.

## When to Use

- Bang kirim **foto waybill/resi** dan tanya "kapan sampai" / "cek dong".
- Bang minta **cron monitor resi** ("cek tiap N jam, kabarin kalau berubah").
- Resi dari kurir apa pun yang punya **halaman tracking publik berbasis querystring**.

## ⛔ ATURAN GERBANG: konfirmasi nomor resi ke Bang SEBELUM membuat apa pun

Nomor resi panjang (12–14 digit) **tidak boleh** diambil dari OCR/pembacaan gambar dan langsung dipakai.
Terbukti 2-Okt-2026: gambar dibaca sebagai `MY3737177280` (12 karakter), padahal yang benar
`MY37377177280` (13 karakter) — **satu digit hilang**. Akibatnya cron memantau nomor yang salah, state
file menyimpan status nomor salah, dan notif yang dikirim juga salah nomor.

**Jumlah karakter adalah alat murah untuk memvalidasi.** Baca nomor **dua kali**, hitung panjangnya, dan
**cetak nomor itu ke Bang untuk dikonfirmasi** — baru buat script/cron. Kalau Bang sudah memberi potongan
angkanya (mis. `37377`), cocokkan dengan hasil bacaan sebelum lanjut.

Konsekuensinya saat sudah terjadi: perbaiki **semua** yang menyimpan nomor lama — script, **state file**, dan
**nama job cron** — bukan hanya variabel `AWB`. Verifikasi dengan `grep -rn` atas nomor lama (harus nol hasil).

## Aturan #1: waybill TIDAK memuat tanggal pickup

Waybill GDEX (dan sejenisnya) hanya mencetak **`Print Date`** + kolom **`RECEIVED BY <KURIR> STAFF → DATE & TIME:`** yang **KOSONG** sebelum kurir scan.

| Yang dilihat | Artinya |
|---|---|
| `Print Date` terisi, kolom staff kosong | resi **baru dicetak**, paket **belum diserahkan** |
| tracking publik: `no records found` | **konsisten** dengan di atas — belum di-scan |

**Jangan pernah menjanjikan ETA dari `Print Date`.** Yang menentukan ETA adalah **scan pertama kurir**. Katakan apa adanya: "resi baru dicetak, belum masuk sistem kurir".

⚠️ Resi ter-print tapi `no records` **>24 jam** = sinyal untuk follow-up ke pengirim (kadang resi dicetak tapi paket belum benar-benar dikirim). Sebut ini ke Bang — jangan diamkan.

## GDEX — endpoint tracking publik (terbukti 2-Okt-2026)

**Form-nya GET biasa**, bukan AJAX. Hasilnya di halaman `/tracking/`:

```bash
curl -s -4 -L --max-time 25 \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" \
  "https://gdexpress.com/tracking/?consignmentno=MY3737177280"
```

- `-4` **wajib** (IPv6 trap khas server kita).
- **User-Agent browser wajib** — tanpa itu respons bisa beda.
- `consignmentno` = nomor resi. Radio form (`quform_1_16`) bernilai `CN` (myGDEX Prime) / `RN`.

### Bentuk halaman form vs halaman hasil (beda!)

| URL | Isi |
|---|---|
| `/our-business/delivery/tools-references/tracking/` | form-nya (Quform + Vue) |
| `/tracking/?consignmentno=<AWB>` | **halaman hasil** (ini yang dibaca script) |

Submit manual ke URL form dengan querystring `?quform_1_16=CN&quform_1_3=<AWB>` **GAGAL** — balas `This field is required`. Jadi **jangan pakai form-nya**; langsung tembak URL hasil.

### Ekstraksi status

Buang tag → ambil potongan antara `Consignment Number:` dan `Frequently Asked Questions`:
```bash
sed 's/<[^>]*>/ /g' | tr -s ' \t\n' ' ' \
  | grep -oE 'Consignment Number:.*?(Frequently Asked Questions|About Us)' | head -1
```
Hasil kalau belum ada: `Consignment Number: <AWB> Sorry, no records found for this Consignment No. <AWB>`.

## Kurir lain — cara menemukan endpoint-nya dalam 1 menit

**Pola umum:** form tracking sering **GET ke halaman hasil** dengan querystring, bukan AJAX. Cara memastikan **tanpa menebak** — sniff network lewat CDP (lihat bagian CDP di bawah): pasang `Network.enable`, submit form, lalu cetak semua URL yang mengandung `track|consign|awb|api`.

🚫 **Jangan** buang waktu pada: `wp-admin/admin-ajax.php` (302), komponen `.vue` di `wp-content/plugins/*/resources/components/` (404), atau menebak `/api/track` — semua pernah dicoba di GDEX dan gagal.

**Kalau halaman butuh JS berat:** jalankan Chrome + CDP (bagian bawah), lalu baca `document.body.innerText`. **Kalau tidak butuh JS:** cukup curl (jauh lebih murah) — tes curl DULU sebelum menyalakan browser.

## Cron monitor resi — pola anti-spam (state file + notif saat berubah)

Template lengkap: `templates/resi_monitor.sh`. Prinsip yang wajib diikuti:

1. **State file = status TERAKHIR, dan notif hanya kalau BEDA.** Tanpa ini Bang di-spam tiap tick.
2. **Gagal fetch → exit 0 DIAM** (jangan kirim notif error palsu). Cek `[ -z "$BODY" ]`.
3. **`no_agent=true` + `deliver=local`** — script yang kirim notifnya sendiri via Telegram API, jadi output stdout kosong = tidak ada pesan (watchdog pattern).
4. **Jalankan SELALU lewat wrapper** dengan `flock` supaya tidak numpuk.

### Dua lapis verifikasi (keduanya wajib sebelum lapor "selesai")

| # | Tes | Ekspektasi |
|---|---|---|
| 1 | run manual pertama | status terbaca + notif terkirim (`"ok":true`) |
| 2 | run manual kedua | log: `sama — tidak kirim notif` |
| 3 | `cronjob action=run` | job result `ok`, output **`silent (empty output)`** |

Tes #3 = bukti anti-spam bekerja **di engine cron**, bukan cuma manual. Sebut hasil ketiganya saat melapor.

### Daftar cron — PITFALL script path

```bash
cp /opt/data/scripts/<name>.sh /root/.hermes/scripts/<name>.sh   # SYMLINK DITOLAK
```
⚠️ `cronjob_manage` menolak **symlink** dengan error `Script path escapes the scripts directory via traversal` — padahal path-nya benar. **Pakai `cp`, bukan `ln -s`**, lalu pastikan `chmod +x`.

⚠️ **Nama job cron juga menyimpan nomor resi** — kalau nomor diperbaiki, update `name` job juga
(`cronjob action=update`), bukan hanya variabel di script. Nama yang salah bikin laporan menyesatkan
berbulan-bulan kemudian.

Cron: `schedule="every 4h"`, `no_agent=true`, `deliver="local"`, `script="<name>.sh"`.

## Kontrol Chrome lewat CDP dengan `websocket` (tanpa install Playwright)

Dipakai kalau: butuh render JS / sniff network, **dan** Playwright/Selenium tidak terpasang di server.

**Cek dulu apa yang tersedia** (jangan install dulu):
```bash
ls /root/.cache/ms-playwright/chromium-*/chrome-linux64/chrome     # binary sering sudah ADA
/usr/local/lib/hermes-agent/venv/bin/python -c "import websocket; print('OK')"   # driver CDP
```
Di staging (2-Okt-2026): Chromium **ada**, `websocket`+`websockets`+`requests` **ada**, Playwright/Selenium **tidak ada** → jalur termurah = CDP manual, **nol instalasi**.

```bash
# launch (background=true, JANGAN nohup/& — ditolak lifecycle guard)
/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome \
  --headless=new --no-sandbox --use-gl=swiftshader --enable-unsafe-swiftshader \
  --remote-debugging-port=9222 --user-data-dir=/root/.config/chromium --window-size=1280,900 about:blank
curl -s http://127.0.0.1:9222/json/version | grep Browser     # verifikasi
```

Driver minimal (websocket-client → `id`/`method`/`params`, tunggu balasan dengan `id` sama, kumpulkan event `method`):
```python
self.ws = websocket.create_connection(ws_url, timeout=60, suppress_origin=True, max_size=200*1024*1024)
# ws_url dari http://127.0.0.1:9222/json/list  ->  pilih tipe "page"
```

- **`suppress_origin=True`** wajib, kalau tidak Chrome 151 menolak handshake.
- Pakai `Runtime.evaluate` dengan `returnByValue=True, awaitPromise=True` untuk isi form & baca `document.body.innerText`.
- **`Network.enable` sebelum `Page.navigate`** → semua request tertangkap; ini cara menemukan endpoint asli (dan di GDEX inilah yang mengungkap bahwa form-nya GET ke `/tracking/?consignmentno=`).
- `Page.captureScreenshot` butuh **`--use-gl=swiftshader`**; `--disable-gpu` bikin timeout (lihat `headless-browser-ops`).

## Pitfalls

- **Jangan baca nomor resi hanya dari OCR barcode.** Cetakan 12-digit bisa ambigu — kalau **luar biasa penting** (nomor HP, rekening, resi), konfirmasi ke Bang dulu sebelum menyimpulkan hasil tracking. Lihat **ATURAN GERBANG** di atas — pernah terjadi satu digit hilang dan cron memantau nomor salah.
- **Bedakan "no records" dari "gagal fetch".** "no records" = jawaban sah (belum di-scan). Body kosong/timeout = gagal → jangan tulis apa pun ke state file.
- Notif resi masuk ke grup notifikasi (staging: `-1004350623808`, token `/root/scripts/.tg_bayar_token` chmod 600) — **jangan taruh token di chat/log/script**.
- `Runtime.evaluate` bisa mengembalikan `None` kalau elemen belum ada — pakai selector `#id` langsung dan periksa hasilnya, jangan asumsikan sukses.
- Kalau hasil tracking di layar bilang "no records" padahal Bang yakin paket sudah dikirim → sarankan cek dari **HP Bang** (IP residensial) sebelum menyalahkan script; sekaligus sarankan follow-up ke pengirim kalau >24 jam.
