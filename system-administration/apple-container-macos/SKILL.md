---
name: apple-container-macos
description: Install & fix Apple container on macOS 26 Apple silicon.
---

# Apple container on macOS 26 (proven 2026-09-09, Mac mini M4 Pro)

`container` (github.com/apple/container) = run Linux containers as lightweight
VMs on a Mac. Written in Swift, optimized for Apple silicon (M4 Pro). Requirements:
**Apple silicon + macOS 26** (uses new virtualization/networking). Two features:
`container run/create` (Linux container) and `container machine` (persistent
Linux env with auto home-sharing).

## Install
1. Download signed installer from GitHub releases (latest e.g. `1.3.1`):
   `container-<v>-installer-signed.pkg`.
2. Install: `sudo installer -pkg ~/Downloads/container-<v>-installer-signed.pkg -target /`
   (needs admin password).

## The XPC `Connection invalid` fix (THE hard part)
`container system start` fails with
`XPC connection error: Connection invalid` on macOS 26 (even after reboot, kernel
flags, debug, in GUI) because:
- **`container system start` under `sudo` computes the WRONG launchd domain**
  (e.g. `gui/0`/`user/0` when it should be `gui/501`), so `container-apiserver`
  fails to bootstrap → the error is swallowed → generic XPC error.
- Also fails if the user home is on an external volume (needs `--app-root` on
  the INTERNAL disk).

WORKING SETUP (order matters):
```bash
# 1) app-root MUST be on internal disk (not home on external volume)
APP_ROOT="/Users/Shared/apple-container-${USER}"
mkdir -p "$APP_ROOT"; chmod 700 "$APP_ROOT"
sudo chown -R "${USER}":staff "$APP_ROOT"   # so the user can write the plist

# 2) write plist + start apiserver (NO sudo — the user must own/attach it)
container system start --app-root "$APP_ROOT" --timeout 60

# 3) IF it still fails, bootstrap the apiserver into the LOGGED-IN user domain
#    (7894/501 = the real uid). This is the key fix for XPC invalid:
sudo launchctl bootstrap gui/501 "$APP_ROOT/apiserver/apiserver.plist"

# 4) set the Kata kernel (NO sudo — kernel set under sudo gives "unauthorized")
container system kernel set --recommended   # downloads kata-static 3.28.0 arm64
#    (if "File exists" error, the kernel is already installed — it is fine)

# 5) test
container system status
container run --rm alpine echo hello      # should print 'hello'
```

## Gotchas
- **Skip `sudo` for most `container` commands** (start, kernel set, run)
  — they must run as the logged-in **user (uid=501)** to match the apiserver in
  `gui/501`. Under `sudo` they either XPC-invalid or return "unauthorized request".
- **`--app-root` must be internal** disk.
- **After install/upgrade, `container version` shows "Plugin not found"** until
  `container system start` has run (the plugins load with the apiserver).
- **Kernel**: `container system kernel set --recommended` (no sudo). The Kata
  kernel URL: `https://github.com/kata-containers/kata-containers/releases/download/3.28.0/kata-static-3.28.0-arm64.tar.zst`.
- **Network `no available interface strategy`** on 1.3.1 → run
  `container system stop` then `container system start --app-root ...` again
  (a clean stop/start makes the vmnet interface strategy appear).
- **`container machine run` interactive** gives `Inappropriate ioctl` over SSH
  (TTY); use `container machine run -n <name> -- <cmd>` for non-interactive.

## Install apps in a container machine (use `-u root`, sudo is broken)
`container machine run` runs commands as the host USER (not root), and **`sudo`
is BROKEN in the container machine** (any `sudo X` prints the sudo usage / fails
— even `sudo whoami`). To install/run system apps (mariadb, nginx, etc.) run
AS ROOT:
```bash
container machine run -n <machine> -u root -- bash -c "apt-get update && apt-get install -y mariadb-server nginx"
container machine run -n <machine> -u root -- bash -c "systemctl start mariadb; nginx; curl -s http://localhost/"
```
- **DNS in the machine is NOT auto-set** (resolv.conf is empty / uses vmnet gateway
  192.168.64.1 which may not forward). To fix apt/internet:
  `sudo systemctl stop systemd-resolved; sudo systemctl disable systemd-resolved;
  sudo sh -c 'printf "nameserver 8.8.8.8\nnameserver 1.1.1.1\n" > /etc/resolv.conf'`
  (do this ONCE; with `-u root` you can drop the `sudo` prefix). After that
  `apt-get update` fetches from kali.download at ~14 MB/s.
- Verify: `container machine run -n <machine> -u root -- mariadb -e "SELECT VERSION()"`
  and `curl -s -o /dev/null -w '%{http_code}' http://localhost/` → `200`.

## Kali Linux container machine (persistent) — proven 2026-09-09
`container machine` (persistent env) needs an image **with an init system**
(`/sbin/init`). The official `kalilinux/kali-rolling` image has NO init →
`container machine create` sticks at `stopped`. Build a Kali image + systemd:
```dockerfile
FROM kalilinux/kali-rolling
ENV container container
RUN apt-get update && apt-get install -y systemd dbus openssh-server \
    net-tools iproute2 iputils-ping curl nmap && apt-get clean
RUN >/etc/machine-id; RUN >/var/lib/dbus/machine-id
RUN systemctl set-default multi-user.target
RUN systemctl mask dev-hugepages.mount sys-fs-fuse-connections.mount \
      systemd-update-utmp.service systemd-tmpfiles-setup.service console-getty.service
# NOTE: do NOT try to write /etc/resolv.conf in the Dockerfile — it is READ-ONLY
# in the build container ("cannot create /etc/resolv.conf"). The container machine
# handles DNS itself (ping 8.8.8.8 works without manual resolv.conf).
```
**Build with `--dns` (critical):** the builder container has no DNS by default;
without it apt fails with "Unable to locate package".
`container build --dns 8.8.8.8 -t local/kali-machine:latest .`
Then `container machine create local/kali-machine:latest --name kalimachine`
→ `container machine ls` shows `kalimachine running`; `container machine run -n
kalimachine -- nmap --version` → Nmap; `ping 8.8.8.8` → works.
Don't add `networkd-dispatcher` to the Dockerfile — it does NOT exist on Kali
(`systemctl disable networkd-dispatcher.service` fails).

## Verify
- `container system status` → `status running`, apiserver version.
- `container run --rm alpine echo hello` → `hello`.
- `container run --rm alpine uname -a` → Linux aarch64 kernel.
- `container run -d --name <n> alpine sleep 60` then `container exec <n> <cmd>`
  → command runs inside.
- `container machine create alpine:latest --name dev` → `container machine ls`
  shows `dev` running; `container machine run -n dev -- whoami` → the Mac user.

## References
- apple/container issues #1721 (external home / --app-root fix) and
  #2008 (launchctl bootstrap domain under sudo).
- docs: github.com/apple/container (README, technical-overview, container-machine).
