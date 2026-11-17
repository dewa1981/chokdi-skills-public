---
name: tanstack-start-cf
description: Use when memilih/deploy framework web full-stack di CF.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tanstack, foldkit, cloudflare, workers, react, fullstack, laravel, express, ssr]
    related_skills: [workers-best-practices, cloudflare-pages-ops, cloudflare-python-workers]
---

# TanStack Start di Cloudflare Workers (1.0 stable, Okt 2026)

## When to Use

- Bang/klien tanya *"framework apa buat proyek web baru?"* atau *"kenapa nggak pakai Laravel?"*
- Butuh keputusan stack: **Laravel (PHP) vs Express (JS) vs TanStack Start (TS)**
- Membuat/mengonfigurasi aplikasi **TanStack Start** dan men-deploy ke **Cloudflare Workers**
- Butuh SSR/streaming + server functions + binding CF (D1/R2/Queue/Cron/DO/Workflows) dalam satu app

Framework web full-stack **React + Solid**. Jalan native di **Cloudflare Workers**. Catatan ini
termasuk perbandingan vs **Laravel/Express** — dipakai saat memutuskan stack untuk proyek baru.

## Jawaban cepat: framework full-stack apa untuk proyek baru?

Bang pernah tanya *"kenapa kita nggak pakai Laravel biar cepat?"*. Jawabannya:

**Pakai TanStack Start, JANGAN Laravel** — kalau yang bikin/rawat adalah agent (hemat token,
tanpa nambah bahasa); **Laravel masuk hitungan hanya** kalau manusia yang ngoding, klien minta PHP,
atau beli template PHP (mis. e-commerce) yang tinggal dimodif.

| Kebutuhan | Laravel (PHP) | Express (JS) | **TanStack Start (TS)** |
|---|---|---|---|
| Full-stack siap pakai | ✅ | ❌ (rakit sendiri) | ✅ |
| Bahasa yang sudah kita pakai | ❌ PHP = bahasa ke-3 | ✅ | ✅ |
| Deploy Cloudflare | ❌ | 🟡 manual | ✅ **partner resmi** |
| Type-safe end-to-end | ❌ | ❌ | ✅ |
| Portable antar host | 🟡 | ✅ | ✅ |
| Gratis | 🟡 butuh server | 🟡 butuh server | ✅ Workers free tier |

**Alasan anti-Laravel (bukan "PHP jelek", tapi konteks kita):**
1. **Agent pembaca kode** — konvensi framework = token terbakar tiap sesi; Laravel menambah
   PHP 8.x + Composer + php-fpm + artisan ke toolchain yang harus dirawat.
2. **588 skill & puluhan cron kita Python/Bash** → Laravel jadi pulau terpisah yang butuh adapter baru.
3. Semua keunggulan Laravel (auth, ORM, migration, admin panel) sudah kita miliki di Python
   (Flask/FastAPI + SQLAlchemy + Alembic), jadi keuntungannya ~0 sementara biayanya nyata.
4. Robot tidak capek menulis boilerplate — keunggulan utama Laravel hilang.

⚠️ **Jangan pakai Deno Deploy** untuk proyek baru (dijadwalkan mati ~Apr 2027) — pakai Cloudflare Workers.

## Apa yang membedakan TanStack Start

> *"The framework does not replace the application model."* — Start **menambah lapisan server**
> di atas **TanStack Router** yang sudah matang; route/param/loader/link/boundary tetap milik Router.

Arsitektur 3 lapis: **Start server layer** (SSR/streaming/server functions/routes/middleware)
→ **TanStack Router** (route tree, URL state, loaders) → **aplikasi Anda** (komponen, data client).

Konsep kunci:
- **Server functions** (`createServerFn()`) — fungsi server bertipe, dipanggil dari komponen/loader;
  tidak perlu menulis endpoint API manual.
- **Tiga batas server**: server functions (pemanggil internal), server routes (API publik), middleware
  (auth/context/logging/policy).
- **File-based routing**: `src/routes/projects.$id.tsx` → `/projects/:id`.
- **Portable**: build pakai Vite atau Rsbuild; ganti host tanpa mengubah authoring route.
- Sumber: `tanstack.com/start/latest` (14,25 juta download/minggu; TanStack total 290,9 juta).

## Membuat proyek baru (resmi CF)

```bash
npm create cloudflare@latest -- my-app --framework=tanstack-start
npm run dev      # preview lokal
npm run deploy   # build + wrangler deploy
```

