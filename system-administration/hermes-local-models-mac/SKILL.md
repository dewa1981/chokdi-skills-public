---
name: hermes-local-models-mac
description: Use when adding local GGUF models to Hermes on macOS.
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [hermes, local-models, llamacpp, macos, gguf]
    category: system-administration
---

# Hermes Local Models on Apple Silicon

Install llama.cpp, register GGUFs, and get them to show up in the desktop app.

## Biggest trap: the page describes the CONNECTED BACKEND

Settings → Providers → Local Models reports **the machine running the backend**, not
the Mac in front of you. "This machine 62.8 GB RAM" + "Running llama.cpp (cpu)"
while the Mac has 128 GB means the app is connected to a **remote** backend, and any
model downloaded there lands on that server.

Verify before installing anything: compare the RAM figure with the target host, then
switch **Settings → Gateways → Connection mode → Local gateway**. Only then do the
Mac's own GPU/RAM and `~/.hermes/models` get listed (models appear under
**Added by you** with a Use button).

## Layout (machine-scoped, not profile-scoped)

- `~/.hermes/models/*.gguf` — servable weights.
- `~/.hermes/models/assets/` — **mmproj/vision projectors ONLY**. A `mmproj-*.gguf`
  left in `models/` is listed as a servable model and breaks the model list.
- `~/.hermes/tools/llamacpp-<backend>-<build>-<os>-<arch>/` — engine binary
  (`llamacpp-metal` on Apple Silicon).
- `~/.hermes/runtimes/llamacpp/presets.ini` — per-model launch policy.

## Install the engine by hand (when the app cannot)

`pm/lock.json` in the Hermes install dir pins every artifact:
`packages."llamacpp-metal".artifacts."darwin-arm64"` → `{url, sha256}`. Then:

```bash
curl -sL -o /tmp/llama.tar.gz "<url>"
shasum -a 256 /tmp/llama.tar.gz          # must equal the sha256 in lock.json
mkdir -p ~/.hermes/tools/llamacpp-metal-<build>-darwin-arm64
tar -xzf /tmp/llama.tar.gz -C <that dir> --strip-components=1
xattr -dr com.apple.quarantine <that dir>
```

## Preset entry format

Each section needs the machine-readable comment Hermes writes itself; without it the
model autoloads with stock fit instead of a policy decision:

```ini
# hermes-decision: {"model_id": "<stem>", "window": 262144, "spilled": false, "refusal": null}

[<stem>]
ctx-size = 262144
batch-size = 4096
ubatch-size = 2048
cache-type-k = q8_0
cache-type-v = q8_0
flash-attn = on
model = /Users/<user>/.hermes/models/<stem>.gguf
mmproj = /Users/<user>/.hermes/models/assets/<mmproj>.gguf
```

`<stem>` = the GGUF filename without `.gguf`; it is also the `/v1/models` id.

## Router run (manual verification)

```bash
llama-server --host 127.0.0.1 --port 18435 --api-key <key> --models-max 1 \
  --models-autoload --metrics --slots --no-ui --jinja --load-mode dio \
  --models-preset ~/.hermes/runtimes/llamacpp/presets.ini
```

Models load on first request; `/v1/models` lists all presets with status `unloaded`.
Prove each one with a chat completion — a listed model is not a working model.

## Pitfalls

- **Official Qwen GGUFs default to thinking mode.** With a small `max_tokens` you get
  an empty `content` and only `reasoning_content`. Either raise `max_tokens` to 400+ or
  send `"chat_template_kwargs": {"enable_thinking": false}`.
- **`hf`/`huggingface-cli` is absent on stock macOS.** Use
  `curl -L -C - --retry 5 --retry-all-errors -A "<browser UA>"`, and compare the file
  size against `x-linked-size` from a HEAD request to prove completeness.
- **TTS voice is per backend config**, not global: `tts.elevenlabs.voice_id` and
  `tts.default_voice`. Switching the gateway from Remote to Local switches voice too —
  set both keys on the new backend.
- **Two routers compete for RAM.** Stop any manually started `llama-server` before
  letting the app's own engine manage the models.
- A second copy of the same model in a different quant is fine but wasteful; pause the
  duplicate download instead of keeping both.

## Speed reference (M5 Max, Metal)

27B dense Q4 ≈ 26 tok/s · 35B-A3B MoE Q4 ≈ 115 tok/s · 35B-A3B MoE Q5 ≈ 87 tok/s.
