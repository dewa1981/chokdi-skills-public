---
name: mcp-app-builder
description: Use when building MCP Apps with UI widgets (Skybridge).
---

# MCP App Builder (Skybridge)

Bikin MCP tool yang **balas UI interaktif** (tabel/chart/tombol) di dalam chat,
bukan teks panjang. Beda dari MCP biasa: ada `view` di tool definition → host
render React widget di **iframe sandbox**.

## Kapan dipakai

- Tool balas data besar (1000 baris tabel) → kasih UI, model cukup lihat ringkasan
- Butuh tombol/aksi di chat (refresh, restart, konfirmasi)
- Dashboard mini yang muncul saat user tanya (status server, kuota, cron)
- **Bukan** untuk tool yang balas 1-2 baris teks — MCP biasa cukup

## Fakta stack

| Item | Nilai |
|---|---|
| Framework | `skybridge` (alpic-ai/skybridge), MIT, ~2.100 bintang |
| NPM | `skybridge` v2.0.0 (server + web entrypoint) |
| Scaffold | `npx create-skybridge@latest <nama>` |
| Host | ChatGPT **dan** Claude (host-agnostic) |
| Node wajib | **>=24.18** menurut package.json — v22.23 masih jalan (warning `EBADENGINE`, bukan error) |
| Jalur dev | `npx skybridge build` lalu `npx skybridge start` (default port **3000**) |
| Endpoint | `POST /mcp` (HTTP 405 pada GET = normal, endpoint hidup) |

## Pitfall #1 — npm install gagal `edgesOut`

`create-skybridge` menjalankan `npm install` sendiri dan sering **merusak lockfile**
→ `npm error Cannot read properties of null (reading 'edgesOut')`.

**Fix (terbukti):**
```bash
cd <project>
rm -f package-lock.json
rm -rf node_modules
npm cache verify
npm install --legacy-peer-deps
```
Hasil: ~471 paket, ~382 MB, `node_modules/skybridge` terpasang.
Jangan ulang `npm install` biasa tanpa hapus lockfile — error yang sama muncul lagi.

## Pitfall #2 — build gagal error TS dari view template

Template demo punya `src/views/components/**`, `onboarding.tsx`, `use-mascot.ts`
yang mereferensikan tool demo (`get-fortune-cookie`). Begitu tool diganti, build
melempar error tipe:
```
error TS2345: Argument of type '"get-fortune-cookie"' is not assignable to parameter of type '"<tool-baru>"'
```
**Fix:** hapus view demo yang tak dipakai (backup dulu!), sisakan view sendiri:
```bash
mkdir -p ../_backup_views_template && cp -r src/views ../_backup_views_template/
rm -rf src/views/components src/views/onboarding.tsx src/views/use-mascot.ts
```
`src/views/images/` boleh ditinggal (aset, bukan komponen).

## Pitfall #3 — `skybridge` bin "Permission denied"

Kalau `node_modules` kosong/rusak, `npx skybridge` balas `sh: 1: skybridge: Permission denied`.
Itu gejala install gagal — bukan masalah permission. Perbaiki install dulu (pitfall #1),
lalu pastikan `node_modules/.bin/skybridge` ada.

## Struktur project

```
src/server.ts        # definisi app + registerTool (metadata + handler)
src/views/status.tsx # komponen React per `view.component`
index.ts             # booting app saat dimuat runtime
```

### Tool definition yang balas UI
```ts
{
  name: "server-status",
  description: "...",
  inputSchema: { note: z.string().optional() },
  annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  _meta: {
    "openai/toolInvocation/invoking": "Mengambil status...",
    "openai/toolInvocation/invoked": "Status siap.",
  },
  view: {
    component: "status",                    // -> src/views/status.tsx
    domain: "https://skybridge.tech",
    description: "Widget status server",
    csp: { resourceDomains: ["https://fonts.googleapis.com", "https://fonts.gstatic.com"] },
  },
}
```

### Handler balas dua lapis
```ts
return {
  structuredContent: { ...data },   // dibaca widget via useToolInfo()
  content: [{ type: "text", text: "ringkasan 1 baris" }],  // dibaca model
  isError: false,
};
```
**Kunci:** model lihat `content` (ringkas), user lihat widget (lengkap).

### View React
```tsx
import { useToolInfo } from "skybridge/web";
const { output } = useToolInfo() as { output?: { structuredContent?: MyType } };
const st = output?.structuredContent ?? {};
```
`csp.resourceDomains` wajib dicantumkan untuk font/gambar eksternal, kalau tidak
iframe sandbox memblokirnya.

## Verifikasi (bukti nyata, bukan asumsi)

```bash
# 1. server hidup?
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3000/mcp   # 405 = OK

# 2. handshake
curl -s -X POST http://127.0.0.1:3000/mcp -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}'

# 3. list tool (cek ada _meta."ui/resourceUri" -> berarti view terdaftar)
curl -s -X POST http://127.0.0.1:3000/mcp -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

# 4. panggil tool
curl -s -X POST http://127.0.0.1:3000/mcp -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"<tool>","arguments":{}}}'
```
Respons SSE (`event: message` + `data: {...}`) = normal, bukan error.
Parse dengan `grep '^data: ' | sed 's/^data: //'` lalu `json.loads`.

## Preview widget tanpa host chat

Widget React tidak bisa dilihat tanpa host. Untuk cek tampilannya:
bikin HTML statis yang **meniru** markup widget (inline CSS, data contoh),
render pakai chromium headless, lalu nilai dengan `vision_analyze`:
```bash
chromium --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=760,560 \
  --screenshot=out.png "http://127.0.0.1:8898/preview.html"
```

## Pola aman untuk widget status server

- Hanya perintah BACA: `uptime -p`, `free -b`, `df -B1 /`, `cat /proc/loadavg`,
  `ps -eo comm --no-headers | grep -c '^hermes$'`
- Semua lewat `execFile` (bukan `exec` shell string) → tidak ada celah injeksi
- Setiap perintah dibungkus try/catch → satu gagal tidak mematikan widget
- `annotations.readOnlyHint: true` supaya host tahu ini aman
- Warna bar otomatis: hijau <70%, kuning >=70%, merah >=88%

## Referensi

- Repo: https://github.com/alpic-ai/skybridge
- NPM: `skybridge` v2.0.0
- Project contoh: `/opt/data/mcpapp/server-widget` (widget status server, build + tes OK)
