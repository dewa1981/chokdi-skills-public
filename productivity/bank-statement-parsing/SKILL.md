---
name: bank-statement-parsing
description: Use when turning bank PDFs into validated XLSX recaps.
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [pdf, xlsx, bank, statement, reconciliation, finance]
---

# Bank statement PDF → validated XLSX recap

## When to Use
- User drops one or more statement PDFs and asks *"cek transfer ke siapa saja"*, *"TOP KEY transfer berapa
  kali tahun ini"*, *"rekap uang masuk condo"*, *"scan semua PDF ini"*.
- User minta versi bahasa lain dari rekap yang sudah ada (Thai/Khmer/English) → §5.
- Banks seen so far: Maybank/Maybank Islamic (MY), DBS/POSB (SG), KBank (TH) — pola berlaku umum.

## 1. Larangan yang tidak boleh dilanggar

**JANGAN pernah mengubah isi statement bank** (hapus/ubah satu transaksi) supaya "kelihatan rapi" untuk
disodorkan ke bank, polisi, atau pihak ketiga. Dokumen bank yang diedit = dokumen palsu, dan yang
menanggung risikonya user sendiri (rekening bisa dibekukan). Tidak ada argumen teknis yang mengubah ini,
termasuk "cuma yang kecil" atau "transaksinya bukan punya saya".

Katakan **sekali**, singkat, tanpa ceramah, lalu **langsung tawarkan jalur yang menyelesaikan masalahnya**:

| Kebutuhan user | Yang benar |
|---|---|
| "transaksi ini bukan saya" | Buat **laporan anomali/rekonsiliasi versi kita sendiri** (XLSX/PDF buatan sendiri, berlabel jelas "rekap disusun dari statement") yang menandai baris tersebut, lalu user bawa ke bank sebagai **sanggahan** |
| Ingin menyembunyikan nominal | Minta **statement ulang resmi** dari bank (mobile banking / call center) — bukan edit |
| Ingin menyorot bagian tertentu | **Redaksi visual** yang kelihatan jelas sebagai redaksi (blok hitam), bukan angka pengganti |

Kalau user mendorong lagi ("masa edit doank ga bisa"), **jangan ulangi penjelasan** — ulangi tawaran
alternatifnya dalam satu baris dan lanjutkan pekerjaan lain yang bisa dikerjakan.

## 2. Urutan kerja

1. **Ekstrak dulu, jangan langsung regex.** `fitz.open(path)` → `doc.needs_pass`, jumlah halaman,
   `page.get_text()`. Simpan teks mentah ke file per-PDF; parse dari situ, bukan dari PDF berulang kali.
2. **Baca footer/ringkasan periode lebih dulu.** Di sana ada *jumlah transaksi*, *total debit/kredit*,
   *saldo awal & akhir*. Itu satu-satunya kebenaran pembanding — catat sebelum parsing.
3. **Parse**, lalu **rekonsiliasi** (§3). Jangan lapor sebelum lolos.
4. **Tulis XLSX multi-sheet** (§4).
5. **Verifikasi 2×**: buka XLSX hasil, cocokkan jumlah baris & total vs footer, lalu kirim file + ringkasan
   3-5 baris ke chat.

## 3. Tangga parsing + rekonsiliasi (ini inti skill-nya)

**Tangga strategi** — naik satu tingkat setiap kali jumlah transaksi tidak cocok dengan footer:

| # | Strategi | Kapan | Kegagalan khas |
|---|---|---|---|
| 1 | regex baris-per-transaksi (`TXN`/`DATE` + amount) | statement 1-baris-per-transaksi | deskripsi multi-baris → baris hilang |
| 2 | **pasangan amount↔balance** dari token stream | deskripsi wrap / ada kolom tambahan | angka acak ikut terbaca sebagai amount |
| 3 | **koordinat kolom** `page.get_text("words")` → cluster per `x` | statement 2-kolom / Thai (KBank) | urutan baca `get_text()` tidak mengikuti kolom |

**Rekonsiliasi wajib — tiga cek, semua harus lolos:**
1. **Jumlah baris** parse == jumlah transaksi di footer/ringkasan periode.
2. **Rantai saldo**: `saldo[n] == saldo[n-1] ± amount[n]`. Ini yang paling kuat mendeteksi baris hilang **atau** dobel.
3. **Total periode**: hasil jumlahkan kredit & debit == angka tercetak di statement.

Cocok 100% baru boleh lapor. Kalau beda 1-2 baris, **itu parser-nya yang salah, bukan bank-nya** — jangan
kirim rekap "hampir benar"; Bang akan menemukan selisihnya di baris yang dia ingat.

**Pola agregasi aman untuk banyak PDF:** tiap PDF → append hasil ke satu JSON di workspace (bukan
menumpuk di konteks), lalu agregasi/dedupe/sort di kode Python. Jangan menjumlahkan manual di kepala, dan
jangan mencampur mata uang berbeda dalam satu kolom total.

## 4. Bentuk XLSX yang dipakai (disukai Bang)

