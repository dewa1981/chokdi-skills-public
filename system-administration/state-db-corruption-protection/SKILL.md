---
name: state-db-corruption-protection
description: Use when state.db korup atau gateway ganda.
---

# Proteksi Korupsi state.db (Hermes)

## ⛔ LARANGAN KERAS: JANGAN BUKA state.db LIVE (13-Sep-2026 — insiden nyata)

**Gejala ini BUKAN korupsi, tapi `DeletedWalGenerationError`:**
```
FATAL: a live process holds a deleted state.db-wal or state.db-shm inode
       while the path names a different (or missing) generation
```
User melihat: *"session history is temporarily unavailable"* / *"pesan tidak diproses"*.
`/new` cuma menyembunyikan sebentar — gejalanya bertahan sampai gateway di-RESTART.

**Mekanisme:** di mode WAL, SQLite **menghapus** `state.db-wal`+`-shm` saat koneksi terakhir menutup.
Kalau gateway sedang **idle** (tidak pegang lock), proses LAIN yang membuka+menutup `state.db`
(detik `sqlite3`, skrip python read-only, `cp` mentah) memicu penghapusan itu → gateway masih
pegang **inode lama yang sudah deleted** → Hermes sengaja HALT semua penulisan (safety) → error.

**Pemicu nyata di insiden 13-Sep** (setiap kejadian meninggalkan folder penanda
`/root/.hermes/state.db.retired-wal-<UTC>-<pid>/`):
| Waktu | Pemicu |
|---|---|
| 13:42 & 13:48 | **Agent membaca DB live pakai `sqlite3`/python untuk verifikasi** (10 detik setelahnya) |
| 13:55 | bot menjalankan maintenance/CLI |

### ✅ Cara aman memeriksa isi DB — SELALU SALIN DULU
```bash
D=/tmp/vc_$$; mkdir -p $D
cp /root/.hermes/state.db      $D/state.db
cp /root/.hermes/state.db-wal  $D/state.db-wal 2>/dev/null
cp /root/.hermes/state.db-shm  $D/state.db-shm 2>/dev/null
sqlite3 $D/state.db "select id, role, substr(content,1,60) from messages order by id desc limit 10;"
rm -rf $D
```
**JANGAN** pakai `sqlite3 'file:/root/.hermes/state.db?mode=ro'` — mode=ro TIDAK menyelamatkan;
perintah `sqlite3` CLI di dokumen ini pun hanya boleh dijalankan pada **salinan**.

### ⛔ Aturan maintenance DB
1. **Dilarang** `VACUUM` / `wal_checkpoint` / `optimize` / hapus-rename `state.db*` **saat gateway jalan**.
2. Operasi DB (update Hermes, VACUUM, cleanup, hapus DB korup) → **stop gateway dulu**, kerjakan,
   baru start — atau jadwalkan jam **03:00** saat sepi.
3. Setelah operasi DB apa pun → **restart gateway** + verifikasi (checklist di bawah).
4. Jangan bikin penulis kedua dengan `HERMES_HOME` yang sama (`/root/.hermes`).

### ✅ Checklist verifikasi TANPA buka DB
```bash
export XDG_RUNTIME_DIR=/run/user/0
systemctl --user is-active hermes-gateway.service                              # harus: active
ps -eo pid,args | grep -cE '^ *[0-9]+ /usr/local/lib/hermes-agent/venv/bin/python -m hermes_cli\.main gateway run'   # harus: 1
lsof +L1 2>/dev/null | grep -c state.db                                        # harus: 0
stat -c '%s byte | %y' /root/.hermes/state.db-wal                              # mtime harus bergerak
grep -hE "^$(date +%F) " /root/.hermes/logs/agent.log | grep -cE "DeletedWalGenerationError|refused further writes"
```
**SEHAT** = active + gateway 1 + deleted 0 + WAL bergerak + error baru 0.

