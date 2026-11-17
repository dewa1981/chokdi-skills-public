---
name: google-api-auth-refresh
description: "Use when Google API calls fail with 403 or auth errors."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [google, oauth, token, refresh, drive, gmail, auth, 403]
---

# Google API auth from Hermes (token refresh + 403 triage)

One credential file serves Drive, Gmail, Calendar, Docs and Sheets on this host:
**`/opt/data/google_token.json`** — holds `token` (access), `refresh_token`,
`client_id`, `client_secret`, `scopes`, `expiry`. Every Google API call in any
skill depends on it, so a stale token looks like *every* integration breaking at once.

## When to Use

Load this skill when any of these happen:

- A Google API call returns **403** — especially `"Method doesn't allow unregistered callers"`.
- A Drive / Gmail / Calendar / Docs / Sheets script that used to work now fails auth, with no
  config change on your side.
- The user pastes a `drive.google.com` link and asks what it is / to read it (see
  `references/drive-link-read.md`).
- A cron job or backup script reports an auth failure against `/opt/data/google_token.json`.

Do NOT use it for a genuine missing-scope error on a fresh token, or for quota/plan problems
(those carry their own messages and are not auth failures).

## The signature failure: 403 "unregistered callers"

```json
{"error": {"code": 403,
  "message": "Method doesn't allow unregistered callers (callers without established identity). Please use API Key or other form of API consumer identity to call this API.",
  "errors": [{"reason": "forbidden", "domain": "global"}],
  "status": "PERMISSION_DENIED"}}
```

**This means the request went out with an empty or expired bearer token — NOT that a scope,
ACL, sharing setting, or API enablement is wrong.** The wording invites an ACL hunt; do not
start one. Any Google endpoint (Drive, Gmail, Calendar) returns this shape when the
`Authorization` header is missing or carries an expired token.

Triage in this order:

1. Read the token file and compare `expiry` (ISO-8601, UTC) against now. An `expiry` in the
   past means stale token — refresh it (below).
2. Only if `expiry` is in the future, look at `scopes` for the missing permission.
3. Only after both, consider API enablement in the Cloud project (that failure names the API:
   "... API has not been used in project <ID> before or it is disabled").

## Refresh in place (stdlib, no shell quoting traps)

Refresh and **write the new token back to the same file** so every later caller inherits it:

```python
import json, urllib.request, urllib.parse
tok = json.load(open('/opt/data/google_token.json'))
data = urllib.parse.urlencode({
    "client_id": tok['client_id'], "client_secret": tok['client_secret'],
    "refresh_token": tok['refresh_token'], "grant_type": "refresh_token"}).encode()
res = json.load(urllib.request.urlopen(
    urllib.request.Request("https://oauth2.googleapis.com/token", data=data), timeout=30))
tok['token'] = res['access_token']
tok['expiry'] = res.get('expiry')
json.dump(tok, open('/opt/data/google_token.json', 'w'))
print("refresh OK, expires_in:", res.get('expires_in'))   # never print the token
```

Then reuse `res['access_token']` in an `Authorization: Bearer <token>` header for the real call
in the same `execute_code` block — one refresh, one call, no second round-trip.

### Why not `curl` with an inline `$(...)` token

`curl -H "Authorization: Bearer $TOK" ...` where `TOK=$(python3 -c ...)` is the trap that
*reproduces this exact 403*: if the inner command fails or prints nothing, curl sends
`Authorization: Bearer ` and the request goes out unauthenticated — the error then looks like
a permissions problem while the real cause was the empty substitution. Use the urllib refresh
above, or read the token into a Python variable; if you must shell out, assert it is non-empty
(`test -n "$TOK" || echo EMPTY`) before calling.

## Rules

- **Never print or echo `access_token`, `client_secret`, or `refresh_token`** into chat, logs, or
  a report. Print `expires_in`, scopes, or the owning account email instead.
- **Refresh writes back to disk.** A refresh that is not persisted burns a round-trip and leaves
  the next caller (often a cron script) failing the same way.
- **One file, many Google accounts.** A host can hold tokens for a personal account plus agent
  accounts; never infer the owner from the token file's `account` field (usually empty — call
  `about.user.emailAddress` instead).
- **Do not report a 401/403 as "integration broken".** Say what was measured (expiry, scope) and
  what you did about it.
- Manual re-auth is only needed when refresh itself fails (revoked grant, password change,
  OAuth client changed, 6+ months idle): generate a fresh auth URL and have the user approve it.

## Support files

- `references/drive-link-read.md` — end-to-end procedure for "cari tau ini <drive link>":
  URL→file ID, metadata, download, extract, and the report order the user expects.
