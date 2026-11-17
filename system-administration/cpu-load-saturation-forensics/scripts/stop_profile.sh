#!/bin/bash
# stop_profile.sh — matikan satu profile Hermes beserta SEMUA cron Hermes-nya,
# dengan backup yang bisa dipulihkan. Bukan mask massal (lihat rule 9 di SKILL.md).
#
# Pakai: ssh -p PORT root@HOST 'bash -s' < stop_profile.sh -- <profile>
#        bash stop_profile.sh <profile>
set -u

PROF=${1:?pakai: stop_profile.sh <profile>}
HERMES=${HERMES_HOME:-/root/.hermes}
P="$HERMES/profiles/$PROF"
TS=$(date +%Y%m%d_%H%M%S)
BK="/root/backup-profile-$PROF-$TS"

[ -d "$P" ] || { echo "FATAL: $P tidak ada"; exit 1; }
mkdir -p "$BK"

count_enabled() {
  python3 - "$P/cron/jobs.json" <<'PY'
import json,sys
p=sys.argv[1]
try:
    d=json.load(open(p))
except Exception as e:
    print("ERR",e); raise SystemExit(0)
jobs=d.get('jobs',d) if isinstance(d,dict) else d
print(len([j for j in jobs if j.get('enabled',True)]))
PY
}

set_jobs_enabled() {   # $1 = true/false
  python3 - "$P/cron/jobs.json" <<PY
import json,sys
p=sys.argv[1]
d=json.load(open(p))
cur=d.get('jobs') if isinstance(d,dict) and 'jobs' in d else d
n=0
for j in cur:
    if j.get('enabled',True) != $1:
        j['enabled'] = $1; n+=1
json.dump(d if isinstance(d,dict) else cur, open(p,'w'), indent=2, ensure_ascii=False)
print('jobs diubah:', n)
PY
}

echo "=== 0) SEBELUM ==="
echo "panjang sebelum  : $(cat /proc/loadavg)"
echo "job enabled      : $(count_enabled)"

echo
echo "=== 1) BACKUP ==="
cp -av "$P/cron/jobs.json" "$BK/jobs.json" 2>&1 | tail -1
cp -a "$P/cron" "$BK/cron-full" 2>/dev/null && echo "cron dir tersimpan"
cp -av "/etc/systemd/system/hermes-gateway-$PROF.service" "$BK/" 2>/dev/null
cp -a "$P/.env" "$P/config.yaml" "$BK/" 2>/dev/null
cp -a "$P/gateway-starts.log" "$BK/" 2>/dev/null
echo "BACKUP DIR       : $BK"

echo
echo "=== 2) MATIKAN SEMUA CRON PROFIL ==="
set_jobs_enabled false
echo "job enabled sekarang: $(count_enabled)"

echo
echo "=== 3) HENTIKAN PROSES PROFILE (per PID, bukan mask) ==="
for pid in $(ps -eo pid,args --no-headers | grep "profile $PROF" | grep -v grep | awk '{print $1}'); do
  ppid=$(ps -p "$pid" -o ppid= 2>/dev/null | tr -d ' ')
  echo "kill pid=$pid (ppid=$ppid)"
  kill -9 "$pid" 2>/dev/null
done
echo "lepas service-manager (kalau ada): systemctl disable hermes-gateway-$PROF"
systemctl disable "hermes-gateway-$PROF" >/dev/null 2>&1 && echo "unit disabled (tidak auto-start saat boot)"

echo
echo "=== 4) VERIFIKASI (bukan exit code) ==="
sleep 3
echo "panjang sesudah  : $(cat /proc/loadavg)"
echo "proses tersisa   : $(ps -eo args --no-headers | grep "profile $PROF" | grep -v grep | wc -l)"
top -bn1 | grep '%Cpu'

echo
echo "=== CARA PULIHKAN ==="
echo "  cp $BK/jobs.json $P/cron/jobs.json"
echo "  systemctl enable --now hermes-gateway-$PROF"
