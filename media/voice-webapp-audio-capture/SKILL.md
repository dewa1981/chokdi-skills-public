---
name: voice-webapp-audio-capture
description: "Use when browser mic capture or STT upload fails (iOS)."
version: 1.0.0
author: Hermes Agent (curator)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [media, audio, mediarecorder, ios, safari, stt, pwa, voice]
---

# Voice Webapp — Audio Capture & STT Upload

The browser half of any mic→STT→LLM→TTS app: how to record reliably across
platforms, ship the right container to the STT API, and avoid the traps that make
an app look "broken" when the server side is actually fine.

Companion skills: `browser-voice-agent` (full pipeline + backend shape) and
`openai-realtime-voice-ai` (JARVIS-specific inventory). This skill is only the
audio-capture layer; read it before writing `MediaRecorder` code.

## Rule 1 — NEVER hardcode `audio/webm`

iOS Safari has **no WebM encoder**. `new MediaRecorder(stream, {mimeType:'audio/webm'})`
throws and the error surfaced to the user is the useless
`The string did not match the expected pattern.` Desktop Chrome/Android are fine
with WebM, so the bug only appears once the user tries their iPhone — late and confusing.

Detect support, mp4 first (iPhone is the most common failure):

```js
const cands = [
  'audio/mp4', 'audio/mp4;codecs=mp4a.40.2',
  'audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'
];
const mime = cands.find(c =>
  MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(c)) || '';
```

Then wrap construction — an unsupported string still throws:

```js
let rec, actualMime = mime;
try {
  rec = new MediaRecorder(stream, mime ? { mimeType: mime } : {});
} catch (e) {
  rec = new MediaRecorder(stream);          // no options at all
  actualMime = rec.mimeType || '';          // recorder is the source of truth
}
actualMime = rec.mimeType || actualMime;    // prefer what was actually negotiated
```

## Rule 2 — send the REAL mime to the backend

Do not label the upload with a guessed type. Pass the negotiated mime up and let
the server pick filename + blob type:

| client mime | extension | blob type |
|---|---|---|
| `audio/mp4` | `m4a` | `audio/mp4` |
| `audio/ogg` | `ogg` | `audio/ogg` |
| anything else | `webm` | `audio/webm` |

Backend (Node) shape that works with ElevenLabs Scribe:

```js
const clientMime = (req.body.mime || '').split(';')[0].trim() || 'audio/webm';
const ext = clientMime.includes('mp4') ? 'm4a' : clientMime.includes('ogg') ? 'ogg' : 'webm';
const blobType = clientMime.includes('mp4') ? 'audio/mp4' : clientMime.includes('ogg') ? 'audio/ogg' : 'audio/webm';
const fd = new FormData();
fd.append('file', new Blob([audioBuf], { type: blobType }), 'input.' + ext);
fd.append('model_id', 'scribe_v1');
```

- The FormData field **must be `file`** and must carry a filename. Without both,
  Scribe answers `400 Must provide either file or a URL parameter` — which reads like
  an auth/format problem and sends you debugging the wrong layer.
- The two fixes interact: a wrong mime label produces the same 400 as a missing field.
  Change both together, then verify with a real audio payload (below).

## Rule 3 — validate on the server, not only in the browser

A failed `getUserMedia`/`MediaRecorder` start can produce a zero-length blob that
still posts. Reject it server-side with a clear message instead of forwarding it.

The threshold matters: ElevenLabs Scribe answers `400 audio_too_short` for clips under
roughly 0.4 s, and the failure is silent downstream — the transcript comes back as
`[pause]` or `[tone]` and the model answers something unrelated, which reads as a
*model* problem when it is really a *button-release* problem. Reject below ~3000 bytes
(≈0.4 s of opus/m4a) and phrase the error as an instruction:

```js
if (!audioBuf || audioBuf.length < 3000) {
  return res.status(400).json({
    error: 'Rekaman kelewat pendek — tahan tombolnya, ngomong minimal 2 detik, baru lepas'
  });
}
```

When you see `audio_too_short` / `[pause]` in the logs, do not touch the model — the
user is releasing the button mid-sentence. Say so and shorten the loop.

Log the mime and byte size on every STT attempt — that one log line is what tells
you whether the browser sent anything at all:

```js
console.log('[stt] send:', clientMime, 'ext:', ext, 'size:', audioBuf.length);
```

## Rule 4 — playback: try THREE lanes, and know which failure you are looking at

`audio.play()` returns a Promise. iOS blocks autoplay unless the call is triggered by a
direct user gesture — but the TTS answer arrives 3-6 s *after* the user released the mic
button, so by then the gesture is spent. Retrying `play()` on the same element does NOT
help; that was a dead end.

Three lanes, in this order — each returns true/false so the next one can run:

1. **Web Audio API** (`AudioContext` + `decodeAudioData` + `BufferSource`). This is the
   only lane that **bypasses the iPhone silent switch** — `<audio>` element output is
   muted when the mute switch is on, Web Audio is not. Use it first.
2. **`<audio>` element** with `playsinline` + `await a.play()`.
3. **A visible "tap to play" button** fed from the last audio base64 held in a variable.
   An `onclick` IS a real gesture, so iOS always allows it. This lane never fails; it is
   the guaranteed floor. Reveal it only after lanes 1-2 both return false.

