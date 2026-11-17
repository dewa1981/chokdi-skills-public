---
name: hci-dashboard-deploy
description: Use when deploying or fixing the HCI dashboard.
---

# Deploy & fix Hermes Control Interface (HCI)

## Kapan dipakai
Pasang dashboard HCI (`xaspx/hermes-control-interface`, MIT, 768★) di server Hermes,
atau kalau HCI menampilkan data kosong / "gateway stopped" padahal jalan.

## Fakta repo
- Repo: `https://github.com/xaspx/hermes-control-interface` — MIT, Node 20+, ~6600 baris server.js
- Stack: Express + WebSocket + better-sqlite3 + Vanilla JS/Vite
- Port default **10272** (README kadang tulis 10274 — percaya `.env`/kode)
- Login: `HERMES_CONTROL_PASSWORD` + `HERMES_CONTROL_SECRET` di `.env` (buat `openssl rand -hex 32`)

## Langkah pasang

```bash
git clone https://github.com/xaspx/hermes-control-interface.git /opt/hermes-control-interface
cd /opt/hermes-control-interface
cp .env.example .env     # isi PASSWORD + SECRET + HERMES_HOME + PORT + HOST=127.0.0.1
npm install && npm run build
# jalankan terlepas dari cgroup gateway (JANGAN nohup/setsid — diblokir):
systemd-run --unit=hci-staging --collect /opt/hermes-control-interface/run-hci.sh
```

`run-hci.sh` wajib export **`HERMES_HOME` yang benar** dan PATH berisi `hermes`.

## 4 PITFALL YANG TERBUKTI (jangan ulangi)

### 1. `HERMES_HOME` salah → semua data kosong
HCI **hardcode `~/.hermes` di 34 tempat** (terutama `discoverGatewayPorts()`), walaupun
`process.env.HERMES_HOME` dihormati di 4 tempat.
**Cek dulu home gateway yang SEBENARNYA, jangan asumsi:**
```bash
PID=$(pgrep -f 'hermes_cli.main gateway run' | head -1)
tr '\0' '\n' < /proc/$PID/environ | grep HERMES_HOME   # ini yang benar
```
Set nilai itu di `.env` HCI + di `run-hci.sh`. Salah set → `agents: []`, `ports: {}`.

### 2. Root + unit `systemctl --user` → gateway terdeteksi "stopped"
Kode asli: `IS_ROOT ? '' : '--user'`. Kalau gateway jalan sebagai **systemd user unit**
tapi HCI jalan sebagai root, dia cek system manager → selalu `inactive`.
**Patch 2 tempat** di `server.js`:
```js
const SYSTEMD_USER_FLAG = '--user';          // baris ~148
const SYSTEMD_USER_FLAG = '--user ';         // baris ~417 (dalam probeGatewayHealth)
```
Lalu hapus gate root di auto-detect XDG:
```js
if (!process.env.XDG_RUNTIME_DIR && process.getuid) { ... }   // hapus `!IS_ROOT &&`
```

### 3. `/api/usage` selalu nol (bug upstream)
`buildUsageSummary()` dipanggil **tanpa argumen** di route `/usage` dan `/api/usage`,
padahal data diambil dari `getInsights()` (`hermes insights --days N`).
**Patch:** jadikan handler `async`, ambil insights, baru bangun summary:
```js
app.get('/api/usage', requireAuth, requirePerm('usage.view'), async (req, res) => {
  let ins = null; try { ins = await getInsights(7); } catch {}
  res.json(buildUsageSummary(ins));
});
```
Catatan: `/api/insights` & `/api/dashboard-state` sudah benar — pakai itu untuk memverifikasi
bahwa `hermes insights` sendiri jalan.

### 4. Akses: jangan bind publik
HCI bisa **start/stop/restart gateway & hapus profil**. Bind `127.0.0.1` lalu pakai
`tailscale serve` (tailnet-only, HTTPS otomatis):
```bash
tailscale serve --bg --https=10272 http://127.0.0.1:10272
```
Jangan expose ke internet tanpa auth kuat.

