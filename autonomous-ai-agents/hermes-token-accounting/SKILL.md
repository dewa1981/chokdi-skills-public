---
name: hermes-token-accounting
description: "Use when asking how Hermes counts or meters token usage."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, tokens, usage, metering, billing, accuracy, insights]
---

# Hermes Token Accounting — bagaimana angka token dihitung & seberapa akurat

Jawaban source-verified (dibaca dari `/opt/hermes/agent/usage_pricing.py`, `conversation_loop.py`, `hermes_state.py`, `tools/transcription_tools.py` — 2026-08-14) untuk pertanyaan "kalkulasi input/output token akurat ga?" dan "kenapa angka usage beda dari bill provider?".

## Inti jawaban

**Angka token = dari RESPONSE API PROVIDER, bukan estimasi lokal.** Hermes TIDAK menghitung token sendiri (kecuali pre-flight context estimation). Alur:

1. Provider stream/response → objek `usage` (OpenAI: `prompt_tokens`/`completion_tokens`; Anthropic: `input_tokens`/`output_tokens`; Codex Responses: `input_tokens` + `input_tokens_details`).
2. `normalize_usage()` (`agent/usage_pricing.py`) → `CanonicalUsage` dengan bucket: `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `reasoning_tokens`. `prompt_tokens = input + cache_read + cache_write`; `total = prompt + output`.
3. Setiap API call dalam tool loop: `agent.session_*_tokens += ` (di `conversation_loop.py`) → `queue_token_counts()` → SQLite `sessions` + `session_model_usage` (per-model attribution).
4. `hermes insights` membaca `session_model_usage` (per-model rows) + reconcile residual terhadap `sessions` aggregate.

**Jadi akurat SEPANJANG provider mengirim usage.** Keakuratan = keakuratan angka yang dilaporkan backend (DeepSeek/OpenRouter/9router pass-through).

## Pitfall & caveat (yang bikin angka "beda")

- **Streaming usage datang di CHUNK TERAKHIR** (`chunk.usage` dengan `choices: []`). Kalau stream putus SEBELUM final chunk (provider drop/error), usage chunk itu HILANG → angka undercount untuk call tersebut. Ini satu-satunya jalur undercount yang nyata.
- **`stream_options: {include_usage: true}`** dikirim otomatis (kecuali native Gemini) — 9router/OpenAI-compat harusnya balas usage; kalau proxy strips usage → 0 tercatat.
- **Cost = ESTIMASI harga publik, BUKAN invoice provider.** `estimate_usage_cost()` pakai pricing dari official-docs snapshot / OpenRouter models API / custom endpoint `/models` metadata. Untuk provider `custom` (9router) dengan model tidak dikenal → `status: unknown`, cost di-drop. Kalibrasi ke bill aktual kalau dipakai untuk tagihan klien.
- **Reasoning tokens dihitung terpisah** (`completion_tokens_details.reasoning_tokens` / `output_tokens_details.reasoning_tokens`) — model reasoning (deepseek-v4-flash) bisa bakar 21K reasoning token untuk 500 visible token; total output tetap masuk `output_tokens`, reasoning cuma bucket tambahan buat analisa.
- **Cache tokens DIPISAH dari input** — `input_tokens` di normalize = `prompt_total − cache_read − cache_write` (OpenAI/Codex contract: prompt total SUDAH termasuk cached; details object yang memecah). Kalau proxy tidak kirim `prompt_tokens_details` → cache read/write = 0 dan input = total.
- **DeepSeek native** kirim cache hit sebagai top-level `prompt_cache_hit_tokens` (bukan nested) — normalize_usage handle ini.
- **Aux calls (vision, compression, title gen, session_search)** dicatat TERPISAH via `aux_accounting.py` → `session_model_usage` dengan kolom `task` (mis. `vision`). `hermes insights` MENJUMLAHKAN aux rows ke total (agar tidak undercount) — kalau angka insights > jumlah main-loop, itu karena aux.
- **Aux streaming**: `_validate_llm_response` chokepoint di `auxiliary_client.py` — non-streaming aux SUDAH tercatat; streaming aux yang gagal di tengah bisa tidak tercatat.
- **MoA (mixture-of-agents)**: advisor fan-out di-fold ke token counts + cost turn (priced per advisor model rate) — jangan double-count manual.
- **Session counters reset** di `reset_session_state()` (`run_agent.py`) — `/new` = fresh 0. Gateway `reset_session()` bikin session id baru.
- **`session_model_usage` vs `sessions` row**: session yang switch model mid-flight terpecah per model di table usage; `sessions` row cuma satu pasangan (model, billing_provider) — jangan samakan kolom `sessions.model` dengan breakdown per-model.

## Kalibrasi / verifikasi cepat

- `hermes insights --days N` (per profile: `HERMES_HOME=/opt/data/profiles/<p>`) — parse Input/Output/Total tokens.
- Bandingkan dengan log API: `grep "API call #" ~/.hermes/logs/agent.log` → `in=`/`out=` per call (sum = session total).
- Cek row: `sqlite3 state.db "SELECT input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens, api_call_count FROM session_model_usage ..."`.
- Kalau angka 0 / undercount → cek apakah provider stream kirim final usage chunk (test `curl` stream langsung), bukan bug Hermes.

## Kenapa ini penting untuk bisnis jualan agent

- Billing per customer pakai `hermes insights` per profile → angka ini = basis tagihan. Karena cost itu ESTIMASI harga publik, untuk invoice klien kalibrasi dengan bill aktual 9router/provider.
- `user_allowed_commands` TIDAK boleh include `/model` (customer bisa ganti ke model mahal → tagihan membengkak) — lihat `hermes-staff-agent-profiles` untuk pola gating lengkap.

## Analisis export usage DeepSeek platform (Bang kirim ZIP dari platform.deepseek.com)

Pola lengkap + insight real ($6.83/hari, cache-hit 81%, miss = 82% biaya): `references/deepseek-platform-usage-export.md`.
Ringkas: export = 2 CSV (cost + amount per jam, BOM `utf-8-sig`); biaya terbesar hampir selalu
**input cache-MISS** bukan output; naikkan cache hit dengan prompt template konsisten.