**Fix cepat kalau gejala muncul lagi:** `bash /root/scripts/state_db_autoheal.sh`
(auto jalan tiap 2 menit juga). **JANGAN** coba hapus/rename WAL sendiri saat gateway hidup.

## ⛔ RESTART SAJA TIDAK CUKUP — WAJIB "HEAL BERSIH" (13-Sep-2026, pelajaran mahal)

**Jebakan yang bikin loop berulang:** kalau restart gateway saat `state.db-wal`/`-shm` **sisa generasi
lama masih ada di path**, Hermes akan **memensiunkan (retire) WAL itu** (muncul folder
`state.db.retired-wal-<UTC>-<pid>/`) **TANPA membuka handle baru** → penulisan **HALT lagi**.
Akibatnya: `restart → retire → halt → watchdog restart → retire lagi` = **loop, bukan fix**.

Bukti: semua folder retire dibuat **beberapa detik setelah gateway start** (13:34→13:42,
13:47→13:48, 14:16:02→14:16:04, 14:20→14:20:10).

### ✅ PROSEDUR "HEAL BERSIH" (ini yang benar)
```bash
# 1. STOP gateway
export XDG_RUNTIME_DIR=/run/user/0
systemctl --user stop hermes-gateway.service
sleep 3
systemctl --user is-active hermes-gateway.service   # pastikan 'inactive'

# 2. BACKUP dulu (state.db + wal + shm)
STAMP=$(date +%Y%m%d_%H%M%S); BK=/opt/backup/dbclean_$STAMP; mkdir -p $BK
cp /root/.hermes/state.db     $BK/ 2>/dev/null
cp /root/.hermes/state.db-wal $BK/ 2>/dev/null
cp /root/.hermes/state.db-shm $BK/ 2>/dev/null

# 3. CHECKPOINT (gateway MATI = aman)
sqlite3 /root/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"
sqlite3 /root/.hermes/state.db "PRAGMA quick_check;"     # harus 'ok'

# 4. ⭐ BUANG WAL+SHM sisa (LANGKAH KUNCI — kalau tidak, halt lagi)
rm -f /root/.hermes/state.db-wal /root/.hermes/state.db-shm

# 5. START gateway
systemctl --user start hermes-gateway.service
sleep 8

# 6. VERIFIKASI
lsof +L1 2>/dev/null | grep -c "state.db"          # HARUS 0
ls -d /root/.hermes/state.db.retired-wal-* | wc -l # TIDAK bertambah
```
**Inti perbaikannya = langkah 4.** Tanpa itu, restart apa pun cuma mengulang siklus.

### Aturan turunan
- Operasi DB (upgrade/VACUUM/optimize/cleanup) **WAJIB stop gateway dulu**, lalu **buang WAL+SHM**
  sebelum start. Cron optimize yang jalan saat gateway hidup = **landmine**.
- **Jangan** "perbaiki" dengan restart berulang tanpa bersihin WAL — itu loop.
- Script `state_db_autoheal.sh` v2+ sudah memakai prosedur ini (bukan restart polos). Kalau mengganti
  script itu, **pertahankan langkah 4**, jangan disederhanakan jadi `systemctl restart` saja.
- Indikator pantau tambahan: `ls -d /root/.hermes/state.db.retired-wal-* | wc -l` — jumlahnya
  **tidak boleh bertambah** (retire baru = ada halt baru).

**Versi Hermes:** v0.21.2+ menolak menulis alih-alih korup (proteksi benar). Sebelumnya kelas bug ini
bisa langsung merusak DB.

## Gejala
- `sqlite3.DatabaseError: database disk image is malformed`
- `Session DB transcript append failed ... file is not a database`
- `Rebuilt N Session DB FTS index(es) after append corruption`
- `exited UNCLEANLY (no exit path ran — SIGKILL / OOM / VM death)` di lifecycle ledger

