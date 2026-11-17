---
name: image-text-extraction
description: "Use when reading text from images or screenshots."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ocr, image, vision, rapidocr, telegram]
---

# Image Text Extraction (OCR fallback)

Extract text from images (screenshots, Telegram attachments, Drive folder-tree screenshots) when the primary vision tool cannot read the local file. This user regularly sends screenshots of Google Drive folders, configs, and status pages that must be read as text.

## Fallback chain (user-defined order)

1. `vision_analyze` (primary) — works when it can access the image.
2. **RapidOCR (local, no network)** — this skill.
3. Custom fallback model (9router) — last resort per user preference.

## RapidOCR — the reliable local path

Installed at `/opt/data/pylibs` (persistent). Requires `PYTHONPATH` and the Hermes venv python:

```bash
export PYTHONPATH=/opt/data/pylibs
/opt/hermes/.venv/bin/python -c "
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
result, _ = ocr('/path/to/image.jpg')
if result:
    for line in result:
        print(line[1])   # recognized text
else:
    print('Tidak ada teks terdeteksi')
"
```

Install if missing (read-only venv → target dir):

```bash
uv pip install --python /opt/hermes/.venv/bin/python --target /opt/data/pylibs rapidocr-onnxruntime
```

## Verification before use

- Confirm the file is a real image first: JPEG starts with bytes `ff d8 ff e0` + `JFIF`; check via Python `open(path,'rb').read(16).hex()`.
- The `vision_analyze` tool may return `404 Couldn't find that` for local paths even when the file exists and is valid — this is exactly when to switch to RapidOCR rather than retrying vision.

## Pitfalls

- **tesseract binary may be absent** — `pytesseract` alone is useless without it; RapidOCR (onnxruntime) needs no external binary, it bundles models. Prefer RapidOCR.
- First run downloads/loads models (~10MB onnx files) — allow time.
- Text lines come back as `[bbox, text, confidence]` tuples; always print `line[1]`.
- For PDFs/scanned docs, use the `ocr-and-documents` skill (pymupdf/marker) instead — this skill is for standalone images.