### 5. Chat gagal "TUI gateway not ready" (bug upstream — `lib/tui-gateway-bridge.js`)
Gejala di log: `[TUI:default] spawn error: spawn python3 ENOENT` berulang, dan UI
menampilkan warning kuning **"TUI gateway not ready"**. Chat masih jalan via CLI fallback,
tapi streaming/status rusak.

Dua hardcode penyebabnya:
```js
// (a) cari instalasi Hermes di tempat yang salah → python3 tak ada di PATH spawn
const root = process.env.HERMES_PYTHON_SRC_ROOT || path.join(os.homedir(), '.hermes', 'hermes-agent');
// (b) HERMES_HOME di-hardcode, mengabaikan environment
env.HERMES_HOME = path.join(os.homedir(), '.hermes');
```

**Patch:** cari root yang benar-benar punya `tui_gateway/`, dan hormati `HERMES_CONTROL_HOME`:
```js
const HERMES_CTL_HOME = process.env.HERMES_CONTROL_HOME || process.env.HERMES_HOME || path.join(os.homedir(), '.hermes');
const candidatesRoot = [process.env.HERMES_PYTHON_SRC_ROOT, '/usr/local/lib/hermes-agent',
                        path.join(HERMES_CTL_HOME, 'hermes-agent')].filter(Boolean);
const root = candidatesRoot.find(r => require('fs').existsSync(path.join(r, 'tui_gateway'))) || candidatesRoot[0];
// lalu:
env.HERMES_HOME = (this.profile && this.profile !== 'default')
  ? path.join(HERMES_CTL_HOME, 'profiles', this.profile) : HERMES_CTL_HOME;
```
Plus di wrapper start: `export HERMES_PYTHON=<venv>/bin/python3` dan
`export HERMES_PYTHON_SRC_ROOT=/usr/local/lib/hermes-agent`.

**Verifikasi:** setelah restart, log tidak boleh lagi memuat `ENOENT`; kirim pesan di tab CHAT
lewat Playwright dan pastikan balasan agent muncul + status `READY` (bukan `RECONNECTING`).

**Cek cepat:** `python3` harus ada juga lewat **spawn** (bukan hanya shell) — HCI memakai
`spawn()` tanpa `sh -c`, jadi PATH proses harus memuat python yang benar.

## Alur verifikasi (wajib)

```bash
# 1. service hidup + port bind
systemctl is-active hci-staging.service; ss -tlnp | grep 10272
# 2. login dapat cookie
curl -c ck.txt -X POST -H 'Content-Type: application/json' \
  -d "{\"username\":\"admin\",\"password\":\"$(grep '^HERMES_CONTROL_PASSWORD=' .env|cut -d= -f2-)\"}" \
  http://127.0.0.1:10272/api/auth/login
# 3. gateway terbaca running (BUKAN stopped)
curl -b ck.txt http://127.0.0.1:10272/api/agent/status    # gatewayStatus harus "running"
# 4. token terbaca
curl -b ck.txt "http://127.0.0.1:10272/api/usage"          # totalTokens > 0
# 5. agents/ports terisi
curl -b ck.txt http://127.0.0.1:10272/api/office/agent-states
```

## Screenshot UI (server tanpa browser)

Playwright ada di `node_modules` repo, tapi versi browser harus cocok. Cek dulu:
```bash
ls /root/.cache/ms-playwright/                     # mis. chromium-1234
```
Pakai `executablePath` eksplisit + `ignoreHTTPSErrors` untuk sertifikat Tailscale:
```js
chromium.launch({ executablePath: '/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome',
                  args:['--no-sandbox','--disable-dev-shm-usage'] })
```
Routing halaman HCI adalah **SPA** → jangan `goto('/agents')` (hasil "Cannot GET /agents");
**klik menu** dengan `page.click('text=AGENTS')` lalu tunggu.

## Login pertama
`GET /api/auth/status` → `first_run: true` → `POST /api/auth/setup` `{username, password}`
membuat admin pertama. Setelah itu pakai `/api/auth/login`.

## Hasil terpasang (staging, 14-Sep-2026)
- Service `hci-staging.service` (systemd transient via `systemd-run`)
- URL tailnet: `https://<host>.tail5cab24.ts.net:10272`
- Kredensial: `/root/.hermes/secrets/hci-login.txt` (chmod 600)
