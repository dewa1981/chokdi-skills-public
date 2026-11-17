# Verifying Thai on-screen text in a rendered video (OCR read-back)

Purpose: prove that the caption you *intended* actually appears in the exported file, and that
no stale text survived a fact correction (e.g. price changed 269฿ → 490฿ but a caption kept 269).
The drawtext filter exits 0 even when the visible result is wrong or the font is missing, so a
zero exit code is not evidence.

## Setup (once per environment)
```bash
which tesseract || apt-get install -y tesseract-ocr
apt-get install -y tesseract-ocr-tha      # Thai language pack (default install is eng+osd only)
tesseract --list-langs                    # expect: eng osd tha
```

## Read back a frame
```bash
# 1) grab a frame at a moment when the captions are visible (skip the first/last 0.5 s)
ffmpeg -y -v error -ss 3 -i out.mp4 -frames:v 1 /tmp/frame.jpg

# 2) OCR full frame (page-segmentation 6 = assume a uniform block of text)
tesseract /tmp/frame.jpg - -l tha --psm 6 2>/dev/null

# 3) better signal: crop just the caption band and upscale before OCR
ffmpeg -y -v error -i out.mp4 -vf "select=eq(n\,45),crop=1080:400:0:60,scale=1600:-1" -frames:v 1 /tmp/top.png
tesseract /tmp/top.png - -l tha --psm 6 2>/dev/null
```

## Interpreting the result (honest limits)
- Tesseract on **outlined / stylised Thai captions** (white text + `borderw` on a photo background)
  returns garbled strings: e.g. `นับเงินไปเรื่อยๆ` came back as `เพพแจพิไฟ้เร้อยๆ` and
  `รวยแล้วนะ` as `เรจยแลอ`. That is still useful as a **presence check** — text is in the right
  screen region, the Thai font is rendering (not tofu boxes □), and roughly the right length.
- It is **not** proof of exact spelling. When spelling matters (price, brand name, pack size),
  confirm by reading the frame yourself with vision, or by comparing against the exact drawtext
  string you passed in.
- A clean way to sanity-check the font itself: render the same string with the same font onto a
  plain white PNG and OCR that — if it reads back correctly there, the font/glyphs are fine and
  any garbling is from the coloured background, not from a broken font file.

## Quick map of typical findings
| Symptom | Meaning |
|---|---|
| OCR reads nothing at all | text missing, font path wrong, or captions off-frame |
| OCR reads □ / boxes | font lacks Thai glyphs — check `/opt/data/fonts/NotoSansThai.ttf` |
| OCR reads garbled Thai | normal for outlined text on a photo — treat as present |
| Only one of two lines appears | second drawtext `y` overlaps the first, or is outside the frame |
