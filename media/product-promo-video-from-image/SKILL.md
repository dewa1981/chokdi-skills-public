---
name: product-promo-video-from-image
description: "Use when making a promo video from product photos."
version: 1.0.0
---

# Product Promo Video from Product Photos

Make a vertical 9:16 sales video from product photos (box shots, Shopee screenshots, sachet photos) with slow zoom, Thai text overlay, and Thai TTS voiceover. Established for Patty's affiliate/seller content (collagen drinks, snacks, etc.).

## Step 0 — READ THE PRODUCT BEFORE WRITING (critical)
- Identify brand, exact product type, price, pack size, claims from the image FIRST (vision_analyze; fallback = 9router combo99 vision via base64 data URL, see `local-image-ocr` skill).
- **Ask/confirm product type + pack size before recording voiceover.** Patty sells several similar "ALL IN ONE F.I.R." boxes (Vene Vicenza = COLLAGEN; VIO FIR; VICHY&GA) — easy to mistake one for a detox or to mix pack sizes. Getting claims wrong wastes a full voiceover render.
- **The user's spoken facts beat what the screenshot shows.** A marketplace listing can display a different variant/pack than the promo actually being run: the Vene listing screenshot read ฿269 while the real offer was **12 sachets @฿490, buy 2 boxes → free 6-sachet small box** — there was no trial box at all. Never carry a price/pack from the image into a voiceover unconfirmed.
- Verify on the brand's own site when a price looks odd (search `"<brand> ราคา กล่อง 12 ซอง"`): the official product page states pack size + price + shipping unambiguously, which beats a marketplace screenshot. Only claim what the brand itself claims — brand marketing lines ("ได้ผลกว่าคอลลาเจนทั่วไป 3 เท่า") stay attributed.
- If vision backend is rate-limited/empty: ask the user 1 short clarifying question (product name + selling angle) rather than guessing.

## Voiceover — FEMALE Thai voice (Patty preference)
- Config default `edge.voice` in profile config.yaml is male `th-TH-NiwatNeural`; cannot be patched via patch tool (config is security-sensitive).
- Override per call with python + edge_tts directly (works when text_to_speech tool uses default male voice):
```python
import edge_tts, asyncio
async def main():
    tts = edge_tts.Communicate(TEXT, "th-TH-PremwadeeNeural", rate="-5%")
    await tts.save("/opt/data/vo_x.mp3")
asyncio.run(main())
```
- Thai female voice: `th-TH-PremwadeeNeural`. Male: `th-TH-NiwatNeural`.
- Check duration: `ffprobe -v error -show_entries format=duration ...` then make video match (~14-16s typical).

## Video build (ffmpeg)
1. Verify images are portrait (960×1280 typical). If landscape, still compose to 9:16.
2. Per image, compose 1080×1920: blurred bg + sharp fg:
```
ffmpeg -y -v error -i photo.jpg -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:3" -frames:v 1 bg.png
ffmpeg -y -v error -i photo.jpg -vf "scale=920:-1" fg.png
ffmpeg -y -v error -i bg.png -i fg.png -filter_complex "[1:v]scale=920:-1[fg];[0:v][fg]overlay=(W-w)/2:(H-h)/2" -frames:v 1 slide.png
```
3. Slideshow with zoom + crossfade (per slide ~5s at 30fps, d=150 frames):
```
ffmpeg -y -v error -loop 1 -t 5 -i slide1.png -loop 1 -t 5 -i slide2.png -loop 1 -t 5 -i slide3.png \
 -filter_complex "[0:v]zoompan=z='min(1+0.0008*on,1.08)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30[v0]; ... [v0][v1]xfade=transition=fade:duration=0.5:offset=4.5[x1];[x1][v2]xfade=transition=fade:duration=0.5:offset=9.5[x2]" -map "[x2]" -t 14.8 -c:v libx264 -pix_fmt yuv420p -r 30 out.mp4
```
- Single-image variant: `-loop 1 -i composed.png` with one zoompan (d=450) — no xfade.
- Thai text overlay via drawtext (font must exist: /opt/data/fonts/NotoSansThai.ttf):
```
drawtext=fontfile=/opt/data/fonts/NotoSansThai.ttf:text='...':fontsize=58:fontcolor=white:borderw=4:bordercolor=black:x=(w-text_w)/2:y=h*0.03
```
  Layout: brand (top), slogan (mid-low ~y=h*0.80-0.82), price/size in yellow. Escape commas inside filter graph text carefully.
4. Merge voiceover: convert .ogg → wav first if needed, then `-c:v copy -c:a aac -b:a 192k -shortest`.

## Deliverables & polish
- Confirm voice gender with user after first render ("เสียงนี้ใช่ไหมครับ"); re-render only the TTS if wrong, remux with `-c:v copy`.
- Check product listing facts (price, rating, sold count) shown on screenshot — reuse real numbers from the image in caption/voiceover (but see Step 0: pack/price go to the user for confirmation).
- **A correction is a two-sided edit.** When the user changes a fact (price, pack, promo), regenerate the TTS script AND every `drawtext` line in the same pass, then verify from a rendered frame (`ffmpeg -ss T -i out.mp4 -frames:v 1 f.png`) — a stale price left on screen while the voice says the new one is the failure mode that slips through. Re-check the duration too: a longer corrected script needs a longer video.
- Post-corrections, also refresh any caption block already written for that product so the feed text matches the video.
