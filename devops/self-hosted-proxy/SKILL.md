---
name: self-hosted-proxy
description: Use when needing a proxy or bypassing outbound IP blocks.
---

# Self-Hosted Proxy (SSH SOCKS5 / CF Worker VLESS / ArgoSBX)

Bikin proxy sendiri untuk akses outbound — bypass IP datacenter yang di-flag Google/YouTube, akses web yang diblokir, atau ganti IP keluar. Berdasarkan pengalaman nyata 2026-08-07 (Hermes cloud di-flag → butuh "kaki bersih").

## Kapan Dipakai

- Hermes/agent di IP datacenter di-flag Google/YouTube (403/CAPTCHA/blokir) → proxy via VPS yang IP-nya bersih.
- User minta "pasang proxy di VPS biar 24 jam" atau referensi script proxy (ArgoSBX dll).
- Butuh IP keluar beda untuk test/curl.

## Opsi (urut dari paling cepat)

### 1. SSH Dynamic Forwarding (SOCKS5) — PALING CEPAT, tanpa install!

```bash
ssh -f -N -D 127.0.0.1:1080 -o ServerAliveInterval=30 user@VPS
```

- `-f` background, `-N` no command, `-D` = SOCKS5 port lokal.
- Pakai VPS yang IP-nya bersih (bukan range yang banyak dipakai bot).
- Test: `curl -x socks5h://127.0.0.1:1080 https://www.youtube.com` → 200 = tembus.
- Jembatan multi-hop: `-J user@hop:port` (ProxyJump) — Hermes→VPS AD→VPS X. Catatan: host key hop harus dikenal (StrictHostKeyChecking=no + UserKnownHostsFile=/dev/null kalau perlu).
- **24 jam**: pasang watchdog cron (lihat `scripts/watchdog_socks.sh`).

### 2. CF Worker VLESS (WebSocket proxy) — gratis, network Cloudflare

- Worker di dashboard CF: Workers & Pages → Create → paste script → Deploy. PASTE MANUAL = paling andal (API upload ribet — lihat pitfalls).
- Client v2rayN/nekobox: import link `vless://<uuid>@<worker>.workers.dev:443?encryption=none&security=tls&type=ws&path=/...#CF-VLESS`.
- Worker SIMPLE WS proxy (pipe ke target) cuma tembus situs WebSocket (googleapis, ip.sb) — website HTTP biasa gagal (ERR_CONNECTION_CLOSED). Butuh worker VLESS PROPER (parse header VLESS: uuid/cmd/port/atyp/host, lalu forward TCP via WS — edgetunnel style) biar tembus semua web.
- Template: `references/cf-worker-vless.md`.

### 3. ArgoSBX (yonggekkk/argosbx) — full multi-protocol server

- GitHub: yonggekkk/argosbx (5.6k★) — one-click, Sing-box+Xray+Argo, 15+ protokol (Naiveproxy, Vless-reality, SS-2022, Hysteria2, Tuic, Vmess-ws, Argo tunnel...).
- Cocok kalau mau JUALAN proxy / banyak klien (subscription Clash/sing-box).
- Mode Argo tunnel = outbound → tidak perlu buka port di firewall (cocok infra all-tunnel).
- Generator SSH command: https://yonggekkk.github.io/argosbx/

## Pitfalls

1. **pkill -f membunuh shell sendiri**: `pkill -f "ssh -f -N -D 127.0.0.1:1080"` di dalam script yang command-nya mengandung string itu → bash di-kill. Pakai pattern yang tidak match shell (mis. cek port dulu dengan `/dev/tcp` probe, kill pakai PID).
2. **CF Workers API deploy**: `curl -F` multipart sering gagal `"multipart uploads must contain a readable body_part"` (termasuk kalau token kurang izin — error misleading!). Python requests + format module (metadata `{"main_module":"file.js"}` + part nama file) lebih andal. Token perlu izin "Workers Scripts: Edit" (bukan cuma Read).
3. **IP datacenter vs CF 403**: 403 CF challenge di IP datacenter = proteksi anti-bot, BUKAN blokir — dari browser residential tetap jalan. Jangan salah diagnosis.
4. **SOCKS5 pakai `socks5h`** (bukan `socks5`) biar DNS resolve di sisi proxy.

## Referensi & Script

- `scripts/watchdog_socks.sh` — watchdog SOCKS5 (cron 2 menit, auto-restart).
- `references/cf-worker-vless.md` — script worker VLESS (simple vs proper) + link format + deploy quirks.
