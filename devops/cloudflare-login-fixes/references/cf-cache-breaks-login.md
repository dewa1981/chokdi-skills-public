# CF Cache-Everything breaks session logins + Komari password hash (proven 2026-08-10)

## Case: forum.sayasuka99.com login broken for months — "Oops! Something went wrong"
Flarum 2.0 forum (Docker nginx + php-fpm, host 163.61.44.61). Every browser login attempt
→ red banner "Oops! Something went wrong. Please reload the page and try again."
Even incognito. Curl straight at the origin container (inside `docker exec nginx`, Host
header set) → POST /login 200 + token. Curl through Cloudflare → 403 (datacenter IP,
normal).

### Root cause
Zone `sayasuka99.com` had a Cache Rule **"Cache Everything [Template]"** with expression
`true` → Cloudflare cached ALL HTML, including the forum's dynamic pages. The browser
received a cached page whose embedded `csrfToken` did not match the session cookie the
server issued → POST /login → **400, 2412-byte HTML page containing "You have been
inactive for too long."** Frontend shows the generic "Oops!" banner. Not a server bug,
not the user's cookies, not a wrong password.

### Diagnostic signature (use this ordering — don't blame the client first)
1. Origin curl with fresh CSRF token: `GET /` → parse `csrfToken":"..."` from HTML →
   `POST /login` with `identification/password/remember/csrfToken` + cookie jar → **200**.
   (Done from inside the nginx container with `-H "Host: forum.sayasuka99.com" -k https://127.0.0.1/`.)
2. Reproduce in a REAL browser (Browserbase / browser tools). If it 400s there too, it is
   NOT the user's cookies → server/CF layer.
3. nginx access log shows the split: `127.0.0.1` curl = 200, CF-edge IPs (162.158.x.x) = 400.
4. Check CF rulesets (read-only OK):
   `curl -s -H "Authorization: Bearer $TOK" https://api.cloudflare.com/client/v4/zones/$Z/rulesets/phases/http_request_cache_settings/entrypoint`
   → look for `action: set_cache_settings, expression: true` ("Cache Everything [Template]").

### Fix
- User (dashboard): Caching → Cache Rules → disable the "Cache Everything [Template]"
  rule (or narrow its expression), then **Purge Everything**.
- The RO token (`cfut_...` in /opt/data/cf_token_readonly.conf, zone
  `46742e94eccddcde768331f4cdefe0d2` = sayasuka99.com) can READ rulesets but
  `PUT` on the entrypoint returns `Authentication error` — dashboard edit or a write
  token is required.
- After the fix, the login error message CHANGES from "Oops! Something went wrong" to
  "Your login details were incorrect" — that transition proves the cache layer is fixed
  and only credentials remain.

### Prevent recurrence
- Never use `expression: true` cache rules on a zone that hosts dynamic apps.
- Dynamic apps on the same zone need their own bypass rule
  (`action: set_cache_settings, action_parameters: {"cache": false}`), ordered BEFORE
  any catch-all. komari.sayasuka99.com already had one — that's why Komari never broke.
- Rule order matters: first match wins.

## Komari admin password (server-monitor-panel-ops companion)
- `users` table (SQLite `/app/data/komari.db`, cols: uuid, username, passwd, sso_*).
- Password hash = **`base64(sha256(password + "06Wm4Jv1Hkxx"))`** — NOT bcrypt.
  Salt constant from `database/accounts/accounts.go` in komari-monitor/komari.
- Recompute/verify: `python3 -c "import hashlib,base64; print(base64.b64encode(hashlib.sha256((PW+'06Wm4Jv1Hkxx').encode()).digest()).decode())"`
- Bang's admin: `sayaano99` / `komari2026-ano99` (hash matches DB, verified).
- `POST /api/login {"username","password"}` → `401 {"message":"Invalid credentials"}`
  = wrong credentials only; server healthy. `200` → admin dashboard `/admin/dashboard`.
- DB inspect: `docker cp komari:/app/data/komari.db /tmp/komari.db` then sqlite3/python
  on the HOST — komari container image has no python3.
