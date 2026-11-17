---
name: remote-agent-monitoring
description: Use when monitoring NAT'd hosts — heartbeat push vs poll.
version: 1.0.0
metadata:
  tags: [monitoring, heartbeat, watchdog, cron, ssh, nat]
---

# Remote Agent Monitoring (Heartbeat Push vs Poll)

How to monitor a host/agent that can't be reached inbound (no public IP, behind NAT, platform-managed container) without drowning in false "DOWN" alerts.

## Core rule (the whole point)

> If the thing you're monitoring has **no stable public inbound address**, **don't poll it** — have it **push a heartbeat out** instead.

- ❌ **Poll inbound**: monitor asks target "are you alive?" → if target is behind NAT/no-public-IP, the probe can't reach it → permanent false alarm.
- ✅ **Push outbound**: target writes a timestamp to the monitor via outbound SSH (the target can almost always reach *out*), monitor only alerts when the heartbeat goes stale.

## Pattern (proven)

**Producer side** (the monitored host — pushes every 5 min):
```bash
#!/usr/bin/env bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"
/usr/bin/ssh -i KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=8 -p PORT root@MONITOR_HOST \
    "echo \$(date +%s) > /tmp/agent_heartbeat.txt" >> /tmp/heartbeat_push.log 2>&1
```
Run via cron `every 5m`, `no_agent=true`, `deliver=local` (silent watchdog).

**Consumer side** (the monitor — checks every 5 min):
```bash
LAST=$(cat /tmp/agent_heartbeat.txt); NOW=$(date +%s); AGE=$(( (NOW-LAST)/60 ))
if [ "$AGE" -ge 12 ]; then
  curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" -d "chat_id=$ALERT_ID" -d "text=DOWN ${AGE}m"
fi
```
Alert threshold should be **>2× the push interval** so one missed push doesn't false-alarm.

## Pitfalls (these bit hard)

4. **One ICMP packet is not evidence of death.** A `ping -c 1 -W 4` verdict flips to DOWN on a
   single dropped packet — routine on tailnet/wifi paths. Require ≥2 attempts spaced ~2 s, and
   treat **any** open probed port as UP even when ICMP is blocked (ICMP filtering is common and
   is not a fault). Otherwise the alert fires on packet loss, and the "outage" lasts seconds.
5. **Before touching a host that an alert calls down, prove it from where you sit**: `ping`, then
   `ss -tlnp`/port probes, then one SSH command (`uptime`). If uptime is long and services are
   running, the finding is "alert is wrong" — report that instead of restarting a healthy box.

1. **Cron `no_agent` jobs run with a MINIMAL `PATH`.** Bare `ssh` (and many other binaries) are "not found" → the script fails silently. ALWAYS `export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"` at the top of any cron script that calls `ssh`/`curl`/`git`, and use absolute paths (`/usr/bin/ssh`).
2. **Never `2>/dev/null` in a heartbeat/healthcheck script.** It eats the exact error that tells you *why* it failed. Log to a file (`>> /tmp/heartbeat_push.log 2>&1`) instead.
3. **Cron "status: ok" ≠ the side effect happened.** A no_agent job reports its *exit code*, not whether the SSH write landed. When a watchdog false-alarms, compare the cron job's `last_run_at` (scheduler fired) against the *actual side effect* (timestamp file on the remote) — a gap means the script ran but the write failed.

## Debugging a false "DOWN" alert (in order)
0. **Check the monitor's own inventory against reality FIRST.** Fleet monitors keep a
   `server_monitor_list.json`-style list of `{host, ts_ip, ssh_port}`. That file drifts:
   an entry still says `ssh_port: 22` while the host moved to `22022`, so the TCP fallback
   probes a port that was never open and reports DOWN forever. Read the inventory entry,
   then probe the *real* port. A closed port at the wrong number is a config bug, not an outage.
   **Fix the inventory once you find the drift** (correct `ssh_port` in the JSON) — otherwise the same
   false DOWN repeats on every tick, and the next session re-diagnoses a host that was never down.
1. Does the producer cron job have a recent `last_run_at` / status `ok`? (scheduler fired)
2. Does the remote heartbeat file actually have a fresh timestamp? (side effect landed)
3. If 1=yes, 2=no → script runs but the SSH write fails → check PATH/absolute-path/error log.
4. If 1=no → scheduler/gateway itself was down, not the target.

## Auto-restart with protection (proven 2026-08-26, 8 Hermes gateways)

When a watchdog goes beyond alerting and **auto-restarts** the monitored
service, these protections are mandatory — otherwise you get restart loops
and duplicate processes:

1. **flock lock file** — only ONE monitor instance may act; concurrent cron
   ticks / double-run are rejected. `exec 9> /tmp/monitor.lock; flock -n 9 || exit`
2. **Restart via `systemctl restart` (or the platform equivalent), NEVER
   `nohup … &`** — systemd stops the old process before starting the new one,
   so a service can't end up doubled. `nohup`/manual spawn is exactly what
   creates duplicate daemons.
3. **Max N restarts per bot per hour** (e.g. 2) — count in a per-service state
   file; after the cap, STOP restarting and escalate.
