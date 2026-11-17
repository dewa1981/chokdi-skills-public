---
name: mediacms-docker-migration
description: Use when migrating MediaCMS to Docker (backup, transfer).
---

# MediaCMS Migration: legacy non-Docker → modern Docker stack

Covers inventory, backup, transfer, and Docker deploy of MediaCMS. Based on a real
v3.1.0 (Nov 2023, non-docker uwsgi install) → v8.4.0 (Docker compose) migration.

## 1. Inventory the OLD install (read-only first)

Typical non-docker layout: `/home/mediacms.io/mediacms/` with venv at
`/home/mediacms.io/bin/`, services via systemd (`uwsgi`, `celery long/short/beat`),
PostgreSQL + Redis on localhost, port 9000 for uwsgi behind host nginx.

```bash
du -sh /home/mediacms.io/mediacms/media_files   # the big one (original/hls/encoded/chunks)
git -C /home/mediacms.io/mediacms describe --tags
git -C /home/mediacms.io/mediacms log -1 --format='%h %ci %s'
sudo -u postgres psql -tAc "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database WHERE datistemplate=false;"
```

PITFALL: `git` refuses with "dubious ownership" when the repo is owned by another user
(e.g. `www-data`). Fix with `git config --global --add safe.directory <path>`.

PITFALL: `sudo -u postgres pg_dump ... > /root/file` prints
`could not change directory to "/root": Permission denied` — the dump STILL SUCCEEDS.
Don't treat it as fatal; verify the file size and checksum instead.

## 2. Backup on the old server

```bash
DEST=/root/mediacms_backup_$(date +%Y%m%d); mkdir -p "$DEST"
sudo -u postgres pg_dump -Fc mediacms > "$DEST/mediacms_db.dump"   # custom format
sudo -u postgres pg_dump mediacms | gzip > "$DEST/mediacms_db.sql.gz"  # plain SQL
tar czf "$DEST/media_files.tar.gz" -C /home/mediacms.io/mediacms media_files
cp /home/mediacms.io/mediacms/cms/local_settings.py "$DEST/"
cp /home/mediacms.io/mediacms/deploy/local_install/mediacms.io "$DEST/mediacms.io.nginx.conf"
cd "$DEST" && sha256sum *.gz *.dump > CHECKSUM.txt
```
Keep BOTH dump formats: `-Fc` for `pg_restore` (handles PG-version drift better),
plain SQL as a readable fallback.

## 3. Transfer: pull from the destination, don't push

Preferred pattern — the DESTINATION server generates its own key and pulls:

```bash
# on destination:
ssh-keygen -t ed25519 -f /root/.ssh/<name>_pull_key -N '' -C 'lab-pull-<svc>'
cat /root/.ssh/<name>_pull_key.pub      # user pastes into old server's authorized_keys

# then:
rsync -avP --partial --inplace \
  -e 'ssh -i /root/.ssh/<name>_pull_key -p <port> -o StrictHostKeyChecking=no' \
  root@<old-ip>:/root/mediacms_backup_<date>/ /opt/mediacms-migrate/
cd /opt/mediacms-migrate && sha256sum -c CHECKSUM.txt   # MUST print OK
```

Always verify checksums on the destination. `--partial --inplace` makes it resumable.
Rate seen on a good link: ~40 MB/s (5 GB in ~2 min).

## 4. Deploy the Docker stack (fresh, BEFORE importing data)

```bash
mkdir -p /opt/mediacms && cd /opt/mediacms
git clone --depth 1 --branch v8.4.0 https://github.com/mediacms-io/mediacms.git .
docker pull mediacms/mediacms:latest    # ~2.2 GB
docker compose -f docker-compose.yaml config --quiet   # validate BEFORE up
```

The official `docker-compose.yaml` runs 6 services: `migrations` (one-shot),
`web`, `celery_beat`, `celery_worker`, `db` (postgres:17.2-alpine), `redis`.
`ENABLE_*` env flags pick the role per container.

### MANDATORY edits to the official compose
1. **`ports: "80:80"` → `"8099:80"`** — port 80 is almost always taken by host nginx.
   Symptom if you skip it: `failed to set up container networking: failed to bind host
   port 0.0.0.0:80/tcp: address already in use`.
