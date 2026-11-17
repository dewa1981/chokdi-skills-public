---
name: ssh-server-hardening
description: Use when hardening SSH on Ubuntu 24.04+ servers.
---

# SSH Server Hardening (Ubuntu 24.04+)

Mengamankan SSH di VPS Ubuntu: ganti port default, rate-limit login, fail2ban, dan CARA SELAMAT melakukannya tanpa mengunci diri sendiri. Terbukti di VPS Anti-DDoS (2026-08-05) — termasuk satu kali terkunci dan recovery-nya.

## Urutan yang BENAR (jangan terbalik!)

1. **Buka port baru di firewall DULU** (ufw + firewall panel provider) — SEBELUM menutup port lama. Urutan terbalik = terkunci dari luar:
   - `ufw allow <newport>/tcp`
   - Kalau provider punya cloud firewall (Vultr/Linode/Lightsail/Hetzner security group): tambah rule TCP <newport> di PANEL PROVIDER juga — ufw saja tidak cukup kalau ada firewall cloud di depan!
2. Ubah `Port` di `/etc/ssh/sshd_config` (hapus semua `^Port ` dulu, baru tambah `Port <newport>` — sed `sed -i '/^Port /d'` lalu `echo 'Port <newport>' >>`)
3. `sshd -t` → harus "CONFIG-OK" (test syntax sebelum restart!)
4. Restart service → test koneksi port baru → BARU tutup port lama

## PITFALL UTAMA — ssh.socket di Ubuntu 24.04

Ubuntu 24.04 memakai **socket activation**: `ssh.socket` (bukan sshd) yang bind port 22 — **mengabaikan `Port` di sshd_config**! Gejala: `sshd -T` bilang `port 22022` TAPI `ss -tlnp` masih `0.0.0.0:22` dan koneksi ke port baru timeout.

Fix:
```bash
systemctl stop ssh.socket
systemctl disable ssh.socket
systemctl enable ssh.service
systemctl restart ssh      # NAMA SERVICE = "ssh", bukan "sshd"!
ss -tlnp | grep ssh        # harus 0.0.0.0:<newport>
```
Catatan: `systemctl restart sshd.service` → "Unit sshd.service not found" di Ubuntu. Jangan restart via `sshd -t` saja — itu cuma test, tidak reload listener.

## Rate-limit (tanpa lock IP)

```bash
sed -i '/^MaxAuthTries/d;/^LoginGraceTime/d' /etc/ssh/sshd_config
echo 'MaxAuthTries 3' >> /etc/ssh/sshd_config
echo 'LoginGraceTime 20' >> /etc/ssh/sshd_config
```
JANGAN whitelist IP statis untuk SSH kalau pengakses dari NAT pool / IP berubah-ubah (Hermes Cloud egress IP berubah!). Cek dulu IP publik aktual (`curl api.ipify.org`) sebelum whitelist — dan kalau berubah-ubah, jangan whitelist sama sekali.

## Fail2ban (jail sshd dengan port custom)

```bash
apt-get install -y fail2ban
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 4
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = 22022          # WAJIB ikut port baru!
logpath = %(sshd_log)s
backend = systemd
maxretry = 4
bantime = 3600
EOF
systemctl restart fail2ban
fail2ban-client status sshd
```
`port` di jail HARUS diubah ke port custom — default 22 tidak akan match log.

## RECOVERY — kalau terkunci (SSH timeout semua port)

Gejala: port lama ditutup, port baru diblokir firewall luar → semua koneksi timeout. **Bisnis via Cloudflare Tunnel tetap jalan** (outbound, tidak butuh SSH) — cuma admin yang kehilangan akses shell.

Recovery via **web console provider** (Vultr console, Linode LISH, Hetzner console, dll):
```bash
ufw allow <newport>/tcp        # atau: iptables -I INPUT -p tcp --dport <newport> -j ACCEPT
ufw status                      # verifikasi rule
```
Lalu test SSH port baru dari luar. Selalu siapkan jalur console provider sebelum mulai ganti port.

## Pitfalls tambahan
- Jangan pernah `sed` port dengan pola yang bisa dobel (`Port 22022022` dari mengganti `22`→`22022` dua kali) — hapus semua `^Port ` dulu, tulis ulang.
- `sshd -T` (huruf besar T) = tampilkan config EFEKTIF setelah semua Include/drop-in (`/etc/ssh/sshd_config.d/*.conf`) — pakai ini untuk verifikasi, bukan grep sshd_config saja.
- Ubuntu drop-in `60-cloudimg-settings.conf` set `PasswordAuthentication no` — key-only auth sudah default di cloud image.
- UFW deny default: port yang TIDAK di-allow = tidak bisa diakses dari luar. Cek `ufw status` selalu setelah perubahan.
- **PITFALL MEMATIKAN (2x kejadian di VPS staging 2026-08-07): `ufw --force enable` dengan deny default MEMBLOKIR PORT LAMA yang masih dipakai listener.** Urutan `ufw allow <newport>` → enable → ganti config → restart TERBALIK bisa mengunci SSH: port lama ke-block UFW (timeout) PADAHAL sshd masih listen di sana (mis. ssh.socket bind 22 — yang MENGABAIKAN `Port 22022` di config!), dan port baru refused (belum ada listener). URUTAN PALING AMAN (terbukti):
  1. `ufw allow <oldport>/tcp && ufw allow <newport>/tcp` — BUKA KEDUANYA dulu, JANGAN enable deny sebelum port baru live!
  2. Fix listener dulu kalau Ubuntu 24.04: `systemctl disable --now ssh.socket && systemctl enable --now ssh.service` (socket cuma bind port default 22 dan mengabaikan sshd_config!)
  3. `sshd -t` → OK → restart → verifikasi `ss -tlnp | grep ssh` = `<newport>` (dan `<oldport>` masih listen)
  4. TEST login port baru DARI LUAR → sukses?
  5. BARU: `ufw delete allow <oldport>/tcp` + matikan port lama di config.
  Jangan pernah menaruh `Port` baru di `/etc/ssh/sshd_config.d/*.conf` drop-in sambil sshd_config juga diubah — config dobel bikin sshd gagal start (refused semua port). Satu sumber kebenaran: hapus semua `^Port ` lalu tulis ulang di sshd_config saja.
- Port SSH di atas 1024 bebas; pilih yang jarang di-scan tapi gampang diingat (contoh 22022). Update semua klien SSH (MSI, laptop, agent) dengan `-p <newport>`.

## Verifikasi
- `sshd -T | grep -E '^(port|maxauthtries|logingracetime)'` → nilai benar
- `ss -tlnp | grep ssh` → listen di port baru, port lama TIDAK ada
- `ssh -p <newport> root@<vps> 'echo OK'` → sukses
- `ssh -p 22 root@<vps> ...` → timeout/refused (port lama tertutup)
- `fail2ban-client status sshd` → jail aktif
