---
name: cpu-load-saturation-forensics
description: Use when CPU 100% / load >> nproc and services go silent.
version: 1.0.0
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [cpu, load, systemd, cgroup, cron, diagnostics, vps, gateway]
---

# CPU / Load Saturation Forensics

Kelas kerja: host penuh (CPU 100%, load >> nproc) dan akibatnya layanan di atasnya
tampak "mati" — bot tidak membalas, gateway `activating (auto-restart)`, ada
`status=9/KILL` di journal. Tujuannya menemukan PEMAKAN yang sebenarnya dengan
bukti, bukan menebak proses yang kebetulan paling besar di layar.

Dipakai juga saat user menuduh bot/profile tertentu ("bot X yang bikin CPU naik") —
tuduhan itu hipotesis, bukan temuan.

## When to Use

- Host dilaporkan CPU 100%, `load average` jauh di atas jumlah core.
- Bot/agent/daemon tidak merespon padahal prosesnya ada; `systemctl` bilang
  `activating (auto-restart)` dengan `NRestarts` besar.
- User menuduh profile, bot, atau script tertentu sebagai penyebab beban.
- Setelah reboot host, beban langsung penuh lagi.

## Aturan inti

1. **Ukur kapasitas dulu.** `nproc`, `cat /proc/loadavg`, `top -bn1 | grep '%Cpu'`.
   load 30 di 3 core = 10x jenuh; `0.0 id` = benar-benar penuh. Tanpa `nproc`,
   angka load tidak berarti apa-apa.
2. **Atribusi lewat cgroup, bukan nama proses.** Semua bot/script bernama
   `python3`. `cat /proc/<pid>/cgroup` memetakan PID ke unit systemd
   (`cron.service` / `hermes-gateway-<profile>.service` / `none`).
3. **Buang `ps` dari daftar pemakan.** `ps --sort=-pcpu` selalu menampilkan dirinya
   sendiri 100-300%. Tanpa filter `comm!="ps"` laporan "pelaku terbesar" jadi palsu.
4. **Cek `etime`/`up` tiap proses gateway.** Kalau semuanya puluhan detik, mereka
   baru booting/restart — CPU tinggi itu GEJALA, bukan sebabnya.
   Kalau counter `NRestarts` masih naik sementara `up` pendek-pendek: ini **kill loop**,
   bukan beban kerja. Jangan lanjut tuning cron/sizing — pindah ke
   `sigkill-root-cause-tracing` (bpftrace, cari `sinyal=9`, resolusi PID pembunuh) dan
   buktikan pembunuhnya sebelum menyentuh apa pun. Beban kerja hanya pelaku kalau
   `NRestarts` BEKU antar dua sampel.
5. **Cari tunas yang memakan CPU lama, bukan yang ramai sesaat.** Snapshot `top`
   menangkap script cron yang baru lahir (`up=00:00`) dan bisa menggeser perhatian
   dari proses panjang (`up=10:59:37`) yang terus-menerus memakan CPU. Urutkan juga
   berdasarkan `etimes` (umur) dan agregat per nama perintah, jangan hanya `%CPU
   saat ini`.
5. **Cek cron sebelum menyalahkan aplikasi.** `* * * * *` sering lebih rapat dari
   dugaan; satu file bisa memuat beberapa baris untuk script yang sama (dipisah
   `sleep 12;` / `sleep 30;`) sehingga tetap beberapa proses per menit.
6. **`NRestarts=0` bukan bukti tidak bersalah.** Profile yang unitnya sehat tetap
   bisa punya cron pemakan CPU. Cek `NRestarts` DAN `cron/jobs.json`-nya.
7. **Satu frame `top`/graf tidak memvonis.** Laporkan `loadavg` + `idle%` bersama;
   loadavg = rata-rata 1/5/15 menit, jadi tetap tinggi walau idle sudah pulih.
8. **Kalau fix tidak menurunkan beban, ukur ulang** — jangan matikan proses lain
   satu-satu. Pola "banyak proses kecil berebut" tidak beres dengan satu kill.
