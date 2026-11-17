#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR a scanned / image-only PDF with pymupdf page rendering + tesseract.

Use when `read_file` on a local PDF answers with
  NeedsOcrError: page N of M needs OCR

i.e. the PDF has no usable text layer. No ghostscript / pdftoppm needed: pymupdf
renders the pages, tesseract reads them.

Usage:
  python pdf_ocr_tesseract.py file.pdf                  # 300 dpi, eng+tha, all pages
  python pdf_ocr_tesseract.py file.pdf --lang eng       # english only
  python pdf_ocr_tesseract.py file.pdf --pages 1,2      # only those pages (1-based)
  python pdf_ocr_tesseract.py file.pdf --dpi 400 --out /tmp/doc.txt

Notes
- Install once into the interpreter you will run: `pip install pymupdf` (~25MB).
- `tesseract --list-langs` must contain the languages you ask for (eng and tha are
  usually installed already).
- OCR is lossy on long hex strings (TxIDs, hashes, account numbers): re-read those fields
  from the image at higher dpi or copy them from the source app. Never trust an OCR'd
  identifier in a document that goes to a bank or a land office.
"""
import argparse
import os
import subprocess
import sys
import tempfile

try:
    import pymupdf as fitz
except ImportError:  # older releases only ship the fitz name
    import fitz  # type: ignore


def ocr_page(page, idx, outdir, dpi, lang):
    pix = page.get_pixmap(dpi=dpi)
    img = os.path.join(outdir, f"page_{idx:03d}.png")
    pix.save(img)
    res = subprocess.run(
        ["tesseract", img, "stdout", "-l", lang, "--psm", "3"],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return f"===== PAGE {idx} (tesseract failed: {res.stderr.strip()[:200]}) =====\n"
    return f"===== PAGE {idx} =====\n{res.stdout.rstrip()}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--lang", default="eng+tha")
    ap.add_argument("--pages", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"not found: {args.pdf}")

    doc = fitz.open(args.pdf)
    wanted = None
    if args.pages.strip():
        wanted = {int(p) for p in args.pages.split(",") if p.strip()}

    chunks = []
    with tempfile.TemporaryDirectory(prefix="pdfocr_") as tmp:
        for i, page in enumerate(doc, start=1):
            if wanted and i not in wanted:
                continue
            chunks.append(ocr_page(page, i, tmp, args.dpi, args.lang))

    text = "\n".join(chunks)
    out = args.out or (os.path.splitext(args.pdf)[0] + ".ocr.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"--- OCR saved: {out} ({len(text)} chars, {len(chunks)} pages) ---")
    print(text[:6000])


if __name__ == "__main__":
    main()
