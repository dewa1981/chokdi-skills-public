#!/usr/bin/env bash
# WATCHDOG SOCKS5 — jaga SSH -D tunnel tetap hidup (cron tiap 2 menit)
# Catatan: JANGAN pakai pkill -f dengan string yang match command shell sendiri!
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

SOCKS_PORT=1080
SSH_TARGET="root@VPS_IP"       # ganti: user@host
SSH_EXTRA="-p 22022 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15 -o ServerAliveInterval=30"

# Cek port hidup (tidak perlu pkill)
if ! (exec 3<>/dev/tcp/127.0.0.1/$SOCKS_PORT) 2>/dev/null; then
    # Matikan proses lama dengan PID (bukan pattern yang match shell)
    for pid in $(pgrep -f "ssh .*-D 127.0.0.1:$SOCKS_PORT" 2>/dev/null); do
        [ "$pid" != "$$" ] && kill "$pid" 2>/dev/null
    done
    sleep 1
    ssh -f -N -D 127.0.0.1:$SOCKS_PORT $SSH_EXTRA $SSH_TARGET
    sleep 3
    if (exec 3<>/dev/tcp/127.0.0.1/$SOCKS_PORT) 2>/dev/null; then
        echo "SOCKS5 proxy restarted (port $SOCKS_PORT)"
    else
        echo "FAIL: SOCKS5 tidak bisa start — cek SSH $SSH_TARGET"
    fi
fi