2. **Move the DB data dir OUT of the repo dir** — `./postgres_data` or `../postgres_data`
   both break. The mediacms image declares `VOLUME /home/mediacms.io/mediacms/`, so every
   time a mediacms container starts Docker recreates the mounted dir owned by uid 33
   (www-data), clobbering any chown you did. Postgres (uid 70) then fails with
   `could not open file "global/pg_filenode.map": Permission denied` — while the
   healthcheck still reports `healthy` (`pg_isready` only probes the socket; it is a
   FALSE POSITIVE). Fix: `- /opt/<app>-db-data:/var/lib/postgresql/data/` plus
   `user: "70:70"` on the db service, and `mkdir + chown 70:70 + chmod 700` that dir.
3. **Pass DB and Redis env to EVERY app service (web, migrations, celery_*), not just db.**
   The official compose only sets `POSTGRES_*` on the `db` service, but
   `deploy/docker/local_settings.py` reads credentials from environment variables:
   `POSTGRES_HOST/PORT/NAME/USER/PASSWORD`. Without them, Django falls back to
   `mediacms:mediacms@localhost` and dies with
   `psycopg_pool.PoolTimeout: couldn't get a connection after 10.00 sec`.
   Also set `REDIS_LOCATION: 'redis://:<pass>@redis:6379/1'` if you enabled
   `requirepass` — the default has NO password and Celery/cache will fail.
   Set `FRONTEND_HOST: 'https://<domain>'` on web for correct absolute URLs.
4. **Passwords from `.env`**, never the hardcoded `mediacms/mediacms` default.
5. Add `cpus: 2.0` to `celery_worker` on shared hosts so video encoding cannot starve
   co-tenant services.
6. Set `TZ` from `.env` (default is `Europe/London`).

`.env` keys used by the official image: `POSTGRES_USER/PASSWORD/DB`, `REDIS_PASSWORD`,
`ADMIN_USER/EMAIL/PASSWORD`, `TZ`. `chmod 600 .env`.

PITFALL — `migrations` exits 0 even when EVERY query failed. `prestart.sh` does not
abort on error: after `PoolTimeout` it still prints "Created admin user with password"
and `collectstatic`, then exits 0. NEVER trust the exit code or `docker compose ps` for
this stack — verify with a real query:
`docker exec <db> psql -U <user> -d <db> -tAc "SELECT count(*) FROM django_migrations;"`
Healthy install = ~60 tables, ~72 migrations, >=1 user.

PITFALL — `role "postgres" does not exist` when probing with `psql -U postgres` is
NORMAL, not a fault: the cluster is initialised with `POSTGRES_USER` as the superuser
(there is no `postgres` role). Probe with the app user instead.

PITFALL — when the DB data dir must be wiped, wipe it AND recreate the stack together
(`docker compose down && rm -rf <data> && up -d`). Re-initialising a cluster while other
app containers hold stale connections/pools produces a confusing mix of auth failures
and `PoolTimeout` that looks like a credentials bug but is not.

PITFALL — heredoc writes into compose files silently fail. A `ssh host 'cat > f <<EOF'`
heredoc produced a file that still contained the ORIGINAL content (port 80, hardcoded
passwords). Detect it by checking `docker compose config` output, not by trusting the
write. Use a file upload / real write tool for YAML, then re-read and grep the file.

PITFALL — the `web` service may sit in `Created` without starting. If the port map is
empty (`docker inspect <web> --format '{{json .NetworkSettings.Ports}}'` → `{}`), the
compose being used is not the one you think. Re-check the file on disk first.

### Verify
```bash
docker compose ps --format 'table {{.Name}}	{{.Status}}'    # db+redis healthy
docker compose logs migrations --tail=20                     # migrations applied OK
docker port mediacms-web-1                                   # 80/tcp -> 0.0.0.0:8099
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8099/
curl -s http://127.0.0.1:8099/ | grep -oE '<title>[^<]*'     # <title>MediaCMS
```
`migrations` exiting with code 0 is SUCCESS, not a failure — it is a one-shot job that
runs `migrate`, `loaddata fixtures/`, creates the admin user, then `collectstatic`.

