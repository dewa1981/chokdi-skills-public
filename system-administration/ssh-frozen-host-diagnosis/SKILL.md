---
name: ssh-frozen-host-diagnosis
description: Use when SSH auth succeeds but no shell opens (frozen host).
---

# Diagnosing a FROZEN host from a remote machine

Use when you cannot get a shell on a server, and you need to tell apart
"network/firewall problem" from "the host itself is frozen" — WITHOUT console access.

## The tell-tale signature of a frozen host

Run ssh with full verbosity:
```bash
ssh -vv -p <port> -o ConnectTimeout=50 -o BatchMode=yes root@<ip> "echo OK" 2>&1 | \
  grep -iE "connect|Server host key|Authentications that can continue|Authenticated to|refused|timed out"
```

| What you see | Meaning |
|---|---|
| `Connection timed out` before anything | firewall/allowlist or host down |
| `Connection refused` | nothing listening on that port |
| `Connection established` + `Host key matches` + **`Authentication succeeded (publickey)`** + then **`Cannot open a new channel: Unexpected error`** | **HOST IS FROZEN** — auth works, the box cannot fork a process |

`Cannot open a new channel` (or a client GUI reporting the same after
"Authenticated to ...") is the strongest remote signal of resource exhaustion.
Do NOT keep retrying and do NOT rewrite auth config: authentication ALREADY works.

## Other probes that separate "frozen" from "unreachable"

- **ICMP ping** answers fast (e.g. 0.3 ms) → the machine and its network stack are alive.
- **TCP port check** — the SSH port may show OPEN while every service port
  (WebUI, A2A, HTTP/HTTPS) times out. A live sshd + dead services = frozen apps,
  not a dead host.
  ```bash
  for P in 22 22022 9000 9120 443 80; do
    timeout 6 bash -c "exec 3<>/dev/tcp/<ip>/$P" 2>/dev/null \
      && echo "port $P: OPEN" || echo "port $P: closed/timeout"
  done
  ```

## Companion symptom in agent fleets

When the frozen host runs Hermes gateways, the bot appears "online" in the chat
platform (Discord/Telegram shows the bot as a member, token still valid) but never
replies to DMs. Prove it from the platform side instead of guessing:
```bash
# read the DM channel history via the platform API and confirm the last user message has no reply
curl -s "https://discord.com/api/v10/channels/<dm-id>/messages?limit=5" \
  -H "Authorization: Bot <token>"
```
A valid-token bot that is a guild member but silent is a GATEWAY problem, not a
permissions problem — distinguish it from `Missing Access` (403), which is a real
permission issue.

## Do NOT chase these red herrings

- **`ssh_agent_bind_hostkey: agent refused operation`** / **`The agent has no identities`**
  — happens because the agent is EMPTY. It is not the cause: the server still accepted
the key file itself. Bypass the agent and retry to confirm the real failure point:
  ```bash
  SSH_AUTH_SOCK= ssh -i /root/.ssh/id_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes \
    -p <port> root@<ip> "hostname"
  ```
  If that still fails at the same place, the fault is on the remote host.
- **Permission denied (publickey)** is a DIFFERENT problem (key not installed).

## Recovery (requires console/panel — a remote agent cannot do this)

1. Try the provider's console/VNC first; if the console is unresponsive, hard
   reboot/power-cycle from the panel.
2. Once a shell is available, capture the CAUSE before restarting anything:
   `free -h`, `df -h /`, `uptime`, `dmesg -T | tail -50`,
   `journalctl -k -n 50 | grep -iE "oom|killed process"`.
3. Clean up per the finding (log vacuum, `docker system prune`, kill the memory hog),
   then bring services back up.
4. Log the incident (recovery sheet md in `/opt/data/`) and add a RAM/disk watchdog
   so the same freeze is caught before it takes the fleet down.
