---
name: memoh-platform-ops
description: "Use when deploying or operating Memoh self-hosted."
version: 1.0.0
---

# Memoh — multi-agent platform: deploy & operate

Memoh (`github.com/felinics/Memoh`, AGPL-3.0, Go+Vue) memberi **1 bot = 1 container** (filesystem +
Xvnc desktop + headed Chrome + kuota CPU/RAM sendiri). Bang memakainya sebagai **platform terpisah**,
bukan pengganti Hermes — segmennya beda (fleet multi-tenant vs personal agent).

Baca juga: `service-server-migration` Fase 7 untuk handoff host yang dikosongkan, dan
`references/memoh-api-and-mcp.md` untuk permukaan API + format body yang sudah diverifikasi.

## Gate WAJIB sebelum janji deploy: KVM, bukan OpenVZ/LXC
`memoh-server` membawa **containerd embedded** → butuh **privileged / nested container**.
Cek dulu: `systemd-detect-virt` → harus **kvm**. Kalau OpenVZ/LXC, backend `containerd` **gagal**
dan rutenya harus backend `docker` manual. Sampaikan ini sebagai prasyarat, bukan kejutan nanti.

## Install (satu perintah, dan dia MENOLAK root)
```bash
cd /opt/memoh
git clone --recurse-submodules --depth=1 https://github.com/felinics/Memoh.git repo
MEMOH_ALLOW_ROOT_INSTALL=true MEMOH_INSTALL_MODE=fresh sh repo/scripts/install.sh -y
```
- Installer **menolak jalan sebagai root** kecuali `MEMOH_ALLOW_ROOT_INSTALL=true`. Ini guard saja, tidak ada efek samping — di VPS khusus Bang aman di-override.
- Audit script dulu (aturan Bang untuk script pihak-3): `grep -nE "curl|wget|eval|rm -rf|systemctl|>/etc/" scripts/install.sh`. Yang kita temukan hanya `docker`, `curl` ke GitHub API, dan `rm -rf` di workspace-nya sendiri.
- Hasil: install minimal di **`/root/memoh/`** (clone dir dibersihkan otomatis; `/opt/memoh/repo` jadi sisa duplikat yang boleh dihapus).

## Arsitektur container (8 basis + 1 per bot)
| Container | Fungsi |
|---|---|
| `memoh-postgres` | DB utama (PostgreSQL) |
| `memoh-pgvector` | Vector DB terpisah (memory) |
| `memoh-migrate` | migrasi skema, one-shot (`Exited (0)` = sukses) |
| `memoh-server` | backend + **containerd embedded** (`privileged: true`, `pid: host`) |
| `memoh-channel` | service channel |
| `memoh-web` | Web UI (Vue 3), port **8082**; API **8080** |
| `memoh-webhook-tunnel` | cloudflared (profile, opsional) |
| `memoh-connect-it` | connector gateway (profile `connectors`) |
| `workspace-<bot-uuid>` | **1 per bot** — JALAN DI DALAM containerd nested, BUKAN di Docker host |

Bot container **tidak muncul di `docker ps`**. Verifikasi lewat containerd di dalam server:
```bash
docker exec memoh-server ctr -n default containers list
docker exec memoh-server ctr -n default tasks list    # → workspace-<uuid> | io.containerd.runc.v2 | RUNNING
```
Itu bukti pamungkas "1 bot = 1 container" beneran jalan.

Kelola: `cd /root/memoh && docker compose -f docker-compose.yml --profile connectors ps|logs -f|down`

## PostgreSQL WAJIB — versi ini tidak mendukung SQLite
`config.toml` memuat komentar eksplisit *"Memoh now supports PostgreSQL only"*. Saat Bang tanya
"pakai SQLite atau PG?" jawab dari config, bukan dari teks UI:
```bash
grep -A3 '^\[database\]' /root/memoh/config.toml    # driver = "postgres"
docker exec memoh-postgres psql -U memoh -d memoh -c '\dt'
```
UI menyebut "SQLite/Local stay graph-only" — itu untuk deployment lama, bukan opsi kita.

## 🔴 Jebakan terbesar: server HK DIBLOKIR OpenAI & Google
Region blokir itu **vendor decision**, bukan larangan pemerintah: OpenAI memblokir HK sejak Jul-2024
(diperlakukan sama seperti China mainland), dan **Gemini juga 403**. Jangan tawarkan proxy/VPN sebagai
solusi — OpenAI juga memblokir traffic VPN, dan akun bisa kena flag.

**Sebelum menjanjikan provider apa pun, scan dari server itu sendiri** (10 detik, read-only, tanpa key):
```bash
for u in https://api.openai.com/v1/models https://generativelanguage.googleapis.com/v1beta/models \
         https://api.jina.ai/v1/models https://api.cohere.com/v1/models https://api.mistral.ai/v1/models \
         https://api.deepseek.com/v1/models; do
  printf '%-58s ' "$u"; curl -s -o /dev/null -w '%{http_code}\n' -m 12 "$u"
done
```
Baca hasilnya: **403 = blokir region** (buang), **401 = jalan tapi butuh key** (kandidat),
**200 = jalan penuh**. Tabel hasil + alasannya ada di `references/memoh-api-and-mcp.md`.

## Model embedding: siapa yang TIDAK punya (jangan cek satu-satu lagi)
| Sumber | Kenapa tidak bisa |
|---|---|
| **DeepSeek** | tidak punya model embedding (hanya `deepseek-flash`, `deepseek-v4-pro`) |
| **Xiaomi MiMo Token Plan** | provider `xiaomi-tokenplan` eksplisit: *"does not support embeddings"* |
| **9router** | 91 model, **0** embedding |
| **OpenAI / Google** | blokir region dari HK |
| **Jina AI** | ✅ satu-satunya yang terbukti jalan dari HK |

