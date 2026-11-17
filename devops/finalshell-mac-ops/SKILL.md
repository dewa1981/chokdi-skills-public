---
name: finalshell-mac-ops
description: Install FinalShell on macOS and bulk-add SSH hosts.
---

# FinalShell di macOS — install & tambah host massal

## Install dari .pkg tanpa password admin
PKG FinalShell tidak bisa dipasang lewat `installer` (butuh sudo). Bongkar payload-nya:

```bash
pkgutil --expand ~/Downloads/finalshell_macos_arm64.pkg /tmp/fs_pkg2
# Payload = gzip (cek: file Payload)
cd /tmp/fs_pkg2/FinalShell-app.pkg && gzip -dc Payload | cpio -idm   # menghasilkan FinalShell.app DI SINI
cp -R FinalShell.app /Applications/
find /Applications/FinalShell.app -type f -exec chmod 644 {} \;
find /Applications/FinalShell.app -type d -exec chmod 755 {} \;
chmod 775 /Applications/FinalShell.app/Contents/MacOS/FinalShell \
          /Applications/FinalShell.app/Contents/runtime/Contents/Home/lib/jspawnhelper
xattr -dr com.apple.quarantine /Applications/FinalShell.app
open -a FinalShell
```

Catatan: skrip `postinstall` asli memanggil `chown :access_bpf /dev/bpf*` + menambah user ke grup `access_bpf` (butuh root). Tanpa itu fitur packet-capture FinalShell tidak jalan; SSH/SFTP normal tetap bisa.

Pitfall saat membongkar pkg:
- **`cpio -idm` menulis ke CWD, bukan ke folder tujuan** — kalau dijalankan setelah `cd /tmp/fs_pkg2/FinalShell-app.pkg`, hasil ekstrak muncul DI situ; `find /tmp/fs_ext` akan kosong 0 byte dan terlihat seperti gagal. `cd` ke folder kosong dulu, baru pipe payload ke `cpio`.
- PKG ini **tidak ber-signature** (`pkgutil --check-signature` → `no signature`) dan `postinstall`-nya mengunduh file dari `http://dl.hostbuf.com` (HTTP polos). Jangan jalankan postinstall — app sudah lengkap di dalam Payload; cukup copy + set permission seperti di atas.
- Cek versi setelah pasang: `/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' /Applications/FinalShell.app/Contents/Info.plist` (bundle id-nya memang aneh: `st`).

## Tambah host massal (tanpa UI)
Koneksi disimpan sebagai JSON polos per host:
`~/Library/FinalShell/conn/<16-char-id>_connect_config.json`

- Bidang kunci: `name`, `host`, `port`, `user_name`, `password` ("" kalau pakai key), `authentication_type` (2 = key), `secret_key_id` (16 char — reuse dari koneksi yang sudah ada agar key sama), `parent_id: "root"`.
- Prosedur: **quit FinalShell** (`osascript -e 'quit app "FinalShell"'`) → `cp -R conn conn.bak-<ts>` → clone file template, ganti `id` (16 char acak lowercase+digit), `name/host/port/user_name`, set `create_time`/`modified_time` (ms) → `open -a FinalShell`.
- Jangan mengarang `secret_key_id` baru: key tersimpan di keystore app, bukan di JSON.
- Verifikasi: `json.load` semua file, pastikan tidak ada duplikat (host,port).

## Jebakan
- macOS: `/Applications` bisa ditulis user admin — tidak perlu sudo untuk copy .app.
- Restart app diperlukan agar daftar koneksi baru terbaca.
- Data di `~/Library/FinalShell/` (bukan `~/.finalshell`).
- URL resmi `https://dl.hostbuf.com/finalshell3/finalshell_macos_arm64.pkg` — cek `Last-Modified`; halaman web mereka sering tertinggal dari file di server.
- Editor bawaan (seperti MobaXterm): buka panel SFTP → double-click file → tab editor → Cmd+S menyimpan ke server.
