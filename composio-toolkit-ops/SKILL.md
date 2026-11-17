---
name: composio-toolkit-ops
description: Use when installing/operating Composio CLI toolkits.
version: 1.0.0
author: chokdi_staging
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [composio, cli, toolkits, oauth, integrations, headless-login]
    related_skills: [mcp-server-setup, hermes-agent]
---

# Composio CLI — install, login headless, katalog toolkit

Composio = katalog besar integrasi SaaS (Gmail, Sheets, Slack, GitHub, Supabase, TikTok Ads, dll)
yang bisa dipanggil sebagai "tool" oleh agent. Satu CLI (`composio`) menangani cari tool, sambung
akun, dan eksekusi.

## When to Use (kapan dipakai)

- Bang minta install/upgrade/login Composio CLI.
- Bang tanya "ada tools apa saja" di Composio, atau minta sambungkan app tertentu.
- Mau eksekusi tool pihak-3 lewat akun Composio (bukan lewat MCP Hermes).

## 1. Audit installer dulu — jangan `curl | sh` buta

```bash
cd /tmp && curl -fsSL https://composio.dev/install -o composio_install.sh
sha256sum composio_install.sh
grep -nE "https?://[^\"' ]+" composio_install.sh | head -40
grep -nE "sudo|eval |base64 -d|nc |/etc/passwd|\.env" composio_install.sh | head -20
```

Yang AMAN = installer mengambil zip rilis dari GitHub `ComposioHQ/composio` releases dan
memverifikasi `checksums.txt` (kalau manifest tidak ada / beda, installer MENOLAK install).
Kalau URL download bukan `github.com/ComposioHQ/...` → STOP dan lapor Bang sebelum jalan.

## 2. Install

```bash
command -v unzip || apt-get install -y unzip   # installer hard-fail tanpa unzip
export PATH="$HOME/.local/bin:$PATH"
sh composio_install.sh --no-plugins            # --no-plugins: jangan sentuh agent host lain
which composio && composio --version
```

- `--no-plugins` wajib di sini: tanpa flag itu installer menjalankan `composio setup --target auto`
yang menulis plugin ke Claude Code / Cursor / host lain. Di Hermes tidak dipakai dan bisa
mengubah config agent lain.
- Hasil: binary `~/.composio/composio`, entry point `~/.local/bin/composio`, PATH block ditulis ke
  `~/.bashrc` + `~/.bash_profile`.
- Jangan simpulkan "belum pernah install" dari adanya `~/.composio`; cek `composio --version` dan
  `release-tag.txt` — file lama bisa tertinggal dari pemasangan sebelumnya.

## 3. Login headless (server tanpa browser)

```bash
composio login --no-wait --no-skill-install   # cetak URL + simpan pending-login-session.json
#  -> kirim URL ke Bang, dia approve di browser
composio login --poll                          # selesaikan; poll sampai ~10 menit
composio whoami                                # bukti: email + org
```

- `--no-skill-install` wajib: default login MENULIS skill `composio-cli` ke Claude Code, bukan ke
  skill pool Hermes.
- `--poll` jalankan sebagai background process (`terminal(background=true)`), jangan menahan satu
  turn 10 menit. Script latarnya harus `chmod +x` dulu — kalau tidak, proses mati dengan
  `bash: ... Permission denied` (exit 126) dan log tidak pernah terbentuk.
- Log kosong BUKAN bukti gagal: output CLI bisa ter-buffer. Bukti sah = `composio whoami`
  mengembalikan email + `current_org_name`.
- Tanpa manusia (unattended): `composio login --agent`. Jangan pakai kalau ada orang yang bisa login
  dengan akunnya sendiri.
- Kredensial tersimpan di `~/.composio/user_data.json` (`api_key: uak_...`) — **jangan cetak atau
  copas ke chat**.

## 4. Katalog: CLI default cuma menampilkan 30

```bash
composio dev toolkits list                 # default limit 30 — BUKAN jumlah total
composio dev toolkits list --limit 500
composio dev toolkits list --connected     # yang benar-benar sudah tersambung
composio connections list                  # '{}' = belum ada akun tersambung
```

Katalog penuh lewat REST API (terukur: **1.742 toolkit / ±83.300 tool**):

```bash
KEY=$(python3 -c "import json;print(json.load(open('$HOME/.composio/user_data.json'))['api_key'])")
curl -s -4 "https://backend.composio.dev/api/v3/toolkits?limit=1000" \
  -H "x-user-api-key: $KEY" -o /tmp/tk1.json
python3 -c "import json;d=json.load(open('/tmp/tk1.json'));print(len(d['items']), d.get('next_cursor'))"
```

- **Header yang benar `x-user-api-key`.** `x-api-key` dibalas `401 APIKey_InvalidAPIKey` (code 801)
  walau key-nya valid — jangan simpulkan key rusak dari situ.
