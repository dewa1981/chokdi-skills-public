---
name: wechat-silk-transcription
description: "Transcribe WeChat .silk voice messages that fail."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
---

# WeChat Voice Message (.silk) Transcription

WeChat (iLink) delivers voice messages as `.silk` files, and the gateway's auto-STT often fails on them ("voice message could not be transcribed automatically"). This workflow decodes the silk audio and transcribes it with a local faster-whisper model.

## When to Use

- Gateway reports `[voice message could not be transcribed automatically; audio at: /opt/data/cache/audio/audio_XXXX.silk]`
- User sends a voice message and the transcript comes back empty/failed.

## Quick One-Shot (if script already exists)

```bash
bash /opt/data/scripts/transcribe_silk.sh /opt/data/cache/audio/audio_XXXX.silk
```

## Manual Pipeline (if script missing or broken)

Durable pieces already installed on this host:
- `/opt/data/bin/silk_decoder` — compiled silk-v3-decoder (decodes silk → raw PCM)
- `/opt/data/models/faster-whisper-base` — working whisper model (clean dir, NOT symlinks)
- `/opt/data/lazy-packages/` — python deps (faster_whisper, ctranslate2, huggingface_hub, etc.)

Steps:

```bash
# 1. silk -> pcm (silk default is 24kHz mono)
/opt/data/bin/silk_decoder /opt/data/cache/audio/audio_XXXX.silk /tmp/vm.pcm

# 2. pcm -> wav
ffmpeg -y -f s16le -ar 24000 -ac 1 -i /tmp/vm.pcm /tmp/vm.wav

# 3. transcribe (Indonesian)
/opt/hermes/.venv/bin/python3 -c "
import sys; sys.path.insert(0, '/opt/data/lazy-packages')
from faster_whisper import WhisperModel
m = WhisperModel('/opt/data/models/faster-whisper-base', device='cpu', compute_type='int8')
seg, info = m.transcribe('/tmp/vm.wav', language='id')
print(' '.join(s.text.strip() for s in seg))
"
```

## Pitfalls (learned the hard way)

- **Model must be in a clean dir with REAL files, not HF symlinks.** The HF snapshot cache (`/opt/data/.cache/huggingface/hub/models--Systran--faster-whisper-base/snapshots/*/`) uses symlinks to `../../blobs/` and ctranslate2 fails with `RuntimeError: Unable to open file 'model.bin'`. Copy real files via `cp -L` into `/opt/data/models/faster-whisper-base/` (persistent). That path is the reliable one.
- **The venv is read-only** (owned by the managed Hermes image). `pip install` fails with Permission denied. `--user` fails (site-packages not visible in venv). Solution: use `/opt/data/lazy-packages/` via `sys.path.insert(0, ...)`.
- **Cron/terminal PATH is restricted.** Scripts that use awk/free/etc. fail under cron with "command not found". Set `export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"` at top of any script run by cron.
- **Concatenating WAV files with ffmpeg `concat:` protocol corrupts headers** (only first clip plays). Use the concat demuxer with a `list.txt` (file 'a.wav' lines) instead.
- **silk-v3-decoder build:** `pilk` (Python silk binding) only ships Windows wheels; on Linux build `kn007/silk-v3-decoder` from source with `make` (needs gcc). Prefer `/opt/data/bin/silk_decoder` which is already built.
- **faster-whisper-base model**: HF model.bin must be fully downloaded; a truncated/corrupt cache gives "Unable to open file 'model.bin'". Re-download with `HF_HUB_DISABLE_XET=1` or `force_download=True` to a fresh cache_dir, then `cp -L` real files out.

## Related

- For WeChat bot limits: WeChat (iLink) can only send audio as file attachments (no native voice bubble), cannot share location, group events usually not delivered. Telegram is the best platform for native voice bubbles.
