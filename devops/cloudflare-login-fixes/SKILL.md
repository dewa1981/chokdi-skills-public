---
name: cloudflare-login-fixes
description: Use when a web app behind Cloudflare can't log in.
version: 1.0.0
---

# Cloudflare cache vs session logins — diagnosis & fix

Dynamic apps (forums, admin panels, dashboards) behind Cloudflare that suddenly
(or for months) refuse logins with a generic error — while curl to the origin
works — are almost always a **CF cache rule caching the dynamic HTML**.

## The classic signature (proven forum.sayasuka99.com, 2026-08-10)
- Browser (incl. incognito) → login fails with generic "Oops! Something went
  wrong" / "Please reload the page and try again".
- curl straight to the ORIGIN with a fresh CSRF token + cookie jar → login 200.
- Reproducing in a REAL browser (Browserbase) fails too → NOT the user's cookies.
- nginx access log: origin-IP requests 200, CF-edge IPs (162.158.x.x) 400.
- Root cause: zone Cache Rule "Cache Everything [Template]" with expression
  `true` caches the dynamic HTML → stale `csrfToken` vs fresh session cookie →
  CSRF mismatch → 400, body "You have been inactive for too long."

## Fix
- Caching → Cache Rules → disable the `true` catch-all rule (or narrow its
  expression), then **Purge Everything**.
- Read-only CF token can list rulesets:
  `GET /zones/{z}/rulesets/phases/http_request_cache_settings/entrypoint`
  (zone `46742e94eccddcde768331f4cdefe0d2` = sayasuka99.com; token
  `cfut_...` in /opt/data/cf_token_readonly.conf).
- Editing rulesets via API needs a WRITE token — the RO token's PUT returns
  "Authentication error". Dashboard edit or write token required.
- After the fix, the error changes to "Your login details were incorrect"
  (= auth layer reached) — that transition is the confirmation.

## Prevention
- Never use `expression: true` cache rules on a zone hosting dynamic apps.
- Per-host bypass for dynamic apps: `set_cache_settings` with
  `action_parameters: {"cache": false}`, ordered BEFORE any catch-all
  (first match wins). komari.sayasuka99.com had one — Komari never broke.

## Login-troubleshooting order (don't blame the client first)
1. Origin curl with CSRF flow (200 = server fine).
2. Real-browser repro (Browserbase) — isolates user-cookie vs server/CF.
3. nginx access log split (origin 200 / CF-edge 400).
4. CF ruleset read (find the `true` catch-all).
5. THEN look at credentials.

## But when the app is NOT CF-cached: blame the CLIENT (proven komari 2026-08-10)

A login pop-up loop where the server is fine (fresh session rows every few
seconds in the app's session table, 200 POST /api/login in logs, WS healthy,
CF bypass active) and login WORKS in a different browser / private mode =
**browser extension blocking the session cookie**, not cache and not the
server. Fix: whitelist the domain in the adblock/privacy extension
(uBlock/AdGuard/Privacy Badger) or use Firefox/InPrivate. Check order once
server-side is confirmed clean: (1) different browser / InPrivate, (2)
extension whitelist, (3) browser cookie settings — server last. Also covers
"login works but LOGOUT button missing / shows Login while logged in" (same
cookie-not-sent mechanism, cf. komari-monitor-ops).

## Support files
- `references/cf-cache-breaks-login.md` — full diagnostic transcript + fix steps (2026-08-10).
- `references/flarum-password-reset-db.md` — Flarum password reset via direct DB (PHP container) + shell-quoting pitfall that nulls bcrypt hashes.
- `scripts/flarum_reset_pw.py` — one-shot Flarum password reset (safe hash write + verify).
