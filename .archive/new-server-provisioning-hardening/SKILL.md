---
name: new-server-provisioning-hardening
description: Use when hardening a fresh Ubuntu server after install.
version: 1.0.0
author: chokdi_staging
license: internal
metadata:
  hermes:
    tags: [ubuntu, hardening, ssh, ufw, fail2ban, docker, tailscale, provisioning]
    related_skills: [ssh-server-hardening, new-server-sop, ssh-port-transition, tailscale-remote-access]
---

# Provisioning & Hardening Server Ubuntu Baru

## When to Use

- Selesai install Ubuntu Server baru dan siap dikonfigurasi
- Server baru perlu masuk Tailscale + hardening sebelum dipakai produksi
- Agent perlu akses root tanpa password (nopasswd sudo)
- Memindahkan monitor/KVM dari server baru (headless), atau menguji reboot/ketahanan server

## Sebelum menyentuh apa pun: pastikan jalur masuk SUDAH terbukti

Server baru di balik NAT hanya bisa dijangkau lewat Tailscale. Urutan ini tidak boleh dibalik:

```
1. User jalankan `tailscale up` di server → approve di browser
2. VERIFIKASI dari sisi agent: ping + port SSH (docker/cf tidak relevan di sini)
3. Pasang SSH key (agent + user)
4. Verifikasi key benar-benar bisa masuk (BatchMode=yes)
5. nopasswd sudo untuk agent
6. Update paket + timezone WIB
7. UFW + fail2ban
8. Matikan password SSH (TERAKHIR)
9. Docker / app
```

**Jangan** menunggu `tailscale up` selesai lalu langsung mengasumsikan device muncul. Device baru **hanya terdaftar setelah user menyelesaikan login** di halaman auth. Cek lewat API device list; kalau belum ada, minta user jalankan `tailscale up` (bukan mengulang approve).

## 1. Agent tidak bisa kirim password ke sudo

Sistem keamanan Hermes **memblokir** `sudo -S` dengan password (dianggap vektor brute-force):
```
BLOCKED: sudo password guessing via stdin (sudo -S)
```

**Solusi:** minta USER jalankan SATU baris ini di terminal mereka (10 detik):
```bash
echo '<user> ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/<user> && sudo chmod 440 /etc/sudoers.d/<user> && sudo -n whoami
```
Setelah itu agent bisa kerja sendiri (verifikasi: `sudo -n whoami` → `root`).

Opsi lain: set `SUDO_PASSWORD` di `.env` (tapi berarti password user tersimpan di server — hindari kalau bisa).

## 2. PITFALL paling sering: password SSH tetap 'yes' walau sudah diubah

Ubuntu cloud-init menaruh drop-in yang **MENIMPA** `sshd_config`:
```
/etc/ssh/sshd_config.d/50-cloud-init.conf:  PasswordAuthentication yes
```

Gejala: sudah `sed -i` di `/etc/ssh/sshd_config`, `sshd -t` OK, restart — tapi `sshd -T | grep passwordauthentication` masih bilang **yes** (karena drop-in dibaca SETELAH config utama).

**Fix:**
```bash
cp /etc/ssh/sshd_config.d/50-cloud-init.conf /etc/ssh/sshd_config.d/50-cloud-init.conf.bak
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config.d/50-cloud-init.conf
sshd -t && systemctl restart ssh
sshd -T | grep -E '^(passwordauthentication|pubkeyauthentication|permitrootlogin)'
```

**Pelajaran umum:** setiap kali mengubah sshd, selalu verifikasi dengan `sshd -T` (config EFEKTIF), bukan dengan membaca file config.

## 3. Jangan pernah matikan password sebelum key terbukti

Password SSH mati = satu-satunya jalur remote hilang. Sebelum mematikan:
1. Pasang key agent + key user (`~/.ssh/authorized_keys`, chmod 700 dir / 600 file)
2. **Tes `BatchMode=yes`** (tanpa password) → kalau berhasil baru lanjut
3. Baru matikan password

**Bedakan dua hal ini** (sering tertukar):
| Jenis login | Efek kalau `PasswordAuthentication no` |
|---|---|
| SSH dari jaringan | ❌ password mati — hanya key |
| **Login di layar fisik (tty)** | ✅ **password TETAP hidup** (PAM, beda jalur) |

Jadi user **tidak akan terkunci**: pintu darurat = colok monitor+keyboard, pakai password user. Kasus terburuk: GRUB → recovery mode → reset password.

## 4. Port 22 vs port non-standar

Yang benar-benar menahan penyerang adalah **KEY**, bukan port. Ganti port hanya mengurangi noise di log (bot scanner).

