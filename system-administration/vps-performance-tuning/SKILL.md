---
name: vps-performance-tuning
description: Use when VPS RAM tinggi — tune swap/php-fpm/MySQL aman.
---

# VPS Performance Tuning (RAM/swap/php-fpm/MySQL)

Tune VPS yang RAM-nya tinggi atau mau ditingkatkan performanya TANPA
mengganggu layanan live (client website/agent). Terbukti 2026-08-08: aaPanel
2-tahun (167.71.223.180) RAM 68.8% → 51.9% (turun ~1.3G, available 1.9G → 3.2G),
Coolify 1GB (174.138.16.102) + swap 2G (9 containers tetap sehat).

## Langkah (urutan aman — swap DULU, restart belakangan)
```bash
# 1) Diagnosa dulu (jangan asal tune!)
free -h                      # used vs buff/cache vs available + swap
ps aux --sort=-%mem | head -8   # RAM hogs (php-fpm berapa proses?)
ss -tlnp | head -20          # service yang listen
uptime                       # load (kalau 0.x santai, RAM tinggi = akumulasi)

# 2) SWAP 2G (asuransi anti-OOM — paling penting di VPS RAM kecil)
fallocate -l 2G /swapfile && chmod 600 /swapfile
mkswap /swapfile && swapon /swapfile
grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
sysctl vm.swappiness=10
grep -q 'vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf

# 3) Tune php-fpm (cari config dulu — path beda per panel!)
#    aaPanel: /www/server/php/<ver>/etc/php-fpm.conf
#    system:  /etc/php/<ver>/fpm/pool.d/www.conf
#    aturan: pm.max_children ≈ RAM_GB x 4 (8GB → 30; 1GB → 5-8)
#    tiap child php-fpm ±40-60MB. Contoh (aaPanel 8GB):
sed -i 's/pm.max_children = 120/pm.max_children = 30/' $CONF
sed -i 's/pm.start_servers = 10/pm.start_servers = 5/' $CONF
sed -i 's/pm.min_spare_servers = 10/pm.min_spare_servers = 5/' $CONF
sed -i 's/pm.max_spare_servers = 30/pm.max_spare_servers = 15/' $CONF
/etc/init.d/php-fpm-83 reload   # ATAU systemctl reload php-fpm  (GRACEFUL — tanpa drop request!)

# 4) MySQL innodb_buffer_pool (512M → 256M kalau DB kecil / RAM ketat)
grep -r innodb_buffer_pool_size /etc/my.cnf /etc/mysql/ 2>/dev/null
sed -i 's/innodb_buffer_pool_size = 512M/innodb_buffer_pool_size = 256M/' /etc/my.cnf
systemctl restart mysqld     # SEBENTAR down — kasih tau user dulu kalau client live!

# 5) Verify
free -h && ps aux | grep php-fpm | grep -v grep | wc -l
```

## Pitfalls
- **Server LIVE/client = reload graceful dulu, restart belakangan.** php-fpm
  reload = tanpa drop request; MySQL restart = sesaat down (informasikan).
- **aaPanel path BEDA**: `/www/server/php/<ver>/etc/php-fpm.conf` (bukan
  /etc/php/) — grep default kosong menyesatkan. Cek `find /www/server/php -name
  "*.conf"` kalau aaPanel.
- **Jangan asal tune server tua (2 tahun, client aktif)** — urutan aman:
  swap dulu (2 menit, tanpa restart) → php-fpm reload → baru MySQL restart.
- **VPS RAM 1GB + banyak container (Coolify 9 containers)** — swap 2G WAJIB;
  tanpa swap = OOM kill container. swappiness 10 = swap cuma cadangan (RAM
  dipakai dulu).
- **php-fpm max_children gila (120 di 8GB!)** = proses 31+ idle makan RAM —
  turunkan ke ~30 (8GB) / 5-8 (1GB). Efek langsung: proses 31→6, RAM turun.
- **Verifikasi di app panel (aaPanel mobile) bisa telat 1-5 menit** — angka
  `free -h` di server adalah sumber kebenaran; app refresh menyusul.

## Kapan TIDAK tune
- Server dengan traffic tinggi/peak — tune di jam sepi, atau hanya swap.
- Kalau available masih lega (mis. RAM 23G, used 1.2G) — tidak perlu.