Unlock audio once on the first user touch (safe to call repeatedly):

```js
let sharedCtx = null;
function unlockAudio() {
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!sharedCtx && Ctx) sharedCtx = new Ctx();
  if (sharedCtx && sharedCtx.state === 'suspended') sharedCtx.resume();
  // a 1-sample silent buffer inside a gesture is what "grants" playback on iOS
}
document.addEventListener('touchstart', unlockAudio, { once: true });
document.addEventListener('click', unlockAudio, { once: true });
```

**Diagnostic that saves hours:** if `play()` **resolves with no error** yet the user hears
nothing, the code is fine — it is the device. That means silent switch, volume, or a
paired Bluetooth headset. Stop editing code and ask the user to check the physical mute
switch on the left edge of the iPhone, the volume buttons, and for connected headphones.
A status line that reports "audio playing" while the user hears silence will send you
through several wrong rewrites; treat *promise resolved + no sound* as a hardware gate,
not a bug.

## Rule 5 — default to continuous conversation, not push-to-talk

Do not ship a mic app whose only mode is press-and-hold. Users experience it as a
walkie-talkie and reject it: "capek kayak HT, tekan ngomong lepas, tekan ngomong lepas."
The expected feel for a voice assistant is *tap once, then talk freely*.

Build the continuous mode in the browser, no library needed:

1. Tap "mulai ngobrol" once → `getUserMedia` once, keep the stream alive.
2. Attach an `AnalyserNode` (`fftSize = 1024`) to that SAME stream; poll RMS every ~100 ms.
3. RMS above the threshold → user is speaking.
4. Silence sustained for ~1.4 s → stop the recorder, send the segment, await the reply.
5. On reply completion, start a fresh segment automatically. The user never touches anything.

Notes that matter:
- Never cut a segment before the silence window elapses — that chops sentences. If the
  user says it cuts them off, **raise** the silence window, do not lower the threshold.
- Keep the press-and-hold mode available as a fallback for when VAD misreads, and always
  ship an explicit STOP control.
- Speech-to-text runs on a live stream, so a zero-length segment is impossible; still keep
  the server-side length check from Rule 3.

## Rule 6 — never expose UI for an unimplemented feature

Shipping a `Hands-free: ON` toggle whose handler does nothing is worse than
omitting it: the user taps it, sees a fake "ON" state or an error, and concludes
the whole app is broken. Either mark it `disabled`, hide it, or have the handler
return an honest "belum siap" message. Never let a control claim a state the code
cannot deliver.

## Verification recipe

1. **Prove the server path first** — post a text payload (no audio) to the endpoint.
   A coherent reply proves LLM + TTS + memory are wired and isolates the bug to capture:
   ```bash
   curl -s -X POST http://127.0.0.1:<port>/talk -H 'Content-Type: application/json' \
     -d '{"text":"Halo, siapa nama kamu?"}'
   ```
2. **Prove STT with a synthetic clip** — generate a WAV with Python stdlib (no ffmpeg
   needed), base64 it, and post it with `mime: audio/wav`. Expect `200` and a
   transcript (a pure tone transcribes as `[tone]` — that still proves the pipe):
   ```python
   import struct, math
   sr, dur = 16000, 2.0
   frames = b''.join(struct.pack('<h', int(3000*math.sin(2*math.pi*440*i/sr))) for i in range(int(sr*dur)))
   hdr = b'RIFF'+struct.pack('<I',36+len(frames))+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,1,sr,sr*2,2,16)+b'data'+struct.pack('<I',len(frames))
   open('/tmp/test.wav','wb').write(hdr+frames)
   ```
3. **Test the rejection path** — post a ~5-byte payload with a normal mime and
   confirm you get your friendly 400 message, not a stack trace.
4. Only then ask the user to retry on their device, and tell them to **hard-refresh
   first** (close the tab or reload without content blockers) — a cached old bundle
   reproduces an already-fixed bug and wastes a round trip.

## Deploy note (containers)

`docker restart` does **not** pick up edited `server.js` / `public/*` — the image is
frozen. Use `docker compose up -d --build`, then verify the file actually present
*inside* the container, not just on the host:

```bash
docker exec <container> grep -c "<marker from your new code>" /app/public/index.html
```

Serve with `Cache-Control: no-store` on `/` and `/index.html`, otherwise the user's
browser keeps loading the previous bundle and the fix appears not to work.

## PWA essentials (managing from an iPhone home screen)

No App Store, no Apple review — a plain web page plus a manifest installs to the
home screen (Safari → Share → **Add to Home Screen**) and runs full-screen:

- `public/manifest.json` — `name`, `short_name`, `start_url: "/"`, `display: "standalone"`, `icons[]`
- `public/icon.png` — 192×192 is enough (generate PNG without a browser using Pillow)
- `<link rel="manifest">` + `<link rel="apple-touch-icon">` + `<meta name="apple-mobile-web-app-capable" content="yes">`

When the user worries about Apple review, explain plainly: an App Store listing needs
a developer account and review; a PWA does not — it is the same website, just
launched from an icon.
