---
name: reel-editing-ffmpeg
description: Use when editing phone clips into reels with ffmpeg.
---

# Reel Editing via ffmpeg (phone clips → FB/TikTok Reels)

Proven workflow (Aug 2026, Patty's สโนว์ content): turn raw phone videos into
vertical reels with Thai title card, fades, and a ready-to-post caption.

## Pipeline (in order)

1. **Probe all incoming files** — identify duplicates first:
   ```bash
   md5sum /path/*.mp4 /path/*.mov        # identical hash = same clip sent twice → use once
   ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate,codec_name -of default=noprint_wrappers=1 FILE
   ```
   Note resolution + fps: all inputs must be **same resolution and fps** before concat.

2. **Extract frames to see content** (1 fps):
   ```bash
   ffmpeg -y -v error -i FILE -vf fps=1 -q:v 3 /tmp/fd/d_%02d.jpg
   ```
   Vision-check the start/middle/end frames (batch 6 vision calls per turn).

3. **Decide the cut** from what frames show: which segment is the hook, where
   dead air should be trimmed. If vision is down (503), ask the user to
   describe the clip — do NOT guess blindly; proceed only on their description.

4. **Test the Thai title card FIRST** (before full render):
   ```bash
   ffmpeg -y -v error -ss 2 -i INPUT -frames:v 1 -vf "scale=720:1280,drawtext=fontfile=/opt/data/fonts/NotoSansThai.ttf:text='TITLE':fontcolor=white:fontsize=48:borderw=5:bordercolor=black@0.6:x=(w-text_w)/2:y=h*0.07" -q:v 3 /tmp/title_test.jpg
   ```
   **Thai font is REQUIRED** — DejaVu has no Thai glyphs (renders □). Download once:
   ```bash
   curl -sL -o /opt/data/fonts/NotoSansThai.ttf "https://github.com/google/fonts/raw/main/ofl/notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf"
   ```
   Avoid emoji in drawtext (→ tofu); use plain Thai text.

5. **Render with concat** — scale EVERY input to a common size first
   (mixed 720x1280 + 960x1280 clips → all 720x1280), trim each segment,
   fade in/out, drawtext title with alpha fade-in/out:
   ```bash
   ffmpeg -y -v error -i CLIP1 -i CLIP2 -filter_complex \
     "[0:v]trim=0:12,setpts=PTS-STARTPTS,scale=720:1280,setsar=1[v0]; \
      [0:a]atrim=0:12,asetpts=PTS-STARTPTS[a0]; \
      [1:v]scale=720:1280,setsar=1[v1]; \
      [v0][a0][v1][1:a]concat=n=2:v=1:a=1[v][a]; \
      [v]fade=t=in:st=0:d=0.5,fade=t=out:st=END-0.6:d=0.6, \
          drawtext=fontfile=/opt/data/fonts/NotoSansThai.ttf:text='TITLE':fontcolor=white:fontsize=48:borderw=5:bordercolor=black@0.6:x=(w-text_w)/2:y=h*0.07:alpha='clip(min((t-0.6)/0.5,(4.8-t)/0.5),0,1)'[vout]; \
      [a]afade=t=in:st=0:d=0.4,afade=t=out:st=END-0.5:d=0.5[aout]" \
     -map "[vout]" -map "[aout]" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
     -c:a aac -b:a 128k -movflags +faststart OUT.mp4
   ```
   Compute `END` = sum of trimmed durations. End-card text (location transition)
   = second drawtext with alpha starting near the end.

6. **Verify the render** (never deliver untested):
   - Extract frames at key timestamps (title ~2s, transition, end card, last frame):
     `ffmpeg -ss T -i OUT.mp4 -frames:v 1 -q:v 3 /tmp/check.jpg`
   - Vision-check: title complete? end card readable? nothing overlapping/cut?
   - Check audio isn't clipped: `ffmpeg -i OUT.mp4 -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"` (max ≤ ~0 dB).

7. **Deliver** via `MEDIA:/path/out.mp4` + ready-to-paste caption (user's voice,
   ค่ะ for Patty) + hashtags + posting tips (reply to comments fast, pinned
   affiliate link in comments, cover image suggestion from user's own photo).

## Pitfalls
- **Different resolutions break concat** — always scale all inputs to one size
  in the filter graph.
- **Thai title tofu** — see step 4; verify with vision after render.
- **Vision_analyze flaky (503)** — retry once with a single frame; if still
  down, proceed with user's content description + technical probes only.
- **Duplicate uploads** — users often send the same clip twice; md5sum first.
- Long clips (30-40s) usually need trimming to the best 12-15s segment each.
- Reels target: ≤ 60s, vertical 720x1280 is fine (don't upscale to 1080).

## Related
- `video-frame-extraction` — extracting frames when video is too large for vision.
- `chat-media-delivery` — delivering generated media in chat.
