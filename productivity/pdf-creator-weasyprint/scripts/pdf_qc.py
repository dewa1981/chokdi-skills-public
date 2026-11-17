#!/usr/bin/env python3
"""QC cepat untuk PDF hasil WeasyPrint.

Pakai:
  PYTHONPATH=/opt/data/pylibs python3 scripts/pdf_qc.py out.pdf
  PYTHONPATH=/opt/data/pylibs python3 scripts/pdf_qc.py out.pdf --png /tmp/qc

Melaporkan: jumlah halaman, jumlah karakter per halaman, font ter-embed,
keberadaan karakter CJK, dan halaman mencurigakan (hampir kosong di antara
halaman penuh = salah page-break, bukan halaman pendek yang wajar).
Exit code 1 kalau ada temuan, supaya bisa dipakai sebagai gate.
"""
import argparse
import os
import sys

EMPTY = 300        # karakter; di bawah ini halaman dianggap tipis
FULL = 900         # karakter; halaman sebelumnya harus sepadat ini

def cjk_count(s: str) -> int:
    return sum(1 for ch in s if '\u4e00' <= ch <= '\u9fff')

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--png", help="render tiap halaman ke PNG di direktori ini (butuh pymupdf)")
    ap.add_argument("--dpi", type=int, default=85)
    ap.add_argument("--empty", type=int, default=EMPTY)
    ap.add_argument("--full", type=int, default=FULL)
    a = ap.parse_args()

    try:
        from pypdf import PdfReader
    except ImportError:
        print("pypdf tidak ada — jalankan dengan PYTHONPATH=/opt/data/pylibs")
        return 2

    r = PdfReader(a.pdf)
    n = len(r.pages)
    if n == 0:
        print("FAIL: 0 halaman")
        return 1

    chars, fonts, cjk, texts = [], set(), 0, []
    for p in r.pages:
        t = p.extract_text() or ""
        texts.append(t)
        chars.append(len(t.strip()))
        cjk += cjk_count(t)
        res = p.get("/Resources", {}) or {}
        for _, v in (res.get("/Font", {}) or {}).items():
            try:
                fonts.add(str(v.get_object().get("/BaseFont")))
            except Exception:
                pass

    print(f"{os.path.basename(a.pdf)}: {n} halaman")
    print("chars/page:", chars)
    print("fonts:", ", ".join(sorted(fonts)) or "(tidak terbaca)")
    print("karakter CJK:", cjk)

    problems = []
    suspect = [i + 1 for i in range(1, n - 1)
               if chars[i] < a.empty and chars[i - 1] >= a.full]
    if suspect:
        problems.append(f"halaman hampir kosong: {suspect} (cek page-break / blok non-splittable)")
    if not fonts:
        problems.append("tidak ada font ter-embed — PDF tidak akan bisa dibuka konsisten")
    if cjk and not any("WenQuanYi" in f or "CJK" in f or "Zen" in f for f in fonts):
        problems.append("ada teks CJK tapi font CJK tidak ter-embed (risiko kotak)")

    if a.png:
        try:
            import pymupdf
        except ImportError:
            print("pymupdf tidak ada — pip install --target /opt/data/tmp_pdfverify pymupdf")
        else:
            os.makedirs(a.png, exist_ok=True)
            d = pymupdf.open(a.pdf)
            for i, page in enumerate(d):
                out = os.path.join(a.png, f"p{i + 1}.png")
                page.get_pixmap(dpi=a.dpi).save(out)
            print(f"PNG: {a.png}/p1..p{n}.png — periksa dengan vision_analyze")

    if problems:
        for p in problems:
            print("SUSPECT:", p)
        return 1
    print("OK: tidak ada halaman mencurigakan")
    return 0

if __name__ == "__main__":
    sys.exit(main())
