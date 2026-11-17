---
name: fill-flat-pdf-form
description: "Isi PDF formulir datar (non-AcroForm) via overlay koordinat."
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [pdf, pymupdf, form, overlay, insurance, verification]
    category: productivity
    related_skills: [pdf, ocr-and-documents, image-text-extraction]
---

# Mengisi PDF Formulir Datar (bukan AcroForm)

## When to Use

User mengirim PDF formulir resmi (asuransi, bank, imigrasi) dan minta diisikan, tapi PDF-nya
**tidak punya widget AcroForm** (teksnya ada, field-nya bukan form isian).

Jangan pakai skill ini kalau: form-nya AcroForm asli (pakai skill `pdf` + `pdf_fill_form.py`),
atau PDF-nya hasil scan tanpa text layer (pakai skill `ocr-and-documents`).

Cek dulu sebelum memilih metode:

```python
import pymupdf
d = pymupdf.open(src)
n = sum(len(list(pg.widgets())) for pg in d)
print(n, d.is_form_pdf)   # 0, False  -> form datar
```

- `n > 0` -> pakai `pdf_read.py --fields` + `pdf_fill_form.py` (skill `pdf`).
- `n == 0` -> **bukan** AcroForm. Kalau ada text layer, JANGAN pakai OCR dan JANGAN pakai
  nano-pdf (itu untuk prompt natural-language). Pakai resep overlay di bawah.

## Resep: overlay teks di koordinat (pymupdf)

1. **Temukan koordinat field dari label, bukan dari tebakan.** Ambil kata+bbox, filter kata kunci:

   ```python
   pg = d[0]
   for w in pg.get_text("words"):        # (x0, y0, x1, y1, teks, block, line, word)
       if any(k in w[4] for k in ["Policy", "Owner", "IC", "Email", "H/P"]):
           print(f"{w[4]:18} x0={w[0]:7.1f} y0={w[1]:7.1f}")
   ```

   Nilai diisi di **kanan** label: `x = label_x1 + ~7`, `y_baseline = label_y0 + 6.5`.
   Cek pasangan label kiri/kanan (mis. `Policy No :` kiri x=29, `Date :` kanan x=357) supaya
   kolom kiri tidak menabrak kolom kanan.

2. **Cari kotak centang** (kotak vektor, bukan glyph `☐`):

   ```python
   for dr in pg.get_drawings():
       r = dr["rect"]
       if 8 < r.width < 14 and 8 < r.height < 14:
           print(f"kotak: x={r.x0:.1f} y={r.y0:.1f}")
   ```

   Centang dengan **dua garis** — karakter `✓` TIDAK ADA di font standar helv:

   ```python
   BLUE = (0, 0, 0.75)
   pg.draw_line(pymupdf.Point(cx+2.4, cy+4.1), pymupdf.Point(cx+4.4, cy+6.6), color=BLUE, width=1.3)
   pg.draw_line(pymupdf.Point(cx+4.4, cy+6.6), pymupdf.Point(cx+9.4, cy-1.9), color=BLUE, width=1.3)
   ```

3. **Tulis nilainya** dengan warna bukan-hitam supaya isian kita kelihatan jelas:

   ```python
   pg.insert_text((x, y), "ANO", fontname="helv", fontsize=10, color=BLUE)
   d.save(out)   # simpan ke FILE BARU, jangan timpa PDF asli user
   ```

## Verifikasi — pakai TEKS DIGITAL, bukan render gambar

**Aturan keras.** `vision_analyze` pada PNG hasil render bisa salah baca huruf kecil yang
berdempetan. Kejadian nyata: `dewamalaikat1981@gmail.com` terbaca `dewamalakat1981@gmail.com`
(huruf `i` hilang) -> hampir dilaporkan sebagai "email salah". False alarm.

```python
for b in d[0].get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            if s["color"] != 0:      # isian kita = bukan hitam
                print(f'[{s["color"]:>8}] x={s["bbox"][0]:6.1f} y={s["bbox"][1]:6.1f} | {s["text"]}')
```

Cocokkan tiap nilai karakter-per-karakter. Render gambar hanya untuk mengecek **posisi**,
dan konfirmasi setiap temuan gambar dengan teks digital sebelum melaporkan masalah ke user.

## Dokumen resmi: JANGAN mengarang nilai

Untuk formulir asuransi/bank/legal, **berhenti dan tanya** sebelum mengisi field yang tidak diketahui.

- **Jangan** mengarang nomor polis/akun/IC. Kalau di surat hanya tertulis sebagian
  (`XXXXXXXXX9761`), isi persis apa adanya dan beri tahu user bahwa digit awalnya tidak ada.
- **Jangan** mengisi data yang tidak diberikan user (email, IC, alamat). Tanyakan dulu —
  dan pakai daftar pilihan (bukan pertanyaan terbuka) supaya user cepat menjawab.
- Kalau user tidak punya data lama yang diminta (mis. nomor passport sebelumnya sudah lupa),
  tulis penanda eksplisit `(not available)` — jangan dikosongkan, supaya petugas tahu itu memang
  tidak tersedia.
- Selalu ingatkan: form masih perlu **tanda tangan + lampiran** (salinan passport/KTP) sebelum
  dikirim, plus batas waktu dari surat (mis. 30 hari).

## Pitfall

- `import fitz` masih jalan tapi deprecated -> pakai `import pymupdf`.
- Font standar cuma `helv`/`tiro`/`cour`, dan **latin-1**: jangan `insert_text` karakter `✓`, `→`,
  atau aksen non-latin (jadi kotak/error).
- Simpan ke file baru (mis. `RFC_<nama>_<no>.pdf`) supaya bisa dibandingkan dan diulang.
- Data identitas orang (passport/IC) hanya ditulis ke file PDF hasil; jangan disalin ke chat/log.
