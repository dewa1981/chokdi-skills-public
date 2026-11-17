---
name: product-photo-promo-video
description: "Use when making a sales/promo video from a product photo."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [ffmpeg, tts, promo, video, thai, shopee, affiliate]
---

# Product Photo → Sales Promo Video (Thai voiceover + captions)

Turn a single product photo (box / Shopee listing screenshot / sachet) into a vertical 9:16 promo video with Thai voiceover and on-screen Thai text. Built & validated for Patty's Shopee-affiliate product promos (Vene Vicenza collagen, VICHY&GA, etc.).

## ⚠️ RULE #1 — CONFIRM PRODUCT FACTS BEFORE RECORDING VOICEOVER

Vision/AI reads of product labels are often WRONG or incomplete. In one session the box was mislabeled and the user corrected TWICE: **"มันคือคอลลาเจน ไม่ใช่ดีท็อกซ์"** and **"แบบทดลอง 269฿ มีแค่ 6"** (trial = 6 sachets, not 12). Each correction = full TTS + video re-render.

Before generating ANY voiceover, confirm with the user (single clarify call):
- **Brand + exact product name** (spelling matters — Vene/VICHY/VIO look-alikes)
- **Product category**: collagen / detox / supplement / skincare — never guess from label tech-words (FIR, F1R, LIPO TECT are marketing, not the category)
- **Exact variant & pack size**: trial vs full box, number of sachets
- **Price** (and whether it's in the photo or must be omitted)
- **Selling angle**: which benefit to lead with (บำรุงผิว ฟื้นฟู เปล่งปลั่ง vs detox...)
- **Voice**: this user wants female Thai voice unless told otherwise

## Pipeline (validated end-to-end)

1. **Read the image** — vision_analyze; if it 429s (GoUsageLimitError) use the 9router combo99 fallback (see `local-image-ocr` skill). Shopee listing screenshots OCR well and carry price/sold/rating — prefer them as the video source when available.
2. **Confirm facts** (Rule #1).
2b. **When price/pack is uncertain, verify against the BRAND'S OWN SITE** — marketplace listings of the same product vary wildly (Vene Vicenza seen at ฿269 / ฿490 / ฿690 across shops), so a Shopee screenshot is weak evidence. Strip the brand page to text:
   ```bash
   curl -sL -A "Mozilla/5.0" --max-time 40 "<brand-url>" -o /tmp/p.html
   python3 -c "import re,html;t=open('/tmp/p.html',encoding='utf-8',errors='ignore').read();t=re.sub(r'(?is)<(script|style|noscript).*?</\1>',' ',t);t=re.sub(r'(?s)<[^>]+>',' ',t);print(re.sub(r'[ \t]+',' ',html.unescape(t))[:3000])"
   ```
   (This is how "1 กล่อง (12ซอง) ราคา 490 บาท (ส่งฟรี)" was confirmed on the brand site while the user's screenshot said ฿269.) State the price with its source, and say so plainly when the listing and the brand disagree — never invent or round a price.
3. **Write Thai voiceover script ~14–15 s** — numbers spoken in Thai words (สองร้อยหกสิบเก้า = 269). Include category + benefit + pack size + price + promo + ส่งฟรี + ของแท้ + CTA. **Get price/pack/promo settled BEFORE recording**: in one session the user corrected the same offer three times (category → pack size → price → "no trial box, buy 2 get a free 6-sachet box") = three TTS files + three full renders.
4. **Voice — check the gender of the CONFIGURED voice first.** `text_to_speech` uses `tts.edge.voice` from `config.yaml`, which for this profile was **`th-TH-NiwatNeural` (MALE)** — the user heard the finished promo and said "เสียงจากคลิปยังเป็นผู้ชายอยู่". The tool's `instructions` parameter is ignored by the edge provider, and an agent write to `config.yaml` is refused ("Refusing to write to Hermes config file"), so get the wanted voice per-call instead:
   ```bash
   grep -A3 '^tts:' /opt/data/profiles/<profile>/config.yaml   # see what voice is actually set
   bash scripts/edge_tts_thai_female.sh "<thai script>" /opt/data/vo.ogg
   ```
   `scripts/edge_tts_thai_female.sh` calls `edge_tts.Communicate(text, "th-TH-PremwadeeNeural", rate="-5%")` directly (female Thai) — no config change needed. Transcode before muxing: `ffmpeg -y -v error -i vo.ogg -ar 44100 -ac 1 vo.wav`; ffprobe duration sets the video length.
5. **Compose one still 1080×1920**: blurred bg (image scaled+cropped then `boxblur=25:3`) + product fg (~900 px wide) centered via overlay. One PNG → then zoompan.
6. **zoompan Ken Burns**: `-loop 1 -i composed.png -vf "zoompan=z='min(zoom+0.0006,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=450:s=1080x1920:fps=30" -t 15 -c:v libx264 -pix_fmt yuv420p` (450 frames @30fps ≈ 15 s).
7. **drawtext Thai captions**: font `/opt/data/fonts/NotoSansThai.ttf` (verify exists — if env was reset, re-download). White text + `borderw=4:bordercolor=black`, price line in yellow. Keep lines short so they fit 1080 width.
8. **Mux**: `-i video_nosound.mp4 -i vo.wav -c:v copy -c:a aac -b:a 192k -shortest`.
9. Deliver via `MEDIA:/path/file.mp4`; state duration/format/voiceover text so the user can verify without opening.

See `scripts/build_promo_video.sh` for a parameterized, known-good implementation of steps 5–8.

### Multi-image (slideshow) variant — 2–4 product/label photos in one promo
Same pipeline, but each still gets its own `zoompan`, joined with `xfade`:
```
[0:v]zoompan=...:d=<seg*30>:s=1080x1920:fps=30[v0];
[1:v]zoompan=...:d=<seg*30>:s=1080x1920:fps=30[v1];
[2:v]zoompan=...:d=<seg*30>:s=1080x1920:fps=30[v2];
[v0][v1]xfade=transition=fade:duration=0.5:offset=<seg-0.5>[x1];
[x1][v2]xfade=transition=fade:duration=0.5:offset=<2*seg-0.5>[x2];
[x2]drawtext=...  → -t <total> → mux voice with -shortest
```
`seg = ceil(voice_duration / image_count)`; with 17.5 s of voice and 3 images use `seg=7`, offsets `6.5` and `13.5`. Ready-made: `scripts/build_slides_promo_video.sh`.

### Step 10 — verify the rendered captions, not just the command
Reading back the on-screen text catches a stale caption after a fact change:
```bash
ffmpeg -y -v error -ss 3 -i out.mp4 -frames:v 1 /tmp/frame.jpg
apt-get install -y tesseract-ocr-tha        # Thai language pack
 tesseract /tmp/frame.jpg - -l tha --psm 6  # Thai OCR is noisy on outlined text → treats a partial read as "text present"
```
See `references/thai-caption-verification.md`. Also report the file's real specs to the user (`ffprobe` duration / WxH) so they can verify without opening it.

## Pitfalls

- **zoompan on a source with alpha/yuva420p fails** ("Filter format:default has an unconnected output") — compose the full frame to a plain RGB PNG first, then zoompan on that still.
- **text_to_speech output is .ogg** — always transcode to 44100 mono WAV before muxing.
- **Video length must match the voice**: use `-t` (video) + `-shortest` (mux).
- **Thai text = tofu (□) if font missing** — check `/opt/data/fonts/NotoSansThai.ttf` before rendering; after env resets it can vanish (download from google/fonts GitHub).
- **On-screen numbers must match voiceover** (pack size, price) — a stale caption after a fact correction is a silent error; rebuild both together.
- Captions with commas/quotes need escaping in drawtext (`text='...'` inside double-quoted -vf).
- **Bash cannot do float arithmetic** — `OFFSET=$((D/3-0.5))` dies with `syntax error: invalid arithmetic operator (error token is ".5")`. Compute fractional values with `python3 -c` or `awk -v s=$SEG 'BEGIN{printf "%.3f", s-0.5}'`, then interpolate the plain numbers into the filtergraph.
- **Do not trust the caption just because ffmpeg exited 0** — drawtext silently renders nothing if the font path is wrong and can emit stale text after a script change; re-extract a frame and read it back (step 10).
- **`edit_config`/`patch` on `config.yaml` is refused** for agent writes — any per-call behaviour change (voice, speed) must go through the tool argument or a direct provider call (see step 4), not a config edit.

## Support files
- `scripts/build_promo_video.sh` — single-still promo (steps 5–8).
- `scripts/build_slides_promo_video.sh` — 2–4 stills → xfade slideshow + Thai captions + voiceover.
- `scripts/edge_tts_thai_female.sh` — Thai FEMALE voiceover without touching config.yaml.
- `references/thai-caption-verification.md` — verify Thai on-screen text via OCR.
