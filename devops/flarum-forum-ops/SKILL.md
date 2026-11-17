---
name: flarum-forum-ops
description: Use when fixing Flarum login/site issues on 163.61.44.61.
---

# Flarum Forum Ops (forum.sayasuka99.com — 163.61.44.61)

Flarum forum on 1Panel host 163.61.44.61 (SSH port 6619). Stack: `nginx` container (nginx:alpine, vhosts from /home/web/conf.d), `php` container (kjlion/php:fpm-alpine, PHP 8.4, fpm socket `/run/php/php-fpm.sock`), `mysql` container. Site root `/var/www/html/forum.sayasuka99.com` (host mount /home/web/html). DB `forum_sayasuka99_com`, user `a87bfef5`, password in config.php.

## Architecture notes
- Vhost: `/etc/nginx/conf.d/forum.sayasuka99.com.conf` inside nginx container — view with `docker exec nginx sh -c 'nginx -T'`.
- nginx container has NO docker CLI and NO php. Run PHP via `docker exec php php ...`, SQL via `docker exec mysql mysql -ua87bfef5 -p<pass> forum_sayasuka99_com -e "..."`.
- `flarum_users` table: `password` column = bcrypt (`$2y$10$...`). Sessions in `flarum_access_tokens` (`session_remember` rows). Password-reset tokens in `flarum_password_tokens`.

## Testing login without CF interference
Cloudflare in front → curl from the server IP gets 403 challenge. Bypass by curling from INSIDE the nginx container with a Host header (origin = https://127.0.0.1 works, cert is fine with -k):
```bash
docker exec nginx sh -c 'rm -f /tmp/jar; curl -s -k -m 10 -c /tmp/jar -H "Host: forum.sayasuka99.com" https://127.0.0.1/ -o /tmp/pg.html; TOKEN=$(grep -o "csrfToken\":\"[^\"]*" /tmp/pg.html | head -1 | cut -d\" -f3); curl -s -k -m 10 -b /tmp/jar -c /tmp/jar -H "Host: forum.sayasuka99.com" -H "Content-Type: application/x-www-form-urlencoded" -H "X-Requested-With: XMLHttpRequest" -H "Origin: https://forum.sayasuka99.com" --data-urlencode "identification=USER" --data-urlencode "password=PW" --data-urlencode "csrfToken=$TOKEN" https://127.0.0.1/login'
```
- Flarum login = POST /login (form) and needs the page's `csrfToken` + cookie jar from the GET.
- **"You have been inactive for too long." (HTTP 400) = missing/stale CSRF token — NOT a session timeout.** This exact page appears when POST /login is sent without the token.
- Wrong password → 401 `{"errors":[{"status":"401","code":"not_authenticated"}]}`. Success → **200 `{"token":"<40-hex>","userId":1}`**.
- Diagnose a broken hash fast: `SELECT id,username,LEFT(password,7) FROM flarum_users` — `$2y$10$` = healthy bcrypt; **empty string = a previous shell-interpolated UPDATE ate the `$`s** (see reset below).

## Password recovery (root cause of "login error / Oops")
Symptom 2026-08-10: login modal "Oops! Something went wrong. Please reload..." — web itself healthy; DB/web/CSRF all fine. Root cause: the stored password hash simply doesn't match what the user remembers. Fix = reset `flarum_users.password` directly:
- ⚠️ **NEVER inject a bcrypt hash through shell interpolation** (`UPDATE ... SET password="$HASH"`): `$2y$10$...` contains `$` which bash expands → the password lands empty/garbage → still 401. This bit us and wasted a full verify cycle. Symptom to watch: the UPDATE's SELECT shows `pw` (LEFT 4) as **blank**, not `$2y$`.
- SAFE: run `scripts/reset_password.php` inside the php container (PDO + password_hash in ONE PHP process, argv-passed password, no shell mangling). Script self-verifies with password_verify; then confirm with the login curl above (expect 200).

## ROOT CAUSE 2026-08-10 — CF "Cache Everything" broke login — RESOLVED ✅
Even AFTER the password was reset correctly (origin curl login = 200), the browser STILL gets 400 "Oops!" — normal AND incognito. Reproduced with a real browser (browser tools) → same 400. So NOT a cookie problem on the user's side.
- **Cause found**: CF zone `sayasuka99.com` has a Cache Rule **"Cache Everything [Template]"** with `expression: true` → applies to ALL subdomains INCLUDING the forum → CF serves the cached HTML page → the `flarum_session` Set-Cookie gets swallowed → every POST /login is a fresh session with a stale token → 400 "inactive for too long".
- **Proof pattern**: origin curl (docker exec nginx, Host header) = 200; anything through CF = 400. Access log shows 400s from CF IPs (162.158.x.x) vs 200 from 127.0.0.1.
- **FIX APPLIED 2026-08-10 (by Bang in CF dashboard, ~2 min)**: Caching → Cache Rules → disable "Cache Everything [Template]" (or exclude the forum) → **Purge Everything**. Verify with a real browser (browser_navigate + type + submit → expect menu user visible). ✅ Login now works: `sayasuka99` / `Admin999!@#` (user was told to change it).
- **Generalize**: any site on this zone with login breaks the same way; check CF cache rules FIRST when "origin works, public URL fails on POST". Komari was NOT affected — it has its own `cache: false` bypass rule, confirmed working (login OK, `sayaano99`/`komari2026-ano99`; a session-cookie quirk on Edge was a browser-extension cookie block — Firefox works).

## Pitfalls
- Don't brute-force password candidates against the hash — reset it directly (that's the answer, not guessing).
- CF caches pages ~5 min: always verify via docker-exec curl against origin, not the public URL.
- **WAF/cache rule introspection with read-only token**: `GET /zones?name=sayasuka99.com` → zone id; `GET /zones/<id>/rulesets/phases/http_request_firewall_custom/entrypoint` (WAF) and `.../http_request_cache_settings/entrypoint` (cache rules) work read-only. Editing needs a write token.
- Backup BEFORE any repair (Bang's SOP): `mysqldump --single-transaction --no-tablespaces` (the `--no-tablespaces` flag is REQUIRED — without it, non-PROCESS-privilege users error "Access denied ... PROCESS privilege") + tar of the site dir via `docker exec nginx` + `docker cp` out. Store under /opt/backup_forum/.
- Flarum app boot for custom scripts is awkward (Application needs Container + Paths + full boot); plain `new PDO(...)` from config.php is enough for DB work — don't fight the framework.