- Pagination pakai `next_cursor`; respons memuat `total_items` dan `total_pages`.
- **Selalu `curl -o <file>` lalu parse file.** Output terminal dipotong (~20 KB) sehingga
  `json.loads` gagal di tengah JSON yang besar.
- Ringkasan katalog per kategori ada di `references/toolkit-catalog.md` — pakai itu untuk menjawab
  "ada tool apa saja" tanpa query ulang.

## 5. Pakai tool

```bash
composio search "send email" --limit 5          # cari by use case -> primary_tool_slugs
composio search "create issue" --toolkits github
composio link gmail                             # OAuth akun ke toolkit
composio tools list gmail                       # daftar tool + schema
composio execute GMAIL_SEND_EMAIL --get-schema
composio execute GMAIL_SEND_EMAIL -d '{...}'
```

Subcommand lain: `run` (inline TS/JS dengan helper Composio), `proxy` (akses API toolkit mentah),
`triggers` (event), `orgs`, `config`, `dev` (project/auth-config/connected-account).

## 6. Batas & keputusan yang harus dijaga

- `~/.composio/config.json` default `destructive_actions: false`. Jangan dinaikkan tanpa izin Bang.
- **Jangan arahkan Stripe/PayPal ke transaksi judi** — akun bisa di-ban permanen; depo/WD tetap jalur
  PG brand sendiri.
- `composio link <app>` = OAuth ke akun Bang. Sebut app + scope-nya sebelum jalan, dan jangan
  menyambungkan akun tanpa permintaan eksplisit.
- Jangan bikin org/project baru di Composio tanpa izin.

## 7. Harga — DUA skema, jangan dicampur

- **Platform** (SDK/CLI, akun dengan developer project — akun kita): Hobby $0 = 100.000 tool call/bln
  (maks **20.000** untuk app OAuth Composio-managed; lewat itu BERHENTI, tidak ditagih), 50.000
  trigger, 3 member, connected account 1.000 pertama gratis, $2 kredit sekali. Pro $29/bln = +$29
  kredit, member unlimited, 10.000 req/menit (Hobby 2.000), kelebihan $0,0003/call, trigger $0,003.
- **For You** (paket dashboard tim): Free $0 = 10.000 call/bln; Standard $18/seat/bln = 10.000 call
  + $18 kredit per seat; kelebihan $0,005/call.
- **Instant tools** (search/scraping/generate gambar-video) ditagih dari kredit terpisah, rate per
  tool beda (contoh Apify: scrape FB posts $0,004/post). Ini yang paling cepat menghabiskan saldo —
  bukan tool call biasa.
- Plan & sisa kredit TIDAK bisa dibaca via API/CLI (endpoint billing balas HTML, termasuk
  `/api/v3/usage`, `/api/v3/orgs`, `/api/v3/billing/plan`) — hanya dashboard
  `dashboard.composio.dev` → Settings → Billing. Jangan mengarang plan aktif Bang.

## 8. Posting multi-platform: jangan connect satu per satu

Composio TIDAK punya login tunggal untuk semua sosmed — OAuth tetap per platform. Jalan pintasnya
pakai toolkit **aggregator** yang sudah ada di katalog:

| Toolkit | Tools | Catatan |
|---|---|---|
| `upload_post` | 12 | **Terbaik**: PUBLISH/SCHEDULE/ENQUEUE 1 post ke 22 jaringan. Free $0 = 10 upload/bln, 2 profile, TikTok TIDAK termasuk; Basic $24/mo ($16 tahunan) = unlimited + TikTok + 5 profile |
| `postiz_mcp` | 14 | Open source, self-host gratis, 34 platform, Public API + CLI + MCP — pilih kalau mau biaya bulanan nol tapi siap maintain container |
| `buffer` | 11 | Draft per 1 channel saja — TIDAK bulk publish |
| `ayrshare` | 3 | Cuma schedule/delete/history — TIDAK ada tool post |

Alur: Bang daftar Upload-Post → connect sosmed di dashboard mereka (terpusat, sekali per platform)
→ `composio link upload_post` pakai API key → publish multi-platform dalam 1 tool call.
Wajib disebut: konten judi di IG/TikTok/FB mudah kena ban — pakai akun khusus, bukan akun utama.

## Pitfall ringkas

- `composio login` tanpa `--no-skill-install` → menulis skill ke `~/.claude` (bukan pool Hermes).
- Installer gagal di awal karena `unzip` belum ada — install `unzip`, jangan cari jalan lain.
- Nested/heredoc panjang di terminal bisa ditolak lifecycle guard ("scan budget exhausted") →
  tulis script ke file dengan `write_file`, baru jalankan; jangan memaksa satu baris panjang.
- `composio dev toolkits list` tanpa `--limit` sering dibaca sebagai "Composio cuma punya 30 app" —
  itu default page size, bukan katalog.