4. **Escalate to "needs human"** — after the cap is hit, send
   `PERLU TANGAN MANUSIA` instead of restarting again. Prevents a crashed-on-
   boot service from being churned forever.
5. **State file + delta logging** — write `last_status` (all-ok | restarting |
   needs-human); only log/notify on *change*, so a healthy run stays silent
   and dedupes notifications.

```bash
# skeleton — the lock + cap pattern
exec 9>/tmp/gw_monitor.lock; flock -n 9 || exit 0   # one monitor only
restart_count() { cat /tmp/gw_monitor/${svc}.count 2>/dev/null || echo 0; }
if [ "$(restart_count)" -ge 2 ]; then
  send_tg "🚨 ${svc} PERLU TANGAN MANUSIA (2x restart gagal)"
else
  systemctl --user restart "$svc"
  echo $(( $(restart_count) + 1 )) > /tmp/gw_monitor/${svc}.count
  send_tg "🔄 ${svc} auto-restarted"
fi
```

This is the concrete version of the cooldown note above; apply it to any
watchdog that auto-restarts.

## Poll-based monitors: prove the PATH, not just the host

A poll probe reports "target unreachable", which is NOT the same as "target down".
Before escalating, restarting anything, or telling the user the service died, rule out
your own vantage point — in this order:

1. **Re-probe from a second vantage**: an SSH jump host that can reach the target,
   ideally one in the target's own subnet —
   `ssh -J root@<peer-host>:22022 -p 22022 root@<target> 'hostname; uptime'`.
   If it answers there, the host is UP and your probe path is the fault.
2. **On the target, separate host-side blocking from upstream**: `ss -tlnp | grep <port>`
   (service really listening), `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:<port>/`
   (endpoint healthy from inside), `ufw status` (an `ALLOW Anywhere` line for that port rules
   out a ufw ACL), `fail2ban-client status <jail>` (banned list empty ⇒ not a ban).
3. **Compare routes from the monitor box**: `ip route get <failing-target>` vs
   `ip route get <peer-host-that-works>` — identical routes prove the block is remote
   (upstream anti-DDoS/WAF/ISP), not local routing.
4. **Pin WHEN it broke from the target's own log** — the last `Accepted publickey` from your
   source IP in `/var/log/auth.log` is the last moment the path worked; pair it with the
   monitor's last OK tick to get the window.

Only after 1-4 say "host down". "My egress IP cannot reach it (every port filtered, ping
loss, while a peer host in the same subnet answers)" is a *different* incident with a
different fix — typically an upstream anti-DDoS/WAF whitelist missing the monitor's IP, or
a userspace-tailscale TCP break while `tailscale ping` still succeeds. Move the probe to the
vantage that works (jump host / same-subnet host) or fix the whitelist; never let a monitor
whose path is broken keep alerting as if the service were dead.

## Health probe must test the DEPENDENCY, not just the local port

A probe that only asks "does the service's own port answer?" reports **healthy** while the host is
useless — a process bound to a local port keeps answering 200 even when outbound internet is dead.
Verified shape: the A2A endpoint returned **200 from localhost** the entire time the box had zero
egress (Telegram API, Discord, cloudflared tunnel all timing out), so the monitor stayed green and
the user noticed the silent bot first.

Pair the local check with an egress check in the SAME script:

```bash
LOCAL=$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:9900/)     # proses hidup
EGRESS=$(curl -s -m 8 -o /dev/null -w '%{http_code}' https://api.telegram.org)   # jalur keluar hidup
# EGRESS 200/302 = sehat ; 000 = egress mati → ALERT walau LOCAL=200
```

- `LOCAL=200` + `EGRESS=000` is its own alerting state ("hidup tapi tidak bisa keluar"), never OK —
  that is exactly when a bot goes mute while every port check passes.
- A route hijack on the target (exit node, VPN, wrong gateway) produces the same signature: answers
  locally, connects nowhere. Verify from inside with `ip route get <destination>`.

## Alert state machine (a bare cooldown is not enough)

A "send again if >N minutes since the last alert" cooldown **that resets its timestamp on
every send** fails twice over: during one sustained outage it re-alerts every N minutes
forever, and its text always claims "down N minutes" because the timer restarts each send —
the duration is wrong exactly when it matters. Keep real state instead:

- **up** — no `down_since` file → stay completely silent.
- **down** — on the FIRST failed probe write `down_since` only if it is unset, and alert
  once; afterwards alert only when `now - last_alert >= reminder_interval` (hours, not
  minutes). Compute the outage length from `down_since`, never from `last_alert`.
- **recovered** — on the first successful probe delete `down_since` and send ONE recovery
  line quoting the true outage length.

Status-change detection also dedupes across ticks, so a healthy run writes nothing at all.

## Notes
- Works for any NAT'd / platform-managed host (e.g. Hermes Cloud container, which has no public IP and no TUN device for Tailscale). Cross-host access there is SSH-by-IP, not Tailscale.
- Prefer an explicit alert-id plus the state machine above (`down_since` + reminder interval)
so a genuinely-down host doesn't spam every poll cycle and the reported outage length stays
true.