Untuk proyek yang sudah ada, tambahkan `@cloudflare/vite-plugin` + `wrangler`, pasang plugin
Cloudflare di `vite.config.ts`, lalu buat `wrangler.jsonc`:

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "my-app",
  "compatibility_date": "<tanggal hari ini>",
  "compatibility_flags": ["nodejs_compat"],
  "main": "@tanstack/react-start/server-entry",
  "observability": { "enabled": true }
}
```

`package.json` scripts: `dev: vite dev`, `build: vite build`, `deploy: npm run build && wrangler deploy`.

### Entrypoint kustom (untuk Queues / Cron / DO / Workflows)
Buat `src/server.ts` yang mengekspor handler default dan menambahkan `queue()`, `scheduled()`,
serta named export untuk Durable Objects/Workflows; lalu set `"main": "src/server.ts"`.

```ts
import handler from "@tanstack/react-start/server-entry";
export { MyDurableObject } from "./my-durable-object";
export default {
  fetch: handler.fetch,
  async queue(batch, _env, _ctx) { for (const m of batch.messages) { console.log(m.body); m.ack(); } },
  async scheduled(event, _env, _ctx) { console.log("Cron:", event.cron); },
} satisfies ExportedHandler<Env>;
```

Uji handler terjadwal lokal:
`curl "http://localhost:3000/cdn-cgi/local/scheduled?cron=*+*+*+*+*"`

### Binding Cloudflare (semua tersedia)
D1 (`env.DB`), R2 (`env.MY_BUCKET`), Queues, Cron Triggers, Durable Objects, Workflows,
Service Bindings (RPC antar-Worker). Contoh R2 dari server function:

```ts
import { createServerFn } from "@tanstack/react-start";
import { env } from "cloudflare:workers";
const uploadFile = createServerFn({ method: "POST" })
  .validator((d: { key: string; content: string }) => d)
  .handler(async ({ data }) => { await env.MY_BUCKET.put(data.key, data.content); return { success: true }; });
```

### Static prerendering
Set `tanstackStart({ prerender: { enabled: true } })` di vite config → HTML statis saat build,
disajikan sebagai static assets. Di CI, set `CLOUDFLARE_INCLUDE_PROCESS_ENV=true` agar env tersedia saat build.

## Pitfall & catatan
- **Status masih baru** (1.0 stable Okt 2026) — breaking change mungkin masih terjadi; validasi dulu
  di satu proyek kecil sebelum jadi standar tim.
- **Butuh React** — kalau tim belum familiar, ada kurva belajar (Solid juga didukung).
- **Tidak ada admin panel instan** seperti Filament Laravel — bikin sendiri.
- **Bukan pengganti panel Flask lama**: untuk kerja internal yang butuh MySQL/MariaDB lokal,
  tetap pakai Flask. TanStack Start untuk aplikasi web baru ber-SSR.
- Jangan menambah adapter lain (mis. `nitro()`) di vite config — hapus sebelum memakai plugin Cloudflare.
- Halaman CF Learning `cloudflare.com/learning/serverless/what-is-tanstack-start/` gagal di-fetch dari
  server kita (per Okt 2026) — pakai docs resmi `developers.cloudflare.com/workers/framework-guides/web-apps/tanstack-start/`.

## Foldkit — alternatif yang perlu dipantau (bukan untuk produksi, Okt 2026)

**foldkit.dev** — framework frontend **TypeScript** dibangun di atas **Effect** + **The Elm Architecture**.
Struktur program: satu **Model** immutable, **Message**, dan satu fungsi **update** murni; efek samping
dikembalikan sebagai **Command** (nilai), bukan panggilan tersembunyi. Ada Routing, Server Rendering
(SSG+SSR), UI components accessible, Submodels, ManagedResources, dan **DevTools**.

**⚠️ Kenapa BELUM dipakai di produksi kita:**
- **Pre-1.0 / Beta**, GitHub **~966 stars**, dibuat satu orang (Devin Jameson).
- **Server rendering = `foldkit/experimental/server`** — dokumentasinya sendiri menyatakan API bisa berubah
  di setiap rilis dan **belum punya "broad production exposure"**; untuk beban security-critical disuruh
  menunggu export stabil.
- Baru **1 production app** resmi (Typing Terminal), untuk SSG konten publik disebut "lowest-risk use today".
- Butuh **Effect** — kurva belajar curam.

**⭐ Yang benar-benar menarik dan layak dipantau: MCP native untuk AI agent.** Runtime data yang sama
diekspos ke agent lewat MCP: agent bisa membaca **Model** saat ini, menelusuri riwayat **Message**,
**rewind UI** ke state lampau, dan **dispatch Message**. Ini persis masalah yang kita hadapi saat debug UI
(agent tidak bisa "melihat" state). Kalau pola ini terbukti, framework lain akan meniru — tunggu versi matang.

**Testing (bagus):** *Story test* menguji state machine langsung (pure, tanpa DOM) dan *Scene test* menguji
lewat view dengan accessible locator (klik/ketik). Dokumentasinya jujur mencantumkan "think twice when":
rewrite dari codebase React besar, butuh ekosistem React, atau situs yang isinya kebanyakan tulisan
(disarankan Astro).

**Cara jalan di Cloudflare Workers** (dari docs CF): `npx create-foldkit-app@latest --name <app>`,
`npm i -D wrangler`, pilih mode render, lalu `wrangler.jsonc`:
- SPA  → `assets.directory = "./dist"` + `not_found_handling = "single-page-application"`
- SSG  → `assets.directory = "./dist/client"`
- SSR  → `main = "./dist/server/fetch.js"` + `assets.directory = "./dist/client"`

Butuh Node.js ≥ 22.22.2. Deploy: `npm run build && npx wrangler deploy`. Tidak ada status partner resmi CF.

## Posisi di stack kita
```
Flask/FastAPI (Python)  → panel backend & kerja internal (existing)
CF Workers (plain JS)   → gateway, bot, cron
TanStack Start (TS)     → web app full-stack baru (SSR + UI)  ← baru
Laravel (PHP)           → tidak dipakai
```