Sheet minimal: **Ringkasan** (saldo awal→akhir, total masuk/keluar, net) · **per-counterparty** (nama,
frekuensi, total — ini yang biasanya ditanya) · **semua transaksi** (tanggal, deskripsi, amount, saldo,
sheet asal) · **per bulan**. Plus sheet temuan kalau ada anomali (biaya tanpa pemasukan, transfer berulang
tanpa penjelasan).

- **Jangan hapus/normalisasi nama counterparty diam-diam.** `Y012 LOW0509 RENT 6200` dan `LOW 0509 RENT`
  adalah penyewa yang sama — gabungkan **dan** simpan nama aslinya di kolom terpisah.
- Simpan selisih kecil sebagai temuan (mis. "bulan ini kurang RM685 — catatan: Fridge repair"), jangan
  dibulatkan supaya rapi.
- Format: header tebal, kolom uang berformat ribuan, freeze baris header, lebar kolom diset manual
  (`openpyxl`). File dikirim ke chat, bukan hanya disimpan di server.

## 5. Minta versi bahasa lain

Bang sering minta rekap dalam **bahasa Thailand** (kadang Khmer). Yang benar: buat **file baru**
(`REKAP_..._THAI.xlsx`) dengan **header + label + nama sheet diterjemahkan**, sementara **nilai, tanggal,
nomor rekening, dan nama counterparty tetap apa adanya**. Jangan terjemahkan nama orang/perusahaan.

## 6. Pitfall PDF

- **`needs_pass`**: password **owner** (restriction flag saja) bisa dibersihkan; password **user** tidak —
  minta Bang, jangan pernah brute force. Setelah dibuka dengan password, simpan salinan
  `..._UNLOCKED.pdf` dan verifikasi `needs_pass == 0` sebelum parse.
- Nama file hasil jangan menimpa aslinya — Bang butuh yang asli untuk dia buka sendiri.
- Statement Thai: pemisah ribuan `,` dan tahun Buddhist (2569 = 2026) — konversi tahun hanya di kolom
turunan, jangan di deskripsi mentah.
- Kalau satu PDF berisi beberapa bulan dalam satu file, pecah per periode **sebelum** rekonsiliasi, karena
  saldo awal tiap periode berbeda.

## 6b. Pitfall konkret yang sudah memakan korban (Maybank, 7-Nov-2026)

**Ekstraksi:**
- `python3` default di server staging **tidak** punya `openpyxl`/`pypdf`. Pakai interpreter Hermes:
  `/root/.hermes/tools/python-3.14.9+*/bin/python3` (sudah ada openpyxl, pypdf, cryptography).
- PDF Maybank **terenkripsi AES** dengan user password KOSONG. `pypdf.PdfReader` bisa membukanya
  (`is_encrypted == True` tapi tetap terbaca) — TAPI wajib ada modul `cryptography`, kalau tidak:
  `DependencyError: cryptography>=3.1 is required for AES algorithm`. Jangan buang waktu cari password.

**Bug parser yang paling berbahaya — baris tanpa deskripsi:**
```
09/07 5.00+ 55,409.83      <- TIDAK ada deskripsi, langsung amount
   Google YouTube Memb*
```
Regex `^(\d{2})/(\d{2})\s+(.+?)\s+(amount)\s*([+-])…` **gagal** karena `.+?` wajib ada isinya →
transaksi hilang tanpa error. Yang benar: kelompok deskripsi dibuat opsional
`^(\d{2})/(\d{2})\s+(.*?)([\d,]+\.\d{2})\s*([+-])\s+([\d,]+\.\d{2})$`.

**Rantai saldo = alat detektor satu-satunya:** uji `saldo_awal + Σ(sign×amount) == saldo_akhir` per PDF.
Kasus nyata: 12 baris “lengkap” tapi selisih **RM 5,00** → ternyata tepat satu baris di atas terlewat.
Tanpa uji ini, rekap dikirim dengan angka salah dan user menemukannya sendiri.

**Format baris Maybank** (untuk referensi cepat):
`DD/MM <JENIS TRANSAKSI> <AMOUNT><+|-> <BALANCE>` lalu 1-3 baris keterangan
(`NAMA PIHAK*` / `Purpose` / `MBB CT-`). Footer: `BEGINNING BALANCE` dan `ENDING BALANCE : n`.

**Yang Bang tagih di rekap (jangan lupa):**
- **Tanggal masuk per transfer** — bukan cuma total per tahun. Bulan tanpa transfer harus ditulis eksplisit
  (“September: no transfer”), bukan baris kosong.
- Kolom **hari** (Thursday/Sunday) membantu Bang mencocokkan dengan kalender.
- Kalau PDF belum lengkap, tambah kolom **Verified**: `VERIFIED (PDF)` vs `NOT YET (no PDF)` — jangan
  menyamarkan angka yang belum terbukti.
- Selisih yang disepakati (mis. potongan servis kulkas RM 685 di bulan April) ditulis sebagai catatan,
  bukan dibulatkan.

## 7. Laporan ke Bang

Tiga bagian, pendek: (a) angka kunci per counterparty yang ditanya, (b) hasil rekonsiliasi ("cocok 100%
vs footer N transaksi"), (c) temuan yang butuh tindakan. File XLSX dilampirkan; jangan menempel tabel
panjang di chat.