Kalau tetap mau ganti port: pakai pola **DUA-PORT** (port lama tetap hidup selama transisi) — lihat skill `ssh-port-transition`. Jangan ganti langsung.

## 5. Paket & setelan yang dipasang

```bash
# timezone (log jadi konsisten)
sudo timedatectl set-timezone Asia/Jakarta

# UFW: hanya SSH + tailscale
sudo ufw default deny incoming; sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow in on tailscale0
sudo ufw --force enable

# fail2ban (backend systemd cocok untuk Ubuntu 24.04)
# /etc/fail2ban/jail.local:
# [DEFAULT] bantime=1h findtime=10m maxretry=5 backend=systemd
# [sshd] enabled=true port=22

# Docker dari repo resmi (bukan snap)
# daftar user ke grup docker supaya tidak perlu sudo
sudo usermod -aG docker <user>
```

## 6. UFW memblokir container → host

Kalau container perlu menjangkau service di host (mis. proxy di 127.0.0.1:PORT), UFW **menolak** koneksinya. Fix:
```bash
iptables -I INPUT -p tcp --dport <PORT> -s 172.16.0.0/12 -j ACCEPT
```
Hanya jaringan Docker (bukan internet). Buat permanen dengan systemd oneshot unit `iptables-*-service` + simpan ke `/etc/iptables/rules.v4`.

## 7. `host.docker.internal` sering menyesatkan

Di container, `host.docker.internal` bisa menunjuk `172.17.0.1` (bridge `docker0`, bukan bridge jaringan container itu). Kalau tidak jalan:
```bash
docker inspect <container> --format '{{range .NetworkSettings.Networks}}gw={{.Gateway}}{{end}}'
```
→ pakai **gateway bridge yang benar** (mis. `172.21.0.1`) atau IP host di bridge itu.

## Checklist akhir (verifikasi 2x)
```bash
hostname; lsb_release -ds; date '+%Y-%m-%d %H:%M %Z'
sudo ufw status | head -1
sudo systemctl is-active fail2ban
sudo sshd -T | grep -E '^(passwordauthentication|pubkeyauthentication|permitrootlogin)'
sudo docker --version; sudo systemctl is-active docker
tailscale ip -4; free -h | head -2; df -h / | tail -1
```

## 8. Uji REBOOT sebelum menyerahkan server (bukti tahan reboot)

Hardening yang tidak tahan reboot = tidak berguna. Setelah semua dipasang, reboot sekali dan verifikasi semuanya naik sendiri.

```bash
ssh <host> 'sudo shutdown -r +0 "reboot test"'
# pantau sampai online: ping + port SSH
for i in $(seq 1 36); do ping -c1 -W2 <ip> >/dev/null 2>&1 && \
  timeout 8 bash -c "cat < /dev/null > /dev/tcp/<ip>/22" 2>/dev/null && echo ONLINE && break; sleep 5; done
```

Sesudah online, verifikasi **semua** ini:
- `uptime` → `up 0 min` (bukti benar-benar reboot)
- `systemctl is-active ssh docker fail2ban tailscaled ufw` → semua `active` (auto-start!)
- `sshd -T` → password **tetap** `no` (hardening tidak hilang)
- `tailscale ip -4` → IP **sama** (auto-reconnect)
- `date` → timezone WIB tetap
- `timedatectl set-timezone` yang di-set sebelumnya tidak kembali ke UTC

## 9. Server headless: monitor/KVM boleh dilepas setelah reboot terbukti

Sekali reboot terbukti naik sendiri + semua service `active`, server tidak butuh monitor/KVM. Boleh dilepas.

Yang **tidak boleh** dilepas: **kabel LAN** (agent kehilangan akses) dan **power**.

Sampaikan juga ke user: pintu darurat tetap ada — **colok monitor sebentar tanpa restart**, layar console login muncul, masuk pakai password user (password SSH mati tidak mempengaruhi tty).

## 10. WiFi: default MATI — tapi tanyakan dulu apakah user mau failover

Installer Ubuntu Server biasanya hanya mengkonfigurasi Ethernet. Interface WiFi (`wlp4s0` dst) akan `DOWN` — itu **benar** untuk server.

Alasan default mati: kabel 2.5GbE lebih cepat dan **stabil**; WiFi menambah satu jalur routing yang bisa bikin trafik bingung.

**TAPI jangan menjadikan ini aturan mati.** Tanyakan / dengarkan kebutuhan user: kalau user ingin bisa **"cabut kabel LAN untuk dapat internet"**, maka WiFi harus `autoconnect yes` dan **boleh** jadi default. Pola yang benar:

| Tujuan | `ipv4.never-default` | `ipv4.route-metric` | `autoconnect` | Hasil |
|---|---|---|---|---|
| Cuma uji, jangan ganggu LAN | `yes` | 600 | `no` | WiFi connect tapi **tidak pernah** ambil alih |
| **Failover (cabut LAN → WiFi)** | **`no`** | **600** | **`yes`** | LAN menang saat tercolok; WiFi ambil alih saat LAN hilang |

```bash
# FAILOVER: LAN tetap menang karena metric lebih kecil (100 vs 600)
sudo nmcli connection add type wifi con-name 'wifi-cadangan' ifname wlp4s0 \
  ssid '<SSID>' wifi-sec.key-mgmt wpa-psk wifi-sec.psk '<pass>' \
  ipv4.method auto ipv4.route-metric 600 connection.autoconnect yes
```

⚠️ **Jebakan yang menipu:** dengan `never-default yes`, WiFi **connect** tapi route default tidak pernah pindah ⇒ cabut LAN = server offline. Kalau kamu lalu menyimpulkan "WiFi tidak bisa failover", itu **salah** — penyebabnya setelan kamu sendiri. Untuk failover, cukup atur **route-metric**.

⚠️ Pilih SSID yang **satu router dengan LAN** (subnet sama). SSID lain = jaringan beda = bukan jalur failover.

⚠️ LAN yang dikelola **netplan** tidak bisa dikontrol `nmcli` (`device is strictly unmanaged`) — itu normal, LAN naik sendiri saat kabel dicolok.

**Verifikasi wajib sebelum & sesudah:**
```bash
ip route | grep '^default'    # harus memuat enp*/eth*
```
Kalau `enp*` hilang dari default → LAN tertimpa; pulihkan: `nmcli connection down 'wifi-*'`.

Scan & alat: `apt-get install -y network-manager iw wireless-tools rfkill lm-sensors`;
`nmcli device wifi rescan; sleep 10; nmcli -f SSID,SIGNAL,CHAN,SECURITY device wifi list`.

### Uji failover end-to-end (simulasi kabel dicabut tanpa kehilangan akses)

```bash
sudo nmcli device disconnect enp3s0     # simulasi cabut
sleep 15
ip route | grep '^default'              # harus pindah ke wlp4s0
ping -c 3 -W 4 -I wlp4s0 8.8.8.8        # bukti internet jalan lewat WiFi
# PULIHKAN (LAN naik sendiri di netplan; kalau tidak, minta user colok ulang)
```
Selalu pulihkan LAN di blok `finally`/akhir skrip — jangan tinggal server di satu jalur tanpa disadari user.

## 11. Watchdog suhu/kesehatan server — notif hanya kalau ada masalah

Server headless tanpa monitor tidak akan kelihatan kalau kepanasan atau disk penuh. Pasang watchdog cron ringan yang **READ-ONLY**.

Aturan desain (yang penting, bukan detail kodenya):
- **Diam kalau normal.** Kirim notif HANYA saat ada masalah — kalau tidak, user akan matikan notifnya.
- **Anti-spam:** satu jenis masalah maksimal sekali per beberapa jam (simpan timestamp di state file).
- **Satu script untuk banyak host:** loop daftar target (lokal + remote via SSH), supaya tidak ada duplikat kode.
- **Ambil metrik lewat perintah yang portabel:** `uptime`, `/proc/loadavg`, `free -m`, `df -m /`, `sensors` (butuh `apt-get install -y lm-sensors`), `/sys/class/thermal/thermal_zone*/temp`.
- **Normalisasi load per-core** (`load1 / nproc`) — angka load mentah tidak berarti tanpa jumlah core.
- **RAM:** pakai `total - available`, BUKAN `used` — cache/buffer membuat `used` menyesatkan (server 60GB tampak "0%" atau "55%" tergantung kolom).
- **Disk:** ambil kolom persen dari `df` langsung, jangan hitung sendiri dari used/total (angka blok bisa bikin salah).
- **Isi laporan:** suhu, load per-core, RAM %, disk %, uptime.

**PITFALL saat membangun script watchdog:** jangan menaruh beberapa `KEY=VALUE` dalam satu baris `awk` (`print "A="$2" B="$3"}`) — parser mudah salah membaca dan hasilnya nilai kosong/0. **Satu pasangan `KEY=VALUE` per baris.** Verifikasi dengan menjalankan perintahnya sendiri lewat SSH dan bandingkan dengan hasil parsing Python.

Sediakan flag `--paksa` untuk mengirim laporan walau semua normal — itu cara satu-satunya membuktikan notif benar-benar sampai ke user.
