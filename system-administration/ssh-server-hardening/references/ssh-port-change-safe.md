# Ganti Port SSH dengan Aman (tanpa lockout)

Kasus nyata: server `mem0-ai165` — dua kali SSH mati total karena langkah salah. Jangan ulangi.

## 🔴 PITFALL #1: JANGAN pakai `ssh.socket` override untuk ganti port

Ubuntu 24.04 pakai **systemd socket activation** (`ssh.socket` aktif, mendengarkan `0.0.0.0:22`).
Menulis override seperti ini **mematikan socket sepenuhnya**:

```ini
# ❌ JANGAN — bikin socket mati, semua port refused
[Socket]
ListenStream=
ListenStream=22022
```

Gejala: `ssh: connect ... port 22022: Connection refused`, lalu port 22 juga mati.
`systemctl restart ssh.socket` tidak memperbaikinya.

## ✅ CARA YANG BENAR: pakai `ssh.service`, dua baris `Port`

```bash
# 1. matikan socket activation (service biasa baca sshd_config langsung)
systemctl disable --now ssh.socket
systemctl unmask ssh.service 2>/dev/null

# 2. sshd_config: DUA baris Port (port lama TETAP hidup)
sed -i '/^Port /d' /etc/ssh/sshd_config
sed -i '/^Include \/etc\/ssh\/sshd_config.d/i Port 22\nPort 22022' /etc/ssh/sshd_config

# 3. VALIDASI sebelum reload — wajib, ini jaring pengaman
sshd -t || { echo INVALID; exit 1; }

# 4. reload (BUKAN restart) + enable service
systemctl enable --now ssh.service
systemctl reload ssh.service

# 5. verifikasi
ss -tlnp | grep -E ':22|:22022'
sshd -T | grep -E '^port'
```

**Hasil:** sshd dengar dua port dari SATU proses (`ss` menunjukkan `pid=X` sama untuk dua-duanya).

## Aturan urutan (WAJIB, jangan dibalik)

1. **JANGAN tutup port lama** sampai port baru **terbukti bisa login**.
2. Port 22 dan 22022 **hidup bersamaan** selama transisi.
3. Validasi `sshd -t` **sebelum** reload. Config invalid = rollback dari backup.
4. **Tes koneksi nyata** ke port baru (`ssh -p 22022 ...`) sebelum tetapkan sebagai port utama.
5. Baru setelah Bang tes sendiri → tawarkan tutup port lama. **Jangan inisiatif sendiri.**

**Catatan:** `LISTEN 0.0.0.0:22` di `ss` **belum berarti bisa login** — pernah mati padahal config tampak benar.
Selalu tes `ssh -p <port>` betulan.

## Jalur penyelamat kalau SSH mati

- **Console/VNC provider** (GreenCloud panel) — satu-satunya jalan kalau SSH mati total.
- **Tailscale** — aktifkan SEBELUM mengutak-atik SSH. `ssh -p <port> root@<tailscale-ip>` sebagai cadangan.
- Server tetap hidup walau SSH mati (ping + service lain jalan). Cek `ping` untuk memastikan bukan server down.

## Zombie process

Setelah mengganti dari socket ke service, proses sshd lama bisa nyangkut memegang port:
```bash
ss -tlnp | grep ':22022' | grep -oP 'pid=\K[0-9]+' | head -1   # ambil pid
kill <pid>                                                       # matikan
```

## `fail2ban` jail sshd

Kalau port SSH berubah, pastikan jail menangkap log service yang benar:
```
fail2ban-client status sshd     # Journal matches: _SYSTEMD_UNIT=sshd.service + _COMM=sshd
```
Jail default biasanya sudah mengikuti `sshd.service` — tidak perlu ubah `port` selama pakai unit yang sama.