## Root cause (urut skor)
1. **Gateway ganda** (2 proses nulis SQLite yang sama = race condition) — PALING SERING
2. I/O disk error (`WAL journal_mode unsupported ... disk I/O error`)
3. Kill paksa (SIGKILL) saat DB sedang nulis
4. WAL kehapus / backup cp mentah saat live (sudah fixed: pakai `sqlite3 .backup`)

## Diagnosa cepat
```bash
# integrity + isi
sqlite3 'file:/root/.hermes/state.db?mode=ro' 'PRAGMA integrity_check; SELECT COUNT(*) FROM messages;'
# proses gateway ASLI (bukan bash wrapper!)
ps -eo pid,args | grep -E '^ *[0-9]+ /usr/local/lib/hermes-agent/venv/bin/python -m hermes_cli\.main gateway run' | grep -c .
# unit systemd
systemctl --user cat hermes-gateway.service | grep -E 'KillSignal|KillMode|Restart='
# timeline korupsi di log
journalctl --user -u hermes-gateway.service --since "2026-08-30 15:00" | grep -iE 'killed|malformed|corrupt'
```

## Proteksi yang dipasang (staging, 30-Agu-2026)

### 0. Lesson 04-Sep-2026 (maintenance tuntas):
- JANGAN biarkan file state.db.corrupt-*/bad-*/malformed-*/pre-* menumpuk lama di ~/.hermes —
  bisa 5.4GB+ (15 file, 290-422MB tiap) & bikin backup/monitoring berantakan. Setelah insiden
  pulih, ARSIP mk k folder lalu HAPUS (sudah ada backup sehat R2/Box 06:00 & 15:00).
- optimistic optimize cukup Minggu; buat DB >300MB/pernah korup → naikin ke **Sen/Rab/Jum 04:00**
  (cron `0 4 * * 1,3,5`) biar checkpoint+VACUUM lebih rajin.
- Tracker `state.db.repair-attempts.json` `failed_attempts` lama → nol-kan + `resolved:true`
  saat korupsi sudah recover sukses (biar monitoring tak false-alarm).
- Verifikasi single-writer: pakai `lsof ~/.hermes/state.db` (bukan grep ps count → false positive);
  yg benul cuma proses hermes gateway 1 utk file itu, + serve/webui mati.

### 1. VACUUM + backup dulu
```bash
sqlite3 /root/.hermes/state.db ".backup '/root/backups/state.db.pre-vacuum-<stamp>'"
# lalu VACUUM via python (busy_timeout 60s)
```
`auto_prune: true` + `retention_days: 90` di config.yaml + optimize-state-weekly.sh (Minggu 04:00, `hermes sessions optimize`).

### 2. Watchdog anti-gateway-ganda → /root/scripts/watchdog_gateway_single.sh, cron */2
PENTING: **JANGAN pakai `pgrep -f 'gateway run'`** — false positive match ke bash wrapper terminal (command-nya mengandung string itu) → bisa salah-kill proses terminal!
Pattern aman:
```bash
ps -eo pid,args | grep -E '^ *[0-9]+ /usr/local/lib/hermes-agent/venv/bin/python -m hermes_cli\.main gateway run' | awk '{print $1}'
```
Logika: count >1 → SIGTERM yang lama, sisakan terbaru; kalau masih hidup setelah 10s → SIGKILL. Notif Telegram ke grup notif.

### 3. Restart graceful
Unit systemd user harus: `KillSignal=SIGTERM`, `KillMode=mixed`, `Restart=always`, `TimeoutStopSec=70`.
JANGAN restart manual dengan `nohup ... &` — bisa spawn gateway DOBEL (nohup + systemd Restart=always). Pakai `systemctl --user restart hermes-gateway.service`.

## SOP restart gateway
1. Backup dulu (sqlite3 .backup)
2. `systemctl --user restart hermes-gateway.service` (SIGTERM graceful)
3. Verify: count == 1, integrity ok, Telegram connected

## Verify setelah proteksi
- `integrity_check` = ok
- count gateway asli == 1
- unit punya KillSignal=SIGTERM
- cron watchdog terpasang
