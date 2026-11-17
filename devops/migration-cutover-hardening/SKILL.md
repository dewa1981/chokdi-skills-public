---
name: migration-cutover-hardening
description: Use when cutting a live site over to a new host.
---

# Cutover: moving a live site to a new host/client stack safely

The last mile of any server migration — proving the new host is really serving, proving the
old one is really gone, and not losing the DNS record that got you there. Applies to any
"pindahkan situs X ke server baru" job (web app, CMS, report site).

## 1. Write verification: prove the file landed, not that the command ran

Remote writes fail silently. A `ssh host 'cat > f <<EOF'` heredoc can leave the ORIGINAL file
untouched while returning exit 0, and a YAML typo can hide behind a valid-looking run.

```bash
grep -n '<the-new-value>' <file>          # runs straight after the write, before using it
docker compose config --quiet             # task's own validator, second check
```

If the expected value is absent, the write never landed — rewrite it with a real file-write
path (upload/`scp`/a local `write_file` then copy) instead of re-running the heredoc.
Symptom of skipping this: the service starts happily on the OLD config (`ports: 80:80`, stale
passwords) and the failure surfaces later as a confusing bind/permission error.

## 2. Never trust a "healthcheck" that only probes a socket

`pg_isready`, a TCP connect, or a landing page returning 200 prove only that SOMETHING
listens. They pass while the service is unusable. Verify with a real transaction/view on the
same object the task cares about:

- DB: `SELECT count(*) FROM <known-table>` must return a NUMBER, not an error.
- App: fetch the page AND grep the body for a known string; for content, fetch one media/asset
  URL and assert a plausible byte size (a few hundred bytes = an error page, not a video).
- Jobs: check the tables/records the first real run should have written.

A container showing `healthy` next to an app that cannot read its own data is expected when the
check is socket-only — treat it as "unknown", never as "verified".

## 3. Check the DNS record BEFORE concluding the cutover worked

The domain can answer HTTP 200 while still being proxied to the OLD host — a stale `A` record
pointing at the old IP looks exactly like success. Confirm the record's content, not just the
status code:

```bash
curl -s -4 "https://api.cloudflare.com/client/v4/zones/<ZONE>/dns_records?name=<domain>" \
  -H "Authorization: Bearer $CF_TOKEN"
```

Then convert it, recording the OLD value in your report so it can be restored:
`A <domain> -> <old-ip>` becomes `CNAME <domain> -> <tunnel-id>.cfargotunnel.com` (proxied)
when the new host is behind a Cloudflare tunnel.

## 4. Prove the cutover from the DESTINATION's own log

HTTP 200 is not proof of where the traffic went. The source of truth is the request appearing
in the new host's app log:

```bash
docker compose logs web --tail=20 | grep 'GET <path>'
```

Do this while the old host is still up. Then confirm the old host is unreachable
(`ssh: connect ... Connection timed out`) and re-fetch the page — a 200 that survives the old
host being off is the actual proof. Only then is turning the old server off safe.

## 5. Keep the tunnel as the single ingress pattern on a shared host

When the destination already runs a cloudflared tunnel, add the hostname to that tunnel instead
of publishing an IP or a new port:

1. Back up `/etc/cloudflared/config.yml` FIRST.
2. Insert `- hostname: <domain>` / `service: http://127.0.0.1:<port>` **before** the trailing
   `- service: http_status:404` catch-all (order matters — ingress is first-match).
3. Validate: `python3 -c "import yaml; yaml.safe_load(open('/etc/cloudflared/config.yml'))"`.
4. `systemctl restart cloudflared`, then confirm the log shows `Registered tunnel connection`.

Benefits worth stating to the user: automatic TLS, DDoS protection, and the origin IP stays
private. Do NOT "simplify" by pointing DNS at the host's public IP — it loses TLS, exposes an
internal host that runs other services, and gains nothing.

## 6. Post-cutover observation before deleting anything

Leave the old server powered on for ~24h and poll the new stack periodically, then make the
final decision from the collected data. Each probe should check the home page, one migrated
content page, and whether the old host is unreachable — that last one is the signal the cutover
is real. Keep state in a JSON file so the job self-terminates instead of notifying forever, and
confirm the first alert actually delivered before telling the user it is set up. Keep the
rollback artifacts (pre-import DB dump, parked copy of the fresh DB, media tarball) until the
observation window closes.

## Pitfalls

- **Report the old value of anything you change.** DNS targets, ports, and paths must be quoted
  back so the user can revert without archaeology.
- **Do not treat an HTTP 200 as "live on the new host"** until the destination log shows the
  request — this is the single most common way a cutover gets reported done while still serving
  from the old machine.
- **A staged migration has an explicit schedule.** Dumping the DB, creating the new one, running
  migrations, and starting writers are separate steps; verify counts (`media=17`, `users=7`) after
  each instead of chaining them silently.
- **Credentials go to a private channel** (DM), never into a group chat or a public log — the
  migration logs often print a randomly generated admin password.
