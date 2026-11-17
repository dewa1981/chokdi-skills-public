# Install binary pihak-3 dengan aman (proven: ZenNotes `zn`, Go, MIT)

## 1. Ambil rilis + checksums dari GitHub Releases

```bash
cd /tmp && mkdir -p <tool>test && cd <tool>test
curl -sL -O https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>_linux_amd64.tar.gz
curl -sL -O https://github.com/<owner>/<repo>/releases/download/<tag>/checksums.txt
```

## 2. WAJIB verifikasi checksum sebelum eksekusi

```bash
grep linux_amd64 checksums.txt
sha256sum <asset>_linux_amd64.tar.gz      # dua hash HARUS identik
```

**Pitfall:** `sha256sum` atas **binary hasil ekstrak** menghasilkan hash BERBEDA dari `checksums.txt` — file itu
meng-hash **arsip `.tar.gz`**, bukan isinya. Bandingkan yang setara (`.tar.gz` vs baris linux_amd64), jangan
lalu mencurigai unduhan rusak atau ganti sumber.

## 3. Pasang permanen — JANGAN tinggal di `/tmp`

```bash
tar -xzf <asset>_linux_amd64.tar.gz
sudo install -m 755 <binary> /usr/local/bin/<binary>
<binary> --version                        # bukti jalan; kebanyakan tool Go static tanpa dependency
```

## 4. Kalau tool punya state/config sendiri: backup dulu

```bash
ls -la ~/.config/<tool>/            # temukan file state
cp ~/.config/<tool>/<file> ~/.config/<tool>/<file>.bak-$(date +%Y%m%d_%H%M%S)
```

Sama seperti config Hermes: setiap `add`/`use`/`connect` mengubah state dan bisa mengarahkan target tulis ke
folder yang salah. **Baca output perintahnya** — banyak tool mencetak efek samping dalam kalimat biasa
(contoh: "It is the default now") yang gampang terlewat kalau hanya melihat exit code 0.

## 5. Uji-tulis di direktori BUANGAN dulu

Sebelum mengarahkan tool ke data produksi: buat folder uji, jalankan operasi tulis + baca-ulang, dan verifikasi
hasilnya **di disk** (bukan dari respons tool). Baru setelah lolos, arahkan ke folder sebenarnya.

## 6. Kalau tool itu MCP server: uji handshake-nya sebelum mendaftarkan

MCP stdio sering menutup pipe saat stdin EOF dan melapor `server is closing: EOF` — itu bukan kegagalan.
Pakai `scripts/mcp_stdio_probe.py` (subprocess interaktif: `initialize` → `notifications/initialized` →
`tools/list`) untuk membaca jumlah + nama tool yang sebenarnya, lalu bandingkan dengan angka yang diklaim
README. Angka hasil `tools/list` yang lebih besar itu yang benar.
