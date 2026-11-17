---
name: pdf-creator-weasyprint
description: "Use when bikin PDF. WeasyPrint Markdown->HTML->PDF keren."
version: 1.0.0
platforms: [linux]
---

# PDF Creator (WeasyPrint)

Resep dari Cakra (Pencakar) — dipakai untuk semua pembuatan PDF di Hermes.

## Aturan WAJIB (dari guru)
1. **Bikin PDF** → WeasyPrint: Markdown → HTML → PDF (CSS styling, header/footer, page number)
2. **Edit PDF existing** → `nano-pdf` CLI (bahasa natural)
3. **File hasil WAJIB disimpan di `/opt/data/TMP/`** sebelum dikirim
4. **Verifikasi sebelum kirim**: file kebuka, isi sesuai, halaman ga error
5. **Proofread** konten yang mau dipublish (bahasa + konsistensi)
6. **Data dinamis** (angka/harga/tanggal): jangan diisi asal — kalau ga ada bilang ga ada

## Tool yang dipakai
- `weasyprint` + `markdown` → di `/opt/data/pylibs/` (install via: `uv pip install --python /usr/bin/python3 --target /opt/data/pylibs weasyprint markdown`)
- `nano-pdf` → `/opt/data/pylibs/bin/nano-pdf`
- Script siap pakai: `/opt/data/scripts/md2pdf.py`

## Pakai
```bash
python3 /opt/data/scripts/md2pdf.py input.md output.pdf
# output default: /opt/data/TMP/<nama>.pdf
```

## Verifikasi (wajib tiap bikin)
```python
from pypdf import PdfReader  # di pylibs
r = PdfReader(path); assert len(r.pages) > 0
assert "judul" in r.pages[0].extract_text()
```

## Pitfall
- WeasyPrint butuh libcairo/pango system — sudah ada di image ini
- Emoji jalan (DejaVu), tabel pakai extension `tables` markdown
- Kalau PDF gagal render → cek syntax HTML di `<style>`, jangan langsung kirim versi lama
