---
name: diagram-png-render-pil
description: "Render diagrams to PNG without a browser — draw with Pillow."
version: 1.0.0
platforms: [linux]
---

# Diagram PNG via Pillow (tanpa browser)

Render diagram arsitektur/alur ke PNG langsung dengan PIL (Pillow) — dipakai
ketika browser tool ga bisa render file lokal. **Proven 2026-08-14** (JARVIS v2
diagram di Hermes Cloud): browser_navigate `file://` di-BLOCK
("Blocked: URL targets a private or internal address"), puppeteer tidak
ter-install, cairosvg/svglib/rsvg-convert/inkscape semua tidak ada → PIL yang
sudah ter-install di `/opt/data/pylibs` adalah jalur yang jalan.

## Kenapa bukan SVG/HTML dulu
PIL ga render HTML/SVG — gambar langsung dengan primitif. Ini SEBENARNYA cepat:
layout diagram (grid, kotak, panah, teks) cuma ~50 baris Python, output 1600x1000
crisp, tanpa dependency baru. Untuk diagram 1 layar (arsitektur, alur, peta
proses) ini lebih andal daripada nyari headless browser.

## Pola inti

```python
from PIL import Image, ImageDraw, ImageFont
import math
W, H = 1600, 1000
img = Image.new("RGB", (W, H), (2, 6, 23))       # bg slate-950
d = ImageDraw.Draw(img)

# grid 40px (gaya architecture-diagram)
for x in range(0, W, 40): d.line([(x,0),(x,H)], fill=(30,41,59), width=1)
for y in range(0, H, 40): d.line([(0,y),(W,y)], fill=(30,41,59), width=1)

def F(path, size): return ImageFont.truetype(path, size)
def box(x, y, w, h, fill, outline, ow=1, radius=10):
    d.rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=fill, outline=outline, width=ow)
def ctext(cx, y, text, font, fill, anchor="mm"):
    d.text((cx, y), text, font=font, fill=fill, anchor=anchor)

def arrow(x1, y1, x2, y2, color, width=2):
    d.line([(x1,y1),(x2,y2)], fill=color, width=width)
    ang = math.atan2(y2-y1, x2-x1); ah = 14
    d.polygon([(x2,y2),
        (x2 - ah*math.cos(ang-0.5), y2 - ah*math.sin(ang-0.5)),
        (x2 - ah*math.cos(ang+0.5), y2 - ah*math.sin(ang+0.5))], fill=color)
```

## Font — WAJIB path file TTF
PIL ga kenal nama font, harus path. Yang ada di image:
- `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` + `DejaVuSans-Bold.ttf` (paling aman)
- `/usr/share/fonts/truetype/liberation/LiberationSans*.ttf` (mirip Arial)
- `/usr/share/fonts/truetype/freefont/FreeSans.ttf`
- Emoji → kotak tofu di font biasa; pakai `NotoColorEmoji.ttf` (bitmap) kalau
  emoji wajib, atau ganti teks ASCII ("->" bukan "→").

## Thai text → WAJIB font Thai (proven 2026-08-25)
DejaVu/Liberation/FreeSans **tidak punya glyph Thai** — teks Thai muncul semua
jadi kotak `□` (tofu) tanpa error. Jangan salahkan layout; cek font dulu.
Fix yang sudah terbukti:
1. Download Noto Sans Thai variable font:
   `curl -sL -o /opt/data/fonts/NotoSansThai.ttf "https://github.com/google/fonts/raw/main/ofl/notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf"`
2. Taruh path itu **PERTAMA** di list FONT_PATHS, dengan fallback DejaVu:
   ```python
   FONT_PATHS = ["/opt/data/fonts/NotoSansThai.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
   def F(size):
       for p in FONT_PATHS:
           if os.path.exists(p):
               return ImageFont.truetype(p, size)
       return ImageFont.load_default()
   ```
3. Verifikasi WAJIB dengan vision_analyze setelah render (jangan kirim ke user
   sebelum dicek) — `vision_analyze(image_path, "ข้อความภาษาไทยอ่านออกไหม? ทับกันไหม?")`.
   Font variable (wdth,wght) render di weight default; cukup untuk judul. Bold
   terpisah belum tersedia di path itu — jangan dipaksa.

## Pitfalls (semua proven 2026-08-14)
1. **`anchor` di `d.text` WAJIB 2 karakter** — `anchor="m"` → `ValueError: anchor
   must be a 2 character string`. Pakai `"mm"` (center) / `"lm"` (left-middle).
2. Kotak semi-transparan: PIL butuh RGBA buat alpha — kalau cuma mau kotak
   solid di atas grid, pakai warna solid gelap (`(15,23,42)`), bukan rgba.
3. Panah elbow (belok): gambar polyline `d.line(pts, joint="curve")` lalu gambar
   segitiga di segmen terakhir.
4. Simpan PNG: `img.save(path)` — langsung bisa dikirim via MEDIA: ke Telegram.

## Alternatif kalau PIL ga ada
- `cairosvg` (pip) bisa SVG→PNG — kalau diagram sudah bentuk SVG string.
- `weasyprint` (sudah di pylibs) bisa HTML→PDF — untuk dokumen, bukan gambar.
- Cek dulu `python3 -c "import PIL"` sebelum bikin pipeline render.
