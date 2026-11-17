#!/bin/bash
# attribute_cpu.sh — atribusi beban CPU ke unit systemd (bukan tebak nama proses).
# Pakai: ssh -p PORT root@HOST 'bash -s' < attribute_cpu.sh
#        atau: bash attribute_cpu.sh
set -u

THRESH=${THRESH:-3}

echo "=== KAPASITAS ==="
echo "nproc : $(nproc)"
echo "load  : $(cat /proc/loadavg)"
top -bn1 | grep -E '%Cpu|MiB Mem|MiB Swap'
echo
echo "=== IDLE CHECK (idle tinggi = sudah pulih walau loadavg masih tinggi) ==="
top -bn1 | awk -F, '/%Cpu/ {print $4}'
echo
echo "=== PEMAKAN CPU > ${THRESH}% (dengan unit systemd) ==="
ps -eo pcpu,pmem,pid,ppid,etime,args --sort=-pcpu --no-headers \
 | awk -v t="$THRESH" '$1 > t && $6 != "ps"' | head -20 \
 | while read -r cpu mem pid ppid etime cmd; do
    unit=$(cat /proc/$pid/cgroup 2>/dev/null | grep -oP '[a-zA-Z0-9_.@-]+\.service' | head -1)
    echo "----------------------------------------"
    echo "CPU ${cpu}%  MEM ${mem}%  PID $pid  PPID $ppid  UP $etime"
    echo "UNIT : ${unit:-none}"
    echo "CMD  : $(echo "$cmd" | cut -c1-160)"
    echo "INDUK: $(ps -p "$ppid" -o args= 2>/dev/null | cut -c1-120)"
 done
echo
echo "=== GATEWAY HERMES: restart counter + umur proses ==="
systemctl list-units 'hermes-gateway-*' --no-legend --all 2>/dev/null | awk '{print $1, $3, $4}' | head -30
for pid in $(pgrep -f hermes_cli.main 2>/dev/null); do
  printf "  pid=%s up=%ss\n" "$pid" "$(ps -p "$pid" -o etimes= 2>/dev/null | tr -d ' ')"
done
echo
echo "=== CRON TIAP MENIT (kandidat beban berulang) ==="
grep -rn '^\* \* \* \* \*' /etc/cron.d/ /etc/crontab /var/spool/cron/crontabs/ 2>/dev/null | cut -c1-180
