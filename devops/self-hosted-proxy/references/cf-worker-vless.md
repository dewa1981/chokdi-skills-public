# CF Worker VLESS Proxy — script + deploy quirks (2026-08-07)

## Dua Level Worker

### 1. Simple WS proxy (cuma tembus WebSocket)
Pipe WS → WS ke target dari query `?host=&port=&path=`. Hanya jalan untuk situs yang support WebSocket (googleapis, ip.sb) — website HTTP biasa → `ERR_CONNECTION_CLOSED`.

### 2. VLESS PROPER (edgetunnel style) — tembus SEMUA web
Harus parse header VLESS dari WebSocket (16+ bytes: version, uuid 16, optM, cmd, port 2, atyp, addr) lalu forward TCP via WS ke `host:port` target. Client v2rayN kirim target di header VLESS — worker simple yang tidak parse header tidak akan tahu target (default www.google.com).

## Link vless:// (format copas v2rayN)

```
vless://<UUID>@<worker>.workers.dev:443?encryption=none&security=tls&type=ws&host=<worker>.workers.dev&path=%2F#CF-VLESS
```

## Deploy via API (kalau tidak mau paste manual)

- Endpoint: `PUT /accounts/{aid}/workers/scripts/{name}` (multipart).
- Format MODULE: metadata `{"main_module":"file.js","compatibility_date":"2024-01-01"}` + part bernama `file.js` (sama dengan main_module).
- Python requests MENANG (curl -F sering gagal `"multipart uploads must contain a readable body_part"` — termasuk saat token kurang izin; error misleading).
- Token butuh izin **Workers Scripts: Edit** — token Read-only gagal dengan error multipart yang sama (jangan salah diagnosis).
- PASTE MANUAL di dashboard (Workers & Pages → Create → Edit code → Deploy) = paling andal; UI mengatur format otomatis.

## Catatan 9Router/Cloudflare edge

- Worker di `*.workers.dev` = CF edge; akses ke situs CF-protected lain bisa kena challenge (CF→CF). Normal.
- Delays sangat rendah (5-30ms) karena network Cloudflare.
