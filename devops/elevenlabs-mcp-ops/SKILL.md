---
name: elevenlabs-mcp-ops
description: "Use when operating the ElevenLabs MCP server in Hermes."
version: 1.0.0
author: chokdi_staging
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [elevenlabs, mcp, tts, voice, agents, oauth]
---

# ElevenLabs MCP (agentes + creative) — ops

Hosted MCP server ElevenLabs, terpasang di staging 15-Sep-2026 lewat OAuth. **111 tool.**

| Hal | Nilai |
|---|---|
| URL | `https://api.us.elevenlabs.io/v1/mcp` (versi `.us` — sesuai instruksi Hermes di situs mereka) |
| Auth | **OAuth** (`auth: oauth`), token tersimpan lokal; TIDAK pakai `ELEVENLABS_API_KEY` |
| Tool | **111** — 81 prefix `agents_*`, 29 `creative_*`, 1 `get_more_tools` |
| Scope | `convai_read/write`, `text_to_speech`, `speech_history_read`, `flows`, `image_video_generation`, `voice_generation` |

## Alur pasang (OAuth — wajib lewat Bang)

```bash
hermes mcp add elevenlabs --url https://api.us.elevenlabs.io/v1/mcp --auth oauth
# non-interaktif akan GAGAL di tahap OAuth → simpan config saja, lanjut login:
hermes mcp login elevenlabs --flow browser      # jalankan PTY background (pty=True)
```

Lalu: kirim **URL authorize** ke Bang → Bang login & authorize → Bang copy URL `127.0.0.1:27890/callback?...`
→ tempel ke sesi PTY itu (`process(action='submit')`) → output `✓ Authenticated — 111 tool(s) available`.

### Pitfall OAuth (semua pernah kena)

1. **`hermes mcp add` non-interaktif gagal di OAuth** — pesannya "non-interactive environment and no cached tokens".
   Tetap jawab `Y` di prompt "Save config anyway" agar entry tersimpan, lalu `hermes mcp login`.
2. **Entry hasil `mcp add` tidak punya `auth:`** → `hermes mcp login` menolak dengan "Server 'elevenlabs' is not configured for OAuth (auth=None)".
   Tambahkan manual di `config.yaml`:
   ```yaml
   elevenlabs:
     url: https://api.us.elevenlabs.io/v1/mcp
     auth: oauth
     enabled: true
   ```
3. **JANGAN set `oauth.redirect_port`.** ElevenLabs memakai **client_id statis** (`nousresearch.github.io/.../client-metadata.json`),
   bukan pendaftaran dinamis. Begitu `redirect_port` diisi, login gagal `Registration failed: 404 {"detail":"Not Found"}`.
   Biarkan default **27890**.
4. **`Errno 98 Address already in use` muncul walau `ss`/`lsof`/`/proc/net/tcp` bersih** — port bind oleh proses
   login yang baru saja exit / race. Jalankan ulang `hermes mcp login`; kalau masih error, tunggu beberapa detik lalu ulangi.
5. **Proses login exit sendiri kalau nunggu lama** (~2 menit: `Authentication failed: OAuth callback port ... in use`
   atau habis waktu). Bang harus **authorize dulu, baru paste URL balikan dengan cepat**.
6. **`--flow device` tidak didukung** server ini: "Server does not advertise device authorization".
7. **Status tetap `disabled` setelah auth sukses** — `hermes mcp configure` butuh terminal interaktif.
   Set manual `enabled: true` di blok `mcp_servers.elevenlabs` pada `config.yaml`.

## Verifikasi

```bash
hermes mcp list            # elevenlabs → ✓ enabled
hermes mcp test elevenlabs # daftar 111 tool
```
Tool baru aktif di **session Hermes berikutnya**; session berjalan belum memuatnya.

Uji panggil dari Python (pola API Hermes):
```python
from hermes_cli.mcp_config import _get_mcp_servers
from tools import mcp_tool_discovery as disc
cfg = _get_mcp_servers()["elevenlabs"]
t = await disc._connect_server("elevenlabs", cfg)
res = await t.session.call_tool("creative_list_voices", arguments={})
```

## Kegunaan buat kita

- `creative_*` → voice/musik/gambar/video (50+ model) — bandingkan dengan jalur Grok/fal/nanobanana kita.
- `agents_*` → kelola voice & chat agent ElevenLabs (prompt, voice, kuota, transcript) tanpa buka dashboard.
- ⚠️ Ini **server cloud** — metadata workspace terkirim ke ElevenLabs (wajar, itu vendor-nya).
  TTS/STT produksi kita (suara Andi, `eleven_multilingual_v2`) tetap jalan lewat API key seperti sebelumnya — MCP ini **tambahan**, bukan pengganti.
- ⚠️ Backup `~/.hermes/config.yaml` sebelum mengubah blok MCP.
