---
name: mcp-remote-oauth-registration
description: "Use when registering an OAuth MCP server in Hermes."
version: 1.0.0
author: chokdi_staging
license: MIT
platforms: [linux]
---

# Remote MCP Registration + OAuth (Hermes)

Non-interactive-safe procedure for adding a hosted (streamable-HTTP) MCP server that needs OAuth, and for
finishing the flow when the server has no browser. Applies to any `<name> --url <mcp-url> --auth oauth`
server; provider-specific notes live in `references/`.

## 1. Back up config first

```bash
cp /root/.hermes/config.yaml /root/.hermes/config.yaml.bak-<name>-$(date +%Y%m%d_%H%M%S)
```
Registration writes into `mcp_servers:` — never edit that block without a timestamped backup.

## 2. Confirm the endpoint is alive BEFORE touching config

A streamable-HTTP MCP endpoint often answers `GET` with **405 Method Not Allowed** — that is not a broken
endpoint, it only serves `POST`. Probe properly:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -m 20 -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}' <mcp-url>
# 401 = server HIDUP, cuma butuh auth → lanjutkan ke OAuth, JANGAN ganti URL/transport
# 404 / DNS gagal / connect refused = URL memang salah
```

Do not start swapping URL variants or pinning `transport: sse` before this probe says `401` or `200`.

## 3. Add the server — the command PROMPTS, it is not fire-and-forget

`hermes mcp add` asks a chain of questions and **cancels silently if stdin cannot answer them**.

tool-selection (`Enable all N tools? [Y/n/select]`) → maybe `Continue without authentication? [Y/n]` →
`Save config anyway? [y/N]`.

```bash
printf 'Y\ny\nY\n' | hermes mcp add <name> --url <mcp-url> --auth oauth
# atau yes Y | hermes mcp add ... untuk semua-yes
```

- The last prompt defaults to **N** — without a final `Y` **nothing is saved** and the command still exits 0.
- Always confirm with `hermes mcp list` that the entry exists. Don't infer success from the tool-list echo.
- When the initial connect failed and you answered "save anyway", the entry lands as **`enabled: false`**.
  That is expected, not a broken install — fix auth, then `hermes mcp test <name>`.

## 4. OAuth login when the host has no browser

Run it as a background PTY so it survives while the user authenticates:

```
terminal(background=true, pty=true, command="cd /root && hermes mcp login <name> --flow browser")
```

Then `process(action='poll')` the session to read the authorize URL and hand it to the user. Ask them to open
it, approve, and note that the browser then lands on `http://127.0.0.1:<port>/callback?...` which **cannot load
— that is expected** (it points at loopback on the Hermes host). They copy the **whole address bar URL** of that
error page and send it back; you `process(action='submit', data=<url>)` into the SAME session.

State lasts only a few minutes and every invocation prints a fresh `state`/`code_challenge` — if it expires,
re-run the login and send a NEW link. A redirect URL from an older run never matches.

Never ask the user for a password, API key, or the authorization code itself: they authenticate in their own
browser and only the final redirect URL is relayed.

### Pitfalls

- **`Server '<name>' is not configured for OAuth (auth=None)`** — the saved block under `mcp_servers:`
  lacks an `auth:` key even though you added it with `--auth oauth` (the key gets dropped when the initial
  connect fails). Fix by adding `auth: oauth` to that server's block in `config.yaml` (backup first), then
  re-run login. Inspect with `sed -n '/<name>:/,/enabled:/p' /root/.hermes/config.yaml`.
- **`Server does not advertise device authorization; use --flow browser`** — `--flow device` needs the server
  to support RFC 8628. Default to `--flow browser` unless you know it does.
- **`hermes mcp login` is refused in a non-interactive shell** (`non-interactive environment and no cached
  tokens found`). That is why it must run as a background PTY, not through a plain piped call.
- **JANGAN mengobati `Errno 98 Address already in use` dengan menyetel `oauth.redirect_port`.**
  Port yang kelihatan terpakai biasanya socket sisa percobaan sebelumnya, dan menambah key itu memindahkan
  flow ke dynamic client registration — provider dengan client_id statis langsung menolak
  (`Registration failed: 404`). Cek dulu `ss -tulpn | grep <port>` dan `/proc/net/tcp`; kalau kosong berarti
  bebas, cukup **ulangi perintah login**.
- **Sesi login bisa keluar sendiri dalam ~2 menit.** Kalau `process(action='submit')` balas `already_exited`,
  jangan berasumsi kodenya salah — prosesnya sudah mati sebelum paste. Mulai ulang login, kirim link BARU,
  dan minta user **authorize dulu baru paste** (jangan dibuat menunggu). Tiap invokasi punya state+PKCE baru;
  URL dari sesi lama tidak akan diterima sesi baru.
- **Urutan ini penting dan mudah terbalik:** `hermes mcp add` (simpan config) DULU, baru `hermes mcp login`.
  `login` menolak kalau entry-nya belum ada / belum punya `auth: oauth`.

## 5. Verify for real, then record

- `hermes mcp test <name>` → expect connect + tool count.
- **Call a read tool AND a write tool through the session, then confirm the effect outside the tool**
  (file on disk, record in the provider). A green `✓ enabled` row is not proof that tool calls work.
- A live `tools/list` can return **more** tools than the provider docs advertise — report what you observed.
- Third-party MCP servers are **untrusted** in Hermes: write-capable tools still prompt for approval.
  Leave the gate on; do not silence it to "make things smoother".
- Newly registered tools load in the **next** Hermes session — the running one does not pick them up.
- Append a one-line entry to the link library and to the provider's skill so the next session does not
  re-derive the endpoint, auth mode, and prompt answers.
- See `references/elevenlabs-mcp.md` for the ElevenLabs variants (regional URLs, OAuth scopes, what the
  connector exposes), and do not confuse OAuth-scoped connectors with an existing API-key integration.
- See `references/third-party-binary-install.md` for installing/verifying a third-party binary (checksums,
  permanent install, backing up the tool's own state) and for probing its stdio MCP handshake.
- See `references/stdio-docker-mcp.md` — when the stdio command is `docker exec`, env vars are NOT
  inherited (and a container-side `.env` is only read if the app calls `load_dotenv`): pass them as
  `-e K=V` arguments to `docker`, and never via `hermes mcp add --env`, which appends them to the end of
  `args` and saves the server `enabled: false`.
- `scripts/mcp_stdio_probe.py -- <command> [args]` — JSON-RPC handshake + tool listing against any stdio MCP
  server, without going through Hermes. Use it to separate "server won't answer" (wrong protocol assumption
  on your side) from "server answers but hangs inside a tool" (server-side lazy init).
