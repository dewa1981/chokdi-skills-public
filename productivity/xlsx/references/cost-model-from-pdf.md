# Model biaya dari dokumen sumber (PDF proposal / tarif / kontrak)

Dipakai kalau Bang kirim PDF penawaran atau daftar tarif lalu minta "bikin xls:
satu orang kena berapa per bulan, kantor kena berapa per bulan".

## Urutan kerja

1. **Ekstrak teks dulu**: `python3 -c "import pymupdf;d=pymupdf.open(p);..."`.
   `pdftotext` bisa tidak terpasang dan hanya menghasilkan output kosong tanpa
   error — kalau hasilnya kosong, langsung pakai `pymupdf` (`fitz`), jangan bilang
   PDF-nya tidak terbaca.
2. **Tabel penting baca dua kali**: render halaman jadi PNG lalu baca dengan
   `vision_analyze`, khususnya halaman tarif, gaji, dan simulasi.
   `pix = page.get_pixmap(dpi=110); pix.save('hal4.png')` → minta vision membaca
   baris demi baris. Teks hasil ekstraksi berderet tanpa kolom; vision yang
   menjaga angka tidak tertukar kolom. Selisih satu baris tarif = seluruh model
   salah.
3. **Pisahkan tarif dari total.** Satu tabel `TARIF` berisi rate (persen, fee per
   unit, fee tetap) yang dipakai sebagai konstanta; setiap total dihitung ulang
   dari rate itu. Jangan salin angka total dari PDF sebagai angka mati.
4. **Rekonsiliasi terhadap total dokumen** sebagai uji kebenaran: kalau hitungan
   sendiri == total PDF, model benar. Kalau beda sedikit (mis. pembulatan deposit),
   catat sebagai temuan di sheet CATATAN — jangan diam-diam dibulatkan supaya cocok.
5. **Verifikasi rumus** dengan `scripts/verify_formulas.py` sebelum dikirim.

## Bentuk workbook default: SATU sheet, jawab pertanyaannya langsung

Default = **satu sheet ringkas**, bukan laporan lima sheet. Kalau dokumen tarifnya USD,
semua angka USD; jangan tambah kolom rupiah/harian yang tidak diminta. Bentuk yang lolos:

1. Blok 1 — **biaya per unit per bulan**: rincian 4-6 baris (gaji pokok, kontribusi
   employer, fee vendor, persen fee) + TOTAL, lalu dua baris "dari total itu: uang ke
   unit" dan "dari total itu: profit/fee vendor".
2. Blok 2 — **tabel per jumlah unit**: 1/5/20/50 dalam kolom, sel jumlah unit **hijau
   (bisa diubah)**, baris total per bulan, profit per bulan, profit per tahun.
3. Blok 3 — **biaya pertama kali setup**: fee sekali + biaya per unit sekali + deposit,
   TOTAL cash out di awal, plus satu baris "tanpa deposit = uang yang benar-benar hilang".
4. Blok 4 — **jawaban singkat** 3-4 baris: per unit/bulan, profit/unit, setup awal,
   setup tanpa deposit.

Itu cukup. Bang menilai dari "berapa yang harus saya keluarkan, berapa profit saya, dan
berapa modal awal" — bukan dari kelengkapan tabel.

**Versi rinci lima sheet hanya kalau diminta eksplisit** (mis. "bikinin detail/lengkap",
analisa tahun ke-2, atau dokumennya akan dikirim ke klien). Kalau Bang bereaksi "makin
liat makin pusing" terhadap versi rinci, jangan pertahankan strukturnya — rebuild dengan
susunan default di atas, dan pertahankan hanya angka-angkanya.

Kalau nanti versi rinci diminta, susunannya: `RINGKASAN` → `PER_<UNIT>_BULANAN` (sampai
per hari) → `<ENTITAS>_BULANAN` (deposit & cash-out) → `SKENARIO` (tahun 1 vs 2) →
`CATATAN` (asumsi + temuan bernomor).

## Aturan isi

- **Satu mata uang mengikuti dokumen sumber.** USD pada proposal USD; rupiah hanya bila
diminta. Kalau dua mata uang dipakai, kurs ditulis eksplisit sebagai sel asumsi yang bisa
diubah — jangan pernah tulis rupiah tanpa menyebut kursnya.
- **Tandai uang siapa**: bedakan fee vendor dari uang yang benar-benar diterima orang
  (gaji, potongan, take-home) — Bang menilai keputusan dari proporsi itu.
- **Sel input beda warna** dari sel hasil rumus, dan beri catatan singkat "boleh diubah".
- Angka uang tanpa desimal bila nilainya besar (`"$#,##0"`), dua desimal untuk tarif
  (`"$#,##0.00"`); total di-bold + fill; `freeze_panes` di header.
- Angka aneh di dokumen (deposit yang tidak pas dengan rumusnya, "per unit" yang
  membagi fee tetap) masuk catatan sebagai temuan bernomor — itu yang bikin Bang
  percaya modelnya, bukan tabelnya yang rapi.

## Versi bahasa lain = rebuild dari generator, jangan edit sel

Simpan generator sebagai file Python (`build_<model>.py`) berisi konstanta tarif di atas
script, lalu untuk permintaan "translate to english" cukup ganti label di generator dan
jalankan ulang ke nama file lain (`<MODEL>_SIMPLE_EN.xlsx`). Jangan mengedit sel satu per
satu: rebuild menjamin angka identik, dan hasilnya diverifikasi ulang otomatis. Sesudah
rebuild, jalankan verifikasi rumus lagi dan bandingkan angka kunci dengan versi lama
(cukup 3-5 sel: total per unit, profit, total setup).

## Pitfall

- Jangan taruh total sebagai angka statis di sheet ringkasan sementara sheet lain
  pakai rumus: begitu Bang ubah jumlah unit, dua tempat jadi tidak sinkron.
- Kalau dokumen menulis "3 bulan biaya operasional", cek basisnya (gaji saja atau
  gaji + fee + biaya sekali) — ambigu, jadi hitung dengan basis yang paling masuk
  akal dan sebutkan di CATATAN.
- Fee per transaksi (persen) dihitung dari nilai yang ditagihkan, bukan dari nilai
  sebelum markup; pastikan basisnya sama dengan angka di simulasi dokumen.