9. **JANGAN mask/disable unit gateway massal.** `systemctl mask` pada unit yang
   sedang selalu dijalankan (`Restart=always`, `StartLimitIntervalSec=0`) bisa
   memicu systemd berhenti merespon perintah lain — `list-units`, `enable --now`,
   bahkan query bisa balik kosong, dan bot lain yang tidak dimaksudkan ikut diam.
   Hentikan per proses (kill PID setelah dipastikan induknya), bukan dengan
   operasi unit massal. Kalau user memang minta host bersih, itu reboot/opin user,
   bukan hak agent.
10. **Tidak ada "stagger delay" yang bisa mengakali sizing.** Menyalakan N gateway satu per
    satu dengan `sleep 10/30` TIDAK menurunkan beban total — tiap gateway yang sudah naik tetap
    memakan CPU permanen (±5-10% sesudah stabil). 19 gateway × 10% = 190-300% di host 3 core:
    tetap jenuh, cuma lebih lambat mencapainya, dan loadavg malah naik bertahap. Kalau total
    kebutuhan > kapasitas, satu-satunya jalan adalah mengurangi jumlah bot ATAU menambah core;
    sebutkan itu sebelum menjalankan script start bertahap, jangan sesudah.
11. **Runtime yang baru di-upgrade membangun ulang environment-nya sendiri.** Sesudah
    `git reset` + `pip/uv install -e`, `hermes-webui.service` menjalankan `uv sync --frozen`,
    `pip_compileall` dan `pm/worker.py` selama 1-3 menit dengan total 200-260% CPU. Semua prosesnya
    ber-`up=00:0X` dan unit-nya `hermes-webui.service` → **tunggu dulu**, jangan dianggap pelaku
    baru. Kalau setelah 5 menit masih nge-gas, baru stop unit WebUI-nya.
12. **`PRAGMA quick_check` per profile = spike CPU berulang tiap cron tick.** Watchdog yang memanggil
    `quick_check` pada 20+ `state.db` (satu 994 MB, dua 291 MB) memakan satu core penuh tiap
    DB besar dan terlihat di `top` sebagai satu proses `python3 -c import sqlite3 ...` berumur
    0-1 detik, berulang dari `cron.service`. Identifikasi lewat isi cmdline (bukan nama file
    script — yang muncul adalah python inline `-c`). Untuk server yang tidak lagi butuh auto-restore,
    komentari baris cron watchdog-nya; jangan diganti dengan tuning yang lebih ringan tanpa izin
    pemilik.
13. **Hentikan profile utuh sebelum menyimpulkan sizing:** set semua job di
   `profiles/<x>/cron/jobs.json` jadi `enabled:false` + backup file-nya ke folder
   persisten, lalu matikan prosesnya. Bandingkan `loadavg` sebelum/sesudah 2 menit.
   Ini cara tercepat memisahkan "cron profile ini penyebab" dari "host memang
   kurang core" — dan verifikasinya bukan exit code, tapi angka load sesudahnya.
11. **Proses tersembunyi di systemd user & WebUI.** `systemctl list-units` (system)
   TIDAK menampilkan `hermes-gateway.service` milik user (`unit=user@0.service`),
   dan `hermes-webui.service` punya `pm/worker.py` yang bisa memakan 100% CPU saat
   render/compile. Keduanya harus masuk laporan walau bukan bot.

## Prosedur

Script siap pakai: `scripts/attribute_cpu.sh` — jalankan via SSH ke host target
(`ssh -p PORT root@IP 'bash -s' < scripts/attribute_cpu.sh`) atau langsung di host.
Untuk mematikan satu profile beserta semua cron Hermes-nya (dengan backup + cara
pulihkan): `scripts/stop_profile.sh <profile>`.

Langkah manual:

```bash
# 1) kapasitas
nproc; cat /proc/loadavg; top -bn1 | grep '%Cpu'

# 2) pemakan + unit systemd-nya
ps -eo pcpu,pmem,pid,ppid,etime,args --sort=-pcpu --no-headers \
 | awk '$1 > 3 && $6 != "ps"' | head -20 \
 | while read -r cpu mem pid ppid etime cmd; do
    unit=$(cat /proc/$pid/cgroup 2>/dev/null | grep -oP '[a-zA-Z0-9_.@-]+\.service' | head -1)
    echo "${cpu}% ${unit:-none} pid=$pid up=$etime :: $(echo "$cmd" | cut -c1-120)"
    echo "   induk: $(ps -p $ppid -o args= 2>/dev/null | cut -c1-100)"
 done

# 3) kalau unit = cron.service: cari barisnya (sistem + cron Hermes per profile)
grep -rn "<nama_script>" /etc/cron.d/ /etc/crontab /var/spool/cron/crontabs/ 2>/dev/null
grep -l "<nama_script>" /root/.hermes/profiles/*/cron/jobs.json 2>/dev/null

# 4) restart loop?
systemctl show <unit> -p NRestarts -p ActiveState
journalctl -u <unit> -n 40 --no-pager | grep -E 'killed|status=9|OOM'
```

## Gejala → arti

| Gejala | Arti |
|---|---|
| gateway `activating (auto-restart)` + `NRestarts` ratusan + `status=9/KILL` | host kelaparan CPU; gateway hidup 15-60 detik lalu dibunuh |
| `free -h` masih lega, journal tanpa oom-killer | BUKAN OOM — jangan kejar jalur RAM/swap |
| semua gateway `up=00:0X` | baru booting/restart; ukur lagi setelah 5-10 menit |
| pemakan ber-`UNIT cron.service` | cron sistem, bukan bot — baca file crontab, jangan tebak dari nama job |
| CPU turun tapi loadavg tetap tinggi | normal: loadavg rata-rata 1/5/15 menit |
| beberapa proses `sleep 12;`/`sleep 30;` di satu crontab | script yang sama dijalankan beberapa kali per menit — hitung total per menit, bukan per baris |
| satu proses `python3 -c "import sqlite3 ... PRAGMA quick_check ... state.db"` berumur 0-1 detik | cron/watchdog health-check DB, bukan bot — unit `cron.service`, `up=00:00`, hilang sendiri |
| 200%+ CPU dari `uv sync` / `pip_compileall` / `pm/worker.py` sesudah upgrade | build ulang environment runtime, selesai sendiri dalam 1-3 menit |
| loadavg naik bertahap tiap 30 detik sesudah script start bertahap | stagger delay tidak mengurangi total beban — sizing yang kurang |
| `NRestarts` naik terus sementara tiap gateway `up=00:0X`, tanpa OOM di journal | bukan beban kerja: ada pembunuh di luar (guard/watchdog script) — trace `kill` lewat bpftrace, lihat `sigkill-root-cause-tracing` |
| proses `hermes_cli.main` cmdline-nya panjang & `pgrep -f` salah hitung | cmdline adalah launcher `-c` multi-baris; hitung lewat `cat /proc/<pid>/cgroup` atau `ps -eo args` di host, bukan pola teks |

## Mitigasi (setelah pelaku terbukti)

1. Longgarkan jadwal cron terberat (tiap menit → tiap 5 menit): beban ~-80%, fungsi tetap.
2. `nice -n 15` + `ionice` pada script berat supaya bot tetap dapat CPU.
3. Pastikan cron berat tidak bertabrakan di menit yang sama.
4. Backup dulu: `cp -av /etc/cron.d/<x> /root/backup-cron/<x>.bak-$(date +%Y%m%d_%H%M%S)`.
5. Kalau kapasitas memang kurang (mis. 20+ gateway Hermes di 3 core) itu masalah
   sizing, bukan tuning. Sampaikan terus terang: pindah sebagian profile, matikan
   profile idle, atau tambah core. Jangan menjual tuning sebagai solusi sizing.

## Pitfall

- **Jangan menyalahkan script tanpa bukti cgroup**, dan jangan membebaskan script
  hanya karena `NRestarts=0`. Dua-duanya sudah menyesatkan laporan.
- **Jangan matikan script bisnis** (OTP, bank notif, anti-phishing) tanpa konfirmasi
  pemilik server; backup file cron dulu.
- Ghost-cron lama di `/etc/cron.d/` tetap jalan walau backup-nya dikira "sudah dimatikan" —
  cek juga status `disabled` unit-nya, bukan hanya komentar di file.
