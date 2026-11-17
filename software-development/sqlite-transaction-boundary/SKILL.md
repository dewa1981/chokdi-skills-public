---
name: sqlite-transaction-boundary
description: "Use when SQLite corrupts or locks up under writers."
version: 1.0.0
author: chokdi_staging (pola dari OpenClaw)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sqlite, database, corruption, transaction, wal, lock]
    category: software-development
---

# SQLite Transaction Boundary

Pelajari kenapa DB SQLite korup dan cara mencegahnya. Pola ini diambil dari lint
OpenClaw (`check-sqlite-transaction-boundary.mts`) — mereka menghapus SEMUA primitif
transaksi async dan menegakkan aturan lewat lint otomatis.

## Aturan Emas

> **Siapkan async SEBELUM transaksi, validasi & tulis DI DALAM callback SYNC.**

```python
# ❌ SALAH — async/network di dalam transaksi
async with conn.transaction():
    data = await fetch_remote()      # lock ditahan selama network call
    await conn.execute("INSERT ...", data)

# ✅ BENAR — async di luar, tulis sync & cepat
data = await fetch_remote()
with conn:
    conn.execute("INSERT ...", data)
```

Akibat melanggar: transaksi kebuka lama → lock ditahan → WAL numpuk → crash di
tengah tulis = **KORUP**.

## 3 Pola Pelanggaran yang Harus Dicegah

| # | Pola | Contoh |
|---|---|---|
| 1 | Import primitif transaksi async | `import ...SqliteImmediateTransactionAsync` |
| 2 | Deklarasi fungsi transaksi async | `async def ..._write_transaction_async(...)` |
| 3 | **Callback async ke helper sync** | `run_state_write_transaction(async (tx) => {...})` |

**#3 paling halus** — deteksi harus mencakup: arrow `async`, function expression
`async`, identifier yang merujuk async function lokal, dan **alias import**.

## Aturan praktis (SQLite apapun)

1. Transaksi harus **pendek** — NOL network call, NOL `await` di dalamnya.
2. `BEGIN IMMEDIATE` untuk tulis kritis — ambil write lock LEBIH AWAL, hindari deadlock.
3. **Satu writer per DB.** Butuh banyak? Pecah DB (pola NanoClaw: DB per-session).
4. **Lock di DB terpisah**, jangan di DB utama (pola OpenClaw `*.lock.sqlite`).
5. **Checkpoint WAL** — kalau `*-wal` lebih besar dari DB utama, ada masalah.

## Checklist audit (jalankan saat DB bermasalah)

- [ ] Berapa proses yang MENULIS ke DB ini? (>1 = bahaya)
- [ ] Ada `await` / network call di dalam transaksi?
- [ ] Ada transaksi yang bisa jalan >1 detik?
- [ ] WAL membengkak tanpa checkpoint? (`*-wal` > DB utama)
- [ ] `BEGIN IMMEDIATE` dipakai untuk operasi tulis kritis?
- [ ] Lock ada di DB terpisah atau di DB utama?
- [ ] Ada guard/lint yang menegakkan aturan di atas?

## Data nyata (perbandingan agent, 12 Sep 2026)

| Sistem | DB | Penanganan |
|---|---|---|
| Hermes `state.db` | SQLite | 1-writer rule (workaround) |
| NanoClaw `v2.db` | SQLite | **DB per-session** (hindari contention) |
| OpenClaw `openclaw.sqlite` | SQLite | **lint boundary + lock terpisah** + `sqlite-vec` |
| nanobot `llm_usage.sqlite3` | SQLite | kecil, jarang tulis |
| IronClaw | **PostgreSQL** | MVCC native (hilangkan masalah by design) |

**Kesimpulan:** DB korup BUKAN karena SQLite jelek — tapi karena boundary transaksi
tidak ditegakkan. OpenClaw membuktikan SQLite aman kalau disiplin. PostgreSQL =
jalan pintas yang menghilangkan masalah by design (tapi butuh server).

## Konteks kita

Hermes `state.db` staging pernah korup karena **2 proses menulis** (webui-safe 8899
vs hermes-serve 9119). Solusi yang dipakai: **1-writer rule** (matikan 9119
permanen). Separuh solusi lainnya = disiplin boundary di atas, yang belum ditegakkan.

## Kalau ketemu DB korup di sistem kita

```bash
# 1) cek siapa yang nulis
lsof /root/.hermes/state.db 2>/dev/null | head
fuser -v /root/.hermes/state.db 2>/dev/null

# 2) cek WAL membengkak
ls -la /root/.hermes/state.db*

# 3) integritas
sqlite3 /root/.hermes/state.db "PRAGMA integrity_check;"     # harapkan: ok

# 4) perbaiki (HANYA kalau rusak)
sqlite3 state.db ".recover" | sqlite3 state.db.recovered

# 5) restore dari backup TERDEKAT sebelum korupsi
#    R2 06:00 / Box 15:00 — jangan ambil yang lebih lama
```
