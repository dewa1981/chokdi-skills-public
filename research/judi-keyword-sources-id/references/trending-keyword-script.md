# Skrip laporan keyword judi harian (referensi implementasi)

Pola yang terbukti: tarik keyword → arsip → kirim ringkas ke Telegram →
render XLS akumulasi. Semua data tersimpan harian supaya tren bisa dibaca
setelah beberapa minggu.

## Alur harian

1. **Tarik** Bing + DuckDuckGo untuk daftar seed (lihat SKILL.md).
2. **Arsip** dua bentuk (keduanya wajib — yang satu untuk hitung, yang satu untuk XLS):
   - `snapshots/YYYY-MM-DD.json` → `{"date", "total", "keywords": [...]}` — snapshot penuh hari itu.
   - `keyword_archive.jsonl` → satu baris per keyword per hari `{"keyword", "date", "source"}`;
     tulis hanya keyword yang belum ada untuk tanggal itu supaya tidak ada baris dobel saat run ulang.
3. **Kirim ringkas** ke Telegram (kategori + maks 14 baris/kategori), tandai keyword baru `🆕`
   dibanding run sebelumnya.
4. **Render XLS** dari arsip, bukan dari hasil fetch, supaya file tetap utuh walau run hari itu skip.

## Bentuk XLS (3 sheet)

| Sheet | Kolom |
|---|---|
| Akumulasi | No, Keyword, Kategori, Pertama Terlihat, Terakhir Terlihat, Jumlah Kemunculan, Sumber, Panjang |
| PerTanggal | Keyword, Kategori, lalu satu kolom per tanggal berisi `1/0` (muncul hari itu) |
| Ringkasan | Kategori × tanggal + total unik |

Simpan dua salinan: `SEO_Keyword_Akumulasi_<YYYY-MM-DD>.xlsx` (riwayat) dan
`_LATEST.xlsx` (selalu terbaru, yang dikirim ke chat).

## Pitfall yang menelan waktu

- **`openpyxl` tidak ada di `/usr/bin/python3` dan python itu juga tidak punya pip.**
  Kalau pakai interpreter Hermes (yang punya openpyxl) di cron, tulis **path absolutnya**
  di wrapper — `python3` di cron bisa menunjuk interpreter lain.
- **Jangan hapus XLS lama saat bikin yang baru**; nama bertanggal = arsip.
- **Jangan cetak token/password ke stdout**; file sementara `chmod 600`, dihapus setelah dipakai.
- Kalau `digest` sama, keluar `[skip]` — tapi **arsip dan XLS tetap dibangun**
  (yang di-skip hanya kirim pesan, bukan pencatatan).

## Kirim ke Telegram

- Grup forum: `sendMessage`/`sendDocument` wajib `message_thread_id`; verifikasi
  nama topik sebelum mengirim (reply ke pesan bot memuat `reply_to_message.forum_topic_created.name`).
- Jangan hardcode thread dari tebakan — cari di memori (Hindsight) atau probe sekali lalu simpan.
- Setelah `sendDocument`, cek `result.message_thread_id` dan `is_topic_message` di respons
  sebagai bukti pesan benar-benar mendarat di topik itu.
