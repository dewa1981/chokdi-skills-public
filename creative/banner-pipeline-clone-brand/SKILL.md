---
name: banner-pipeline-clone-brand
description: Use when cloning a banner cron pipeline to another brand.
---

# Clone pipeline banner (1 brand/hewan → brand/hewan lain)

## QC WAJIB — pakai Gemini Decisions (JANGAN Jev)

Saat meng-clone pipeline, tahap QC **WAJIB** tetap pakai `gemini-decision-1` (Gemini Decisions API),
**BUKAN** TypeSafe Jev. Terbukti 12-Nov-2026: Gemini 540px + 25 pertanyaan = **0,93 dtk /
Rp 4,24 / 5-dari-5 BENAR**; Jev 200px + 4 pertanyaan = **Rp 20 dan SALAH**, 240px = HTTP 400
`max_tokens_exceeded`.

Resep + cara baca: `skill_view(name='banner-engine-selection', file_path='references/qc-banner-gemini-decisions.md')`.
Jangan clone pipeline lama yang masih memakai Jev untuk QC gambar — hasilnya salah dan lebih mahal.

Dipakai mis. Dog House → Cat House: copy semua script banner + ganti prompt, lalu cron sendiri.

## Langkah yang terbukti
1. **Inventaris dulu**: `ls /opt/data/scripts | grep -i <brand>` dan `ls -la /opt/data/prompts_<brand>_banner/{,assets,out}`.
   Script produksi biasanya satu file mandiri (`cron_banner_<brand>_v6.py`) + wrapper `.sh`; sisanya iterasi dev.
2. **Copy + substitusi mekanis** pakai script converter (bukan edit manual 29 file): rename file `dog→cat`,
   substitusi frasa panjang DULU (`Premium Dog House`→`Premium Cat House`, `DOGHOUSE`→`CATHOUSE`, `prompts_dog_banner`),
   baru kata tunggal (`puppies→kittens`, `dogs→cats`, `dog→cat`), plus Khmer (ឆ្កែ→ឆ្មា) & Mandarin (犬只→猫咪).
   Konverter disimpan: `/opt/data/scripts/make_cat_banner_from_dog.py`.
3. **Ganti blok daftar ras** — substitusi kata merusak isi list (`Golden Retriever puppy`→`kitten`).
   Ganti seluruh blok `CATS = [...]` via regex `^CATS = \[.*?^\]` (re.S|re.M) dengan daftar ras baru.
4. **Verifikasi**: `grep -rniE "\bdog|puppy|anjing"` di semua script baru harus kosong (kecuali file converter).
5. **Folder kerja baru**: `/opt/data/prompts_<brand>_banner/{assets,out}`; copy `owner_ref.jpg`; state/manifest JANGAN dicopy (rotasi mulai bersih).
6. **Tes 3 variasi** dengan parameter dipaksa (pos / jumlah hewan / pose / baju / kolom teks) — jangan andalkan random.
7. **Cron**: file `/etc/cron.d/<nama>` (write_file DITOLAK untuk /etc → pakai `terminal` + printf), jadwal digeser 1 menit
   (`1-59/3` vs `*/3`) supaya tidak start barengan cron lain di akun ChatGPT yang sama.
8. **Kirim Telegram**: gate env `SEND_TG` di wrapper; default 0 sampai Bang tentukan grup/thread.
   Chat id + thread: COPY dulu `state.db` ke scratch (jangan buka live), lalu
   `SELECT chat_id,thread_id,display_name FROM sessions ORDER BY started_at DESC`.

## Menambah & memutar baju (owner bilang "bajunya itu-itu aja / kehabisan baju")

Pipeline hewan punya satu daftar `TRAD_WORLD` berisi `(tag, deskripsi)` + `OUTFITS` (fashion/cosplay).
Kalau owner menyebut kawasan ("Timur Tengah", "Amerika Selatan"), tambahkan **satu set lengkap**
negara kawasan itu sekaligus (bukan 1–2 contoh), lalu sebutkan daftar negaranya di laporan.

1. Backup dulu: `cp <script> <script>.bak-sa-$(date +%Y%m%d_%H%M%S)`.
2. Sisipkan entri baru **sebelum penutup list** (anchor `\n]\n\nOUTFITS = [`) lewat script patch Python,
   bukan `sed` per baris — blok multi-baris mudah kehilangan koma/penutup dan script langsung mati.
   Patch **kedua** script (doghouse & cathouse) dalam satu jalan; keduanya punya list yang sama.
3. `py_compile.compile(path, doraise=True)` setelah patch. Syntax error di sini = cron berhenti
   mengirim **tanpa alarm**, baru ketahuan dari grup yang sepi.
4. Verifikasi dari file hasil, bukan dari niat: hitung tag per prefiks kawasan (`br-`, `pe-`, `mx-`,
   `sa-`, `ae-`, …) lalu cetak daftarnya. Angka "40 → 59 baju" yang boleh dikutip ke owner hanya
   boleh datang dari hitungan ini.
5. **Tambahkan anti-ulang di `pick_outfit`.** `random.choice` boleh mengembalikan baju yang baru saja
   dipakai, dan owner membacanya sebagai "bajunya habis". Buang kandidat yang ada di
   `state["outfit_recent"][-8:]`, fallback ke daftar penuh kalau semua tersaring — jangan sampai
   list kosong membuat `random.choice([])` melempar IndexError di tengah cron.
6. Render 1 banner nyata per pipeline sebagai bukti, dan sebut baju yang keluar di caption.

**Footer caption wajib seragam** di semua pengirim hewan: pembuat + engine + IP,
contoh `🤖 Sule234 pakai ChatGPT Plan (Codex OAuth) yang bikin foto ini (IP <ip>)`. Jangan menulis
"ChatGPT Plus" — owner mengoreksi kata itu; engine-nya Plan/Codex OAuth.

## Pitfall yang sudah kena
- **Posisi vs kolom teks bentrok**: minta subjek KANAN + teks KANAN → model taruh subjek di KIRI. Paksa kolom teks
  berlawanan dengan posisi subjek (`pos==left → text_col=right`, dst). Bug ini ADA JUGA di pipeline lama.
- **Jumlah hewan meleset** (minta 2, keluar 4): tambah baris `ABSOLUTE COUNT RULE ... EXACTLY {n} ... count one by one`
  setelah baris placement.
- **Kata "dog" jangan dipakai di prompt negatif** versi cat ("no puppy, no dog") — bikin grep verifikasi kotor; pakai
  "or other animal of any kind".
- **Lock**: test runner pakai flock BLOCKING di lock global (`/opt/data/prompts_dog_banner/.lock`), cron pakai lock project sendiri;
  dua pipeline terbukti bisa jalan paralel di akun ChatGPT yang sama (dog total naik sambil cat jalan).
- **Bahasa Khmer** sering keluar pseudo-Khmer (AI). Solusi kalau Bang minta rapi: overlay teks Khmer asli pakai PIL setelah generate.
- Render 1 banner ~3-4 menit; cron 3 menit berarti hampir selalu overlap → wajar ada `[skip]` kalau pakai lock yang sama.
- `sed` untuk ubah cron bisa merusak komentar panjang; lebih aman tulis ulang file utuh dengan `printf`.

## Verifikasi wajib sebelum lapor
- `grep -cE "^OK: .*<BRAND>_v6"` di cron log (jumlah banner jadi), `grep "^SENT mid="` (jumlah terkirim),
  dan cek cron lain tetap jalan (`tail` log-nya + total naik).
- Vision check minimal 1 banner hasil cron: hewan benar, posisi benar, brand di crest benar.
