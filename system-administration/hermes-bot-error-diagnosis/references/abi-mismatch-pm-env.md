# ABI mismatch: gateway venv (cp311) memuat site-packages env pm (cp314)

`ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'` (kadang disertai
`_cffi_backend`) di tengah turn, padahal paketnya ada dan bot baru saja di-restart.
Penyebabnya campur-interpreter: paket dikompilasi untuk minor Python lain.

## Ciri khas — beda dari "paket setengah ter-update" dan "proses basi"

- Chat: `Something went wrong and I couldn't finish this reply` tiap pesan.
- Traceback lompat keluar dari install tree:
  ```
  File "…/installs/<key>/environments/<hash>/venv/lib/python3.14/site-packages/pydantic/version.py"
  ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
  RuntimeError: Failed to initialize OpenAI client: …
  ```
  Angka `python3.14` di path vs interpreter proses gateway (mis. 3.11) = inti masalah.
- Sering ikut: plugin platform mati di `_cffi_backend`, `Tool search assembly skipped`,
  dan `Supervised task hosted_room_worker died … giving up restarts`.
- Muncul/berulang **tepat setelah** updater menyentuh `installs/<key>/environments/`
  (bandingkan mtime `facts.json` dengan waktu error pertama).

## Diagnosa (urut; buktikan ABI mismatch dulu sebelum menambal apa pun)

```bash
# a) Interpreter yang benar-benar dipakai gateway
PID=$(systemctl --user show hermes-gateway.service -p MainPID --value)
tr '\0' ' ' < /proc/$PID/cmdline | awk '{print $1}'
/opt/hermes-v0204/.venv/bin/python --version
cat /opt/data/installs/<key>/environments/<hash>/venv/pyvenv.cfg | grep version_info

# b) Import di KEDUA venv — pembeda ABI vs paket hilang
G=/opt/hermes-v0204/.venv/bin/python
P=/opt/data/installs/<key>/environments/<hash>/venv/bin/python
$G -c 'import pydantic_core; print(pydantic_core.__file__)'
$P -c 'from pydantic_core import _pydantic_core; print("env pm OK")'
# env pm sehat sendirian + gateway tidak bisa memuatnya = ABI mismatch.

# c) Bukti runtime: env pm sudah ter-map ke proses gateway?
grep -c 'python3.14' /proc/$PID/maps          # >0 = bocor

# d) Singkirkan penyebab lain — env/unit/.pth harus bersih
tr '\0' '\n' < /proc/$PID/environ | grep -i pythonpath
grep -rn 'PYTHONPATH\|installs' /opt/data/.env ~/.config/systemd/user/hermes-gateway* ~/.config/environment.d/ 2>/dev/null
ls <gateway-venv>/lib/python3.1*/site-packages/*.pth
/opt/hermes-v0204/.venv/bin/python -c 'import sitecustomize' 2>&1 | tail -1
```
Kalau env bersih tapi maps tetap memuat env pm → penyuntiknya kode pm
(`activate_dependencies()`), bukan config kita.

## Cek upstream sebelum menambal

Bug kelas ini pernah dilaporkan terbuka; komentar issue biasanya memuat workaround yang
sudah dicoba orang lain — lebih murah daripada bereksperimen di produksi.
```bash
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/search/issues?q=repo:NousResearch/hermes-agent+pydantic_core" \
  | python3 -c "import json,sys; [print(f\"#{i['number']} [{i['state']}] {i['title'][:90]}\") for i in json.load(sys.stdin)['items'][:10]]"
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/NousResearch/hermes-agent/issues/<N>/comments" \
  | python3 -c "import json,sys; [print('---', c['user']['login']); print((c['body'] or '')[:1200]) for c in json.load(sys.stdin)]"
```
Cari kata kunci `workaround`, `HERMES_DISABLE_LAZY_INSTALLS`, `ABI guard`.

## Workaround parsial — pasang, lalu BUKTIKAN

`HERMES_DISABLE_LAZY_INSTALLS=1` mencegah *lazy install*, tetapi **tidak selalu**
menghentikan rewrite `sys.path` yang sudah aktif. Perlakukan sebagai pengurang, bukan
obat: setelah restart, error bisa turun dari tiap beberapa detik menjadi sekali per boot.

```bash
# 1) Backup unit + hitung baseline (pembanding verifikasi nanti)
systemctl --user cat hermes-gateway.service > /opt/data/backups/systemd/hermes-gateway.service.bak-$(date +%Y%m%d_%H%M%S)
BEFORE=$(grep -c pydantic_core /opt/data/logs/errors.log)

# 2) Drop-in
mkdir -p ~/.config/systemd/user/hermes-gateway.service.d
cat > ~/.config/systemd/user/hermes-gateway.service.d/python.conf <<'EOF'
[Service]
Environment=HERMES_DISABLE_LAZY_INSTALLS=1
EOF
systemctl --user daemon-reload
```

Restart gateway memakai jalur cron (guard memblokir restart langsung dari sesi agent).
Script restart sebaiknya mencatat bukti env kepakai, mis.:
```bash
echo "$(date '+%F %T') status=$ST pid=$PID env_ok=$(tr '\0' '\n' < /proc/$PID/environ | grep -c HERMES_DISABLE)" >> /opt/data/logs/gw_patch_restart.log
```

## Verifikasi — SEMUA harus lolos sebelum bilang beres

```bash
tr '\0' '\n' < /proc/$PID/environ | grep HERMES_DISABLE        # 1) env kepakai
grep -c 'python3.14' /proc/$PID/maps                           # 2) harus 0
awk -v n="$BEFORE" 'NR>n' /opt/data/logs/errors.log | grep -c pydantic_core   # 3) harus 0
```
Service `active` saja TIDAK cukup. Kalau (2)/(3) masih gagal → laporkan patch tidak
cukup, jangan naik ke opsi berisiko tanpa persetujuan user.

## JANGAN: pindahkan `ExecStart` ke interpreter env pm

`installs/<key>/environments/<hash>/` berisi **workspace Hermes sendiri** (`workspace/hermes_cli`,
commit & ukuran berbeda) — itu **instalasi Hermes terpisah** hasil updater, bukan sekadar venv.
Mengarahkan gateway ke sana = migrasi (patch lokal seperti weixin/LINE & plugin harus
dibawa ulang, config bisa beda). Sajikan sebagai opsi bermigrasi dengan estimasi & uji,
bukan sebagai "fix cepat".

## Rollback

```bash
rm ~/.config/systemd/user/hermes-gateway.service.d/python.conf
systemctl --user daemon-reload
# restart lewat cron (jalur yang sama saat memasang); unit asli ada di /opt/data/backups/systemd/
```
