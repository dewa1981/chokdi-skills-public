# Memoh API + MCP — permukaan yang sudah diverifikasi

Semua contoh di bawah dijalankan dari **dalam server Memoh** (`http://127.0.0.1:8080`).
Token: `POST /auth/login` → `access_token`.

## 🔴 Aturan routing
Hampir semua route **TANPA prefix `/api`**. `/api/memory-providers` → 404, `/memory-providers` → 200.
Satu pengecualian: login di **`/auth/login`**.

## Menemukan route yang tidak terdokumentasi
Dua teknik yang terbukti, dari yang paling murah:

1. **Baca test file di repo upstream** — paling akurat, karena test meng-enumerasi route beserta method:
   ```bash
   git clone --depth=1 --filter=blob:none --sparse https://github.com/felinics/Memoh.git memoh_src
   cd memoh_src && git sparse-checkout set internal/handlers internal/channel
   grep -rn 'sessions/:session_id' internal/handlers/*_test.go
   ```
   `session_queue_test.go` memuat daftar `method + route` yang valid — itu cara menemukan
   `POST /follow-up-queue` dan membedakannya dari fiktif.
2. **`OPTIONS` untuk menemukan method yang diizinkan** sebelum menebak body:
   ```bash
   curl -s -i -X OPTIONS "$URL" -H "Authorization: Bearer $T" | grep -iE '^HTTP|^allow'
   # → "Allow: OPTIONS, GET, POST"
   ```
   Ini yang mengungkap `/queue` hanya `GET` sementara `/follow-up-queue` menerima `POST`.
3. `strings <binary> | grep -oE '/bots/\{bot_id\}/[a-z0-9/{}/_-]*'` untuk peta kasar route.
   **Jangan** grep patch lebar tanpa pola — pernah timeout 180 detik di binary 1+ GB.

## Struktur request yang benar (setelah ditebak, diverifikasi dari kode)
| Operasi | Body |
|---|---|
| Login | `{"username":"admin","password":"..."}` |
| Tambah provider | `{"provider_template_id":"<uuid>","name":"...","client_type":"openai-completions","icon":"openai","enable":true,"config":{"api_key":"...","base_url":"..."}}` |
| Tambah model embedding | `{"provider_id":"<uuid>","model_id":"...","name":"...","type":"embedding","enable":true,"config":{"dimensions":1024}}` |
| Tambah MCP | `{"name":"jina","type":"http","is_active":true,"url":"https://mcp.jina.ai/v1","headers":{"Authorization":"Bearer <key>"}}` |
| Kirim pesan | `{"message":{"text":"..."}}` |

**`code` (bukan `curl` mentah) lebih aman untuk body berisi key** — key dibaca dari file.

## Endpoint yang berguna
```
POST   /auth/login                          → access_token (umur 168h)
GET    /providers                            → daftar provider + config (key ter-mask)
POST   /providers                            → 201; butuh provider_template_id
DELETE /providers/<id>                       → 204
GET    /provider-templates                   → 43 template, domain: llm|speech|transcription|video
GET    /models                               → daftar model
POST   /models                               → 201; type: chat|embedding|image|speech|transcription|video|vision
POST   /models/<id>/test                     → {"status":"ok","reachable":true,"latency_ms":N}
GET    /memory-providers                     → provider memory terpasang + config
GET    /memory-providers/meta                → schema tiap provider (builtin|mem0|openviking)
GET    /bots/<bot_id>/sessions               → daftar session
GET    /bots/<bot_id>/messages?session_id=X  → riwayat pesan
POST   /bots/<bot_id>/web/messages           → KIRIM PESAN (200 {"status":"ok"})
GET    /bots/<bot_id>/mcp                    → daftar MCP connection + tools_cache
POST   /bots/<bot_id>/mcp                    → 201; url di level atas
POST   /bots/<bot_id>/mcp/<id>/probe         → 200; {"status":"connected","tools":[...]}
GET    /bots/<bot_id>/agents                 → {"items":[]}  (lihat pitfall di SKILL.md)
```

## Memory provider: siapa yang bisa self-host
Dari `GET /memory-providers/meta` (sumber kebenaran, bukan blog):

| Provider | Deskripsi base_url di schema | Self-host? |
|---|---|---|
| `builtin` | punya field `embedding_model_id` + `memory_mode` | — (bawaan) |
| `openviking` | *"OpenViking API base URL (self-hosted or SaaS)"*, contoh **`http://openviking:8088`** | ✅ **BISA** |
| `mem0` | *"Mem0 SaaS API base URL. Defaults to https://api.mem0.ai"* | ❌ SaaS-only |

**Cara membaca bukti ini:** contoh default `http://openviking:8088` memakai **nama service Docker**,
bukan domain internet — itu tanda Memoh memang dirancang jalan satu jaringan dengan container
OpenViking. Ditambah adapter `internal/memory/adapters/openviking/openviking.go` dengan 15 method
(`Add`, `Search`, `GetAll`, `Update`, `Delete`, `Compact`, `Rebuild`, ...).
OpenViking sendiri = **1 container** all-in-one (port 1933, workspace di filesystem lokal, tanpa DB
eksternal); Mem0 = **3 container** (API + Postgres/pgvector + Neo4j).

## Tabel hasil scan provider dari server HK

| Provider | HTTP | Arti |
|---|---|---|
| OpenAI | **403** | blokir region (`unsupported_country_region_territory`) |
| Google Gemini | **403** | blokir region |
| Jina AI | **200** | jalan penuh |
| Cohere / Mistral / DeepSeek | 401 | jalan, butuh key |
| DashScope (Alibaba) / Ark (Volcengine) / SiliconFlow | 401 | jalan, butuh key |
| Voyage | 404 | endpoint berbeda — perlu ditelusuri ulang |

**Volcengine Ark tidak layak dicoba**: registrasinya menuntut **nomor HP China (+86)**.

## Membuktikan MCP hidup — JSON-RPC langsung
```bash
curl -s -X POST https://mcp.jina.ai/v1 \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \   # WAJIB dua-duanya, kalau tidak → 406
  -H "Authorization: Bearer $KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
# → SSE: "event: message" lalu "data: {\"result\":{\"tools\":[...]}}"
```
Parse `data:` dulu (`re.search(r"data:\s*(\{.*\})", txt, re.S)`), baru `json.loads`.
Panggil satu tool murah untuk bukti fungsi:
```bash
-d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"primer","arguments":{}}}'
# → timestamp + client IP + country + ASN **server kita sendiri** = bukti eksekusi nyata
```

## Catatan Jina MCP
Dokumentasi menyebut 19 tool; instance **live** mengembalikan **22** (plus `search_web_deep`).
Jangan mengoreksi angka dari dokumen — hitung dari respons `tools/list`.
Filter server-side menghemat context: `?include_tags=search,read`, `?exclude_tags=parallel`.

## Sisa kerja yang belum tuntas saat serah terima
- Bot pertama (`Pedro`) belum membalas pesan walau pesan tercatat (assistant 0 char); log berhenti
  setelah `compaction: skipped`. Belum terverifikasi penyebabnya — **arahkan Bang tes dari Web UI**
  sebelum menyimpulkan apa pun tentang konfigurasi agent/workspace.
- Belum: sambung ke Telegram, test memory end-to-end, CF Tunnel, resource limit per bot, backup
  `config.toml` + `.env` + `docker-compose.yml`.

Penuh catatan deploy ada di brain-vault: `server-ano99/apps/memoh/README-memoh-hk.md`.
