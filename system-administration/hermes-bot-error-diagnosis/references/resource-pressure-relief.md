# Membebaskan Tekanan Resource di Server Multi-Profile Hermes

Dipakai SEBELUM repair/reinstall/restart apa pun di server Hermes yang sesak.
Urutannya penting: repair di server sesak akan putus di tengah dan meninggalkan
paket setengah ter-update — jadi sesak harus dibuka dulu.

## 1. Baca peta RAM — siapa sebenarnya yang memakan

Jangan mengandalkan `free` saja; jumlah proses gateway yang jalan biasanya biangnya.

```bash
free -m
ps -eo pid,ppid,%mem,rss,etime,cmd --sort=-rss | head -20
free -m | grep -i swap
pgrep -fc 'hermes_cli.main'          # jumlah gateway yang jalan
```

Interpretasi khas server multi-profile:
- N proses gateway (default + tiap profile) × ~400–750 MB = pemakan terbesar.
  Yang paling gede biasanya profile dengan state.db paling besar juga.
- `free` = 0 **dengan** `buff/cache` besar BUKAN krisis — itu cache, bisa dibuang.
- `free` = 0 **dan** swap penuh = krisis nyata: alokasi baru akan gagal/menggantung,
  dan proses restart cenderung gagal di tengah.

Siapa yang memakai swap per proses:
```bash
for f in /proc/[0-9]*/status; do
  awk '/^Name:/{n=$2}/^VmSwap:/{if($2>50000) print $2" kB "n}' "$f" 2>/dev/null
done | sort -rn | head -12
```

## 2. Bebaskan yang aman dulu (non-destruktif)

```bash
sync; echo 3 > /proc/sys/vm/drop_caches; sleep 2; free -m
```
`drop_caches` hanya membebaskan `buff/cache` → `free` naik besar tanpa menyentuh
satu pun proses. Terbukti membawa `free` dari ratusan MB ke puluhan GB. Nol risiko.

## 3. Hentikan proses/platform yang tidak dipakai

Ini yang benar-benar mengurangi pemakaian, bukan cuma memindahkan cache. Matikan
dulu yang jelas-jelas tidak dipakai — jangan mulai dari yang penting.

Kandidat paling aman & paling berisik:
- Platform messaging yang tidak dipakai tapi reconnect terus (log
  `Reconnect <platform> error ... next retry in 300s`, counter sampai ribuan
  percobaan). Matikan di `config.yaml`:
  `platforms.<nama>.enabled: false` — **backup config dulu**
  (`cp -av config.yaml config.yaml.bak-$(date +%Y%m%d_%H%M%S)`), baru edit.
  Perubahan ini baru berlaku tuntas setelah gateway restart.
- Container/service pihak ketiga yang boleh nanti dinyalakan lagi.

## 4. Baru restart / repair

Setelah ada headroom, baru restart gateway (lihat bagian restart di SKILL.md).
Verifikasi hasilnya dengan `MainPID` yang BERUBAH dan `free -m` yang lebih lega —
bukan dengan "service active".

## Pitfall

- **`drop_caches` bukan solusi kalau tekanan berasal dari proses.** Cache kembali
  terisi dalam hitungan menit kalau prosesnya masih lapar RAM. Ia berguna untuk
  membuka ruang SEKARANG supaya langkah berikutnya (restart/repair) tidak gagal.
- **Jangan kill proses gateway sembarangan untuk "menghemat RAM".** Gateway tanpa
  supervisor yang tepat bisa mati permanen → bot hilang. Pakai jalur restart resmi.
- **Satu profile = satu state.db;** state.db besar (>200 MB) memperlambat dan
  memperbesar jejak memori profile itu. Ini kandidat optimasi terpisah, bukan alasan
  mematikan profile tanpa izin user.
- **Jangan mematikan profile/bot milik user tanpa konfirmasi.** Di server multi-profile,
  "menghemat RAM" bisa berarti mematikan layanan yang sedang dipakai orang.
- Selalu catat baseline `free -m` SEBELUM dan SESUDAH tiap langkah, supaya klaim
  penghematan punya angka, bukan kesan.