- Kill/pkill berulang pada anak proses yang di-respawn induk akan terlihat seperti
  "kill tidak ngefek". Sebelum mengulang, lihat PPID dan unit cgroup-nya.
- **`echo 1 > cgroup.kill` pada cgroup unit systemd adalah no-op** kalau unit hidup:
  systemd langsung respawn (`Restart=always`, `RestartSec=5`) dalam hitungan detik,
  jadi load tidak berubah dan terlihat seperti perintah gagal. Kill proses baru
  berguna kalau unitnya lebih dulu di-mask; dan itu justru yang harus dihindari
  (rule 9).
- **Mask unit file yang ada di `/etc/systemd/system/` GAGAL** ("Failed to mask unit:
  File ... already exists"). Mask butuh symlink ke `/dev/null`, jadi file aslinya
  harus di-backup lalu dihapus dulu. Kalau tetap perlu mask: `cp` unit file ke
  folder backup, `rm` file aslinya, baru `systemctl mask`, lalu `daemon-reload` dan
  uji dengan percobaan start yang HARUS gagal — itulah bukti, bukan exit code.
- Quote berlapis di `ssh '...'` mudah rusak (`tr '\0' ' '` jadi `tr: extra operand`).
  Tulis script ke file lokal, `scp` ke host, baru `ssh ... 'bash /tmp/<script>.sh'`.
  Pola ini juga menghindari guard yang memindai isi perintah ssh.
- **Komunikasi ke user selama forensik panjang:** Bang benci progres tanpa hasil
  ("manaaa, kok ga ada laporan?"). Kirim angka sesudah tiap aksi (load, idle%,
  jumlah proses) — bukan cerita apa yang sudah dicoba.
- **Jangan menyunting `config.yaml` dengan regex saat api masih menyala.** Mengganti blok
  `model:`/`fallback_providers:` lewat `re.sub(re.S)` mudah menghasilkan key ganda
  (`fallback_providers` dua kali) atau sisa potongan (`allback_providers`). Dampaknya **lintas
  profile**: gateway lain yang membaca config itu ikut gagal parse —
  `hermes_cli.config_read_errors: … duplicate key` / `Cannot read gateway.standalone from
  …/config.yaml`. Saat config sudah rusak, **bangun ulang dari backup**, jangan menambal sisa.
  Verifikasi wajib sesudah tulis: `python3 -c "import yaml;yaml.safe_load(open(CFG))"`
  + `grep -c '^fallback_providers:' CFG` harus `1`. Simpan backup bernama alasan
  (`config.yaml.bak-<alasan>-$(date +%Y%m%d_%H%M%S)`) sebelum menyentuh.
- **Nama bot di chat ≠ nama folder profile.** User menyebut "Susi", "Mery", "Udin"; config
  yang harus diedit adalah milik `HERMES_HOME` tempat **token bot itu** berjalan, sering beda
  dari folder yang namanya mirip. Petakan dulu token-prefix → `HERMES_HOME` → unit pemilik,
  baru edit. Profile default tinggal di `/root/.hermes/` dan jalan sebagai gateway **user**
  (`unit=user@0.service`) yang **tidak muncul** di `systemctl list-units 'hermes-gateway*'`.
  Kalau unit yang diedit tidak memakai token bot yang dikeluhkan, perbaikan itu bukan untuknya.
- **`model.provider: X` butuh entri `custom_providers[].name: X` yang sama persis.** `base_url`
  yang tampak ada belum tentu provider chat — bisa milik blok `image_gen`. Gejalanya
  `Primary provider auth failed (Unknown provider '<X>')`; verifikasi dengan mencetak daftar
  `custom_providers[].name`, lalu pastikan baris `Unknown provider` hilang dari journal sesudah restart.
- **Bot diam pasca-upgrade runtime = `ImportError`, bukan config.** Gateway yang hidup sebelum
  `git reset`/`pip install -e` masih memegang modul lama di memori; pesan berikutnya gagal dengan
  `ImportError: cannot import name …` walau `is-active` dan koneksi platform sehat. Cek journal
  gateway **itu** sebelum menyentuh model/provider, lalu restart semua gateway yang lebih tua dari update.