LLM ≠ embedding. Model China jago chat tapi umumnya tidak menyediakan endpoint embedding; kalau
user bertanya "kenapa HS bisa pakai Xiaomi TP?" jawabnya: HS memakai Xiaomi untuk **fact extraction**
(LLM), sedangkan embedding-nya **lokal di dalam container** (model HuggingFace di-cache, mis.
`bge-small-en-v1.5`). Endpoint embedding HS **tidak di-expose ke luar** — jangan janjikan bisa dipakai
ulang oleh platform lain tanpa membuktikannya (`/v1/embeddings` di server itu → 404).

### Memasang embedding ke Memoh
Jina: provider `openai-completions`, base `https://api.jina.ai/v1`, model
`jina-embeddings-v5-text-small` (**1024** dim), `config.dimensions` **wajib**.
Bandingkan hasil dengan `POST /models/<id>/test` → `{"status":"ok","reachable":true}`.
Model chat dan embedding didaftarkan terpisah; hapus provider yang sudah mati
(`DELETE /providers/<id>` → 204) dan buktikan key-nya benar-benar hilang dari file + DB.

## MCP per bot — Jina memberi 22 tool ke bot
Memoh mendukung MCP (`type`: `stdio` | `http` | `sse`) dengan tabel `mcp_connections` per bot
(ada `tools_cache`, `last_probed_at`, OAuth 2.1). **`url` diletakkan di LEVEL ATAS body**, bukan
di dalam `config` — kalau ditaruh di `config` jawabannya `400 command or url is required`.
Simpan key di file sementara (`chmod 600`), kirim lewat script python — **jangan** lewat `argv`.
Urutan yang terbukti: `POST /bots/<id>/mcp` → **`POST /bots/<id>/mcp/<conn_id>/probe`** → cek
`tools_cache` berisi 22 tool. `?include_tags=search,read` di URL bisa memangkas context kalau perlu.

**Membuktikan tool benar-benar hidup (bukan cuma ke-list):** panggil MCP-nya langsung dengan
`curl` JSON-RPC. Wajib kirim **`Accept: application/json, text/event-stream`** (kalau hanya salah
satu → `406 Not Acceptable`). Responsnya format **SSE** (`event: message` + `data: {...}`) — parse
`data:` dulu, jangan `json.loads` seluruh body. Panggil satu tool murah (mis. `primer`) dan pastikan
hasilnya memuat data **server kita sendiri** (IP/region) — itu bukti nyata, bukan klaim.

## Mengirim pesan ke bot lewat API — format yang benar
```bash
curl -X POST "http://127.0.0.1:8080/bots/<bot_id>/web/messages" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":{"text":"..."}}'      # → 200 {"status":"ok"}
```
- Route **`/web/messages`** yang bekerja; `/message`, `/chat`, `/session/.../message` → 404.
- `follow-up-queue` BUKAN pintu masuk percakapan — `POST` ke situ butuh `invocation_id` + `text`
dan tetap balas **409 `queue_no_active_run`** kalau tidak ada run aktif. Pakai `/web/messages`.
- `POST` ke session baru akan **membuat session baru** (auto title-gen terlihat di log) —
  jadi jangan bingung pesan "tidak muncul" di session lama, cek title di `docker logs`.
Detail lengkap (termasuk endpoint model/provider/memory-provider) di `references/memoh-api-and-mcp.md`.

## 🔴 Endpoint API Memoh TANPA prefix `/api`
Hampir semua route ada di root server: `/providers`, `/models`, `/memory-providers`, `/bots/...`.
`/api/memory-providers` → **404**. Satu pengecualian: login jalan di **`/auth/login`**
(`/api/auth/login` membalas `missing or malformed jwt`). Token hasil login: `access_token`, umur 168h.

## Komunikasi ke Bang
- Bang memakai istilah **MCP** dan **TS** (= test/tes) — "TS MCP-nya bisa nggak tuh?" artinya
  **buktikan tool-nya jalan**, bukan cukup tampilkan daftarnya. Selalu panggil minimal satu tool
  dan tunjukkan output nyatanya.
- Laporan singkat + bukti: perintah, HTTP code, angka. Kalau belum tuntas, katakan apa adanya
  ("Pedro belum jawab, dugaan X") — jangan mengklaim selesai.
- Perubahan ke production/kredensial → minta **"gas?"** dulu; yang read-only boleh langsung jalan.

## Pitfalls
- **Jangan titipkan key layanan di `argv`.** Ambil nilainya dari API provider tempat key itu sudah
  tersimpan ke file `/tmp` (`chmod 600`), pakai dari file itu, lalu `shred -u`. Command line terlihat
  di `ps` dan di log tool.
- **`GET /bots/<id>/agents` kosong (`{"items":[]}`) saat bot tetap bisa merespons adalah normal** —
  jangan simpulkan "otak bot belum dipasang" dari endpoint itu saja, dan jangan pakai itu sebagai
  alasan menunda laporan. Kalau bot tidak membalas padahal pesan masuk (user tercatat, assistant
  0 char) dan log berhenti setelah `compaction: skipped`, laporkan sebagai **belum terverifikasi** +
  arahkan Bang tes dari Web UI — jangan bongkar konfigurasi bot atas dugaan.
- Jangan set token JWT Memoh ke tempat permanen; umurnya 7 hari dan biasanya cukup untuk sesi kerja.