PITFALL — the admin password is generated randomly and printed to the migrations log
(`Created admin user with password: <random>`). To control it, set `ADMIN_PASSWORD` in
`.env` (passed through the `migrations` service env). Deliver credentials to the user
over a private channel (Telegram DM), never in a group chat or public log.

## 5. Import legacy data (Fase 3)

Old instance runs PostgreSQL 14; the compose ships 17.2. Plan: `pg_restore` the `-Fc`
dump into the new `db` container (`--no-owner --no-privileges`), then run
`python manage.py migrate` inside `web` to bridge the schema gap (v3 → v8 has many
migrations and fixtures). Extract `media_files.tar.gz` into the project dir so the
volume mount sees it. Always dump the DB again immediately before importing.

Working sequence that preserved all data (v3.1.0 → v8.4.0, 17 media / 7 users):
```bash
# 0. rollback point
docker exec <db> pg_dump -U <user> -d <db> -Fc > /opt/<app>-migrate/db_BEFORE_IMPORT.dump
# 1. stop writers, park the fresh DB somewhere safe
docker compose stop web celery_worker celery_beat
docker exec <db> psql -U <user> -d postgres -c "ALTER DATABASE <db> RENAME TO <db>_fresh;"
docker exec <db> psql -U <user> -d postgres -c "CREATE DATABASE <db> OWNER <user>;"
# 2. restore legacy dump
docker cp /opt/<app>-migrate/<db>.dump <db>:/tmp/legacy.dump
docker exec <db> pg_restore -U <user> -d <db> --no-owner --no-privileges /tmp/legacy.dump
# 3. bridge the schema (this is the step that actually upgrades v3 -> v8)
docker compose run --rm -e ENABLE_UWSGI=no -e ENABLE_NGINX=no -e ENABLE_CELERY_SHORT=no \
  -e ENABLE_CELERY_LONG=no -e ENABLE_CELERY_BEAT=no migrations python manage.py migrate --noinput
# 4. start writers again
docker compose up -d
```
Migrations went 35 → 72 and tables 38 → 60 while `files_media` stayed at 17 — proof the
upgrade ran without data loss. `pg_restore` re-run errors ("relation already exists")
are expected noise if you run it twice; the FIRST run is what counts.

Media verification (do this, don't assume): `files_media.media_file` stores
`original/user/<u>/<file>.mp4` — relative to `MEDIA_ROOT` (`/home/mediacms.io/mediacms/media_files/`).
So the working URL is `/media/original/user/<u>/<file>` and must return 200 with the full
byte size. `/media/user/<u>/<file>` (no `original/`) returns 404.

## 6. Cut over the domain and prove the cutover

On a host that already runs a cloudflared tunnel, add the hostname to
`/etc/cloudflared/config.yml` (`- hostname: <domain>` / `service: http://127.0.0.1:<port>`
BEFORE the trailing `- service: http_status:404`), back the file up first, validate with
`python3 -c "import yaml; yaml.safe_load(open(...))"`, then `systemctl restart cloudflared`.

PITFALL — an existing DNS record may still point at the OLD server. Check the record
before assuming the tunnel is serving: the site can answer 200 while still hitting the
old host, which makes the cutover look done when it is not. Convert
`A <domain> -> <old-ip>` into `CNAME <domain> -> <tunnel-id>.cfargotunnel.com` (proxied).

Prove the cutover from the destination, not from HTTP status alone: the source of truth
is the app container's access log on the NEW host showing the request,
`docker compose logs web --tail` → `"GET /view?m=<token> HTTP/1.1" 200`. Also confirm the
old host is unreachable (`ssh: connect ... Connection timed out`).

## 7. Post-cutover watchdog

Keep the old server powered on for ~24h and poll the new stack every 4h (a small script +
`/etc/cron.d/<name>`), reporting to a monitoring chat. Each run should check: home page
200, one migrated media page 200, and whether the old host is now unreachable — the last
one is the signal the cutover is real. Write state to a JSON file so the job self-terminates
after the window instead of notifying forever, and always verify the FIRST notification
actually delivered (`"ok":true` from the Telegram API) before telling the user it is set up.
