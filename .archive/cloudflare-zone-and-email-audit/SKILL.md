---
name: cloudflare-zone-and-email-audit
description: Use when auditing a Cloudflare zone or email setup.
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [cloudflare, dns, email, routing, sending, dmarc, zone-lookup]
    related_skills: [cloudflare-api-ops, cloudflare-email-routing, cloudflare-dns-ops]
---

# Auditing a Cloudflare zone and its email setup

Read-only reconnaissance for any Cloudflare work: locate the zone, dump its DNS, and
establish exactly what email state a domain is in **before** changing a record. The audit is
always safe to run; the write is what needs the user's go-ahead.

## When to Use

- User asks "cek DNS domain X" / "domain ini ada fitur email ga" / "kenapa email tidak masuk".
- Before enabling Email Sending (onboarding writes SPF/DKIM/DMARC — see step 5).
- A domain must be located in a large account ("domain saya tidak ada di akun" is usually a
  pagination artefact, step 1).
- Any `cf` CLI call returns `Zone not found` or `No zone specified` (steps 1–2).

## Step 1 — `cf zones list` paginates: page 1 is not the account

20 zones per page. A domain absent from page 1 is a **false negative** — a real account here
held 57 zones across 3 pages, and the target domain was on page 3. Walk until a page is
empty:

```bash
for p in 1 2 3 4 5 6 7 8; do
  cf zones list --page $p > /tmp/zp.txt 2>&1
  [ "$(grep -c '\"status\":' /tmp/zp.txt)" -eq 0 ] && break   # empty page = done
  grep -i "<domain>" /tmp/zp.txt && echo "FOUND on page $p"
done
```

Report the **zone ID**, not just "found" — every later command needs it.

## Step 2 — some subcommands reject the zone NAME but accept the zone ID

```
cf email-sending subdomains list -z example.com
→ ┌ Error  │ Zone not found: example.com
cf email-sending subdomains list -z <32-hex-zone-id>
→ []          # correct
```

Name rejected + ID accepted = a name-resolution quirk, **not** a token/permission failure.
Retry with the ID before reporting an auth error, otherwise you send the user chasing
credentials that were fine.

`-z/--zone` is mandatory for zone-scoped subcommands; omitting it gives "No zone specified"
with the three valid ways to supply it (positional, `--zone`, `CLOUDFLARE_ZONE_ID` env var).

## `cf` beta CLI: product subcommands, `schema`, and `send --body`

The beta `cf` CLI follows `<product> <subcommand>`, so do not hand-roll curl for anything
that already has a command:

```bash
cf email-sending subdomains {list,create,get,preview,dns,reputation}
cf email-sending {send,send-raw,limits,get,suppressions}
cf email-sending subdomains dns {get,status,fix}     # fix = writes ALL records — see Step 6
cf email-routing {enable,disable,addresses,rules,dns,settings}
cf zones list / cf dns records list / cf accounts list / cf billing
```

**`cf schema <command>` prints the exact API request** (method, path, `requestBodyFields`) —
use it to find flags that `--help` does not list. `cf email-sending send`, for example,
exposes no per-field flags beyond `--body`, so the CLI send is JSON directly:

```bash
cf email-sending send --body '{"to":"a@b.com","from":"test@domain.com",
  "subject":"...","text":"..."}'
# → {"message_id":"<...@domain.com>","delivered":["a@b.com"],"permanent_bounces":[]}
```
An empty `permanent_bounces`/`suppressed_recipients` with a non-empty `delivered` = really
accepted. Read the response body, not the exit code.

**`--dry-run` on write subcommands only echoes HTTP method + URL + body** — it does NOT list
the DNS records that would be added. Do not treat it as a safety net for DNS changes.

## Step 3 — dump DNS to a file, then parse the file

```bash
cf dns records list -z $ZID --per-page 200 > /tmp/dns.txt 2>&1
grep -c '"type":' /tmp/dns.txt                                        # count
grep -oP '"type": "\K[^"]+' /tmp/dns.txt | sort | uniq -c | sort -rn  # recap per type
```

Piping `cf` JSON straight into `python3 -c` is fragile and trips command security scanners —
redirect to a file first, then parse it.

When summarising for the user, **group by record NAME** and show type + content, flagging
`proxied: true/false` (orange-cloud vs DNS-only). A flat list of hundreds of A records buries
the answer; a per-name grouping is readable at a glance.

## Step 4 — Routing and Sending are separate products

Do not report one as the other. They use **different SPF includes**:

| Marker | Means |
|---|---|
| MX `route1/2/3.mx.cloudflare.net` | Email **Routing** (inbound) enabled |
| SPF `include:_spf.mx.cloudflare.net` | authorizes Cloudflare for **inbound routing only** |
| MX on `cf-bounce.<domain>` exists | Email **Sending** onboarded |
| `cf2024-1._domainkey` TXT present | DKIM; routing creates it, sending reuses it |

A domain can be routing-enabled and sending-disabled at the same time — commonly is. Always
report four rows separately: **Routing / Sending / SPF (which service) / DMARC policy**.

Also read the catch-all, because "Routing is enabled" does not mean mail is accepted:

```bash
cf email-routing settings get   -z <zone-id>
cf email-routing rules catch-all get -z <zone-id>
cf email-sending subdomains list -z <zone-id>   # [] = sending not onboarded
cf email-sending limits get                     # null/null = never activated on account
```

A catch-all with `enabled: false` and `actions: [{type: "drop"}]` silently **discards** mail to
unmatched addresses. Test with an address that has an explicit rule, or you will diagnose a
working pipeline as broken. The full "can it receive?" verdict matrix is step 7.

## Step 5 — DMARC is the risk dial; read it before proposing a write

| Policy | Risk to act on this domain |
|---|---|
| `p=reject` | Highest. A mistake rejects real mail. Do not experiment here |
| `p=quarantine` | Medium. Failures land in spam |
| `p=none` | Lowest — failures are only reported. The right place to trial |
| no `_dmarc` | Safe-ish, but no failure reports |

Enabling Email Sending adds SPF/DKIM/DMARC records, and **two SPF or two `_dmarc` TXT records
make both invalid**. So: never trial Sending on a production `p=reject` domain, and prefer a
`p=none` domain or a dedicated sending subdomain.

## Step 6 — Onboarding Email Sending: apply records ONE BY ONE, never `dns fix`

This is the write that follows the audit. `cf email-sending subdomains create -z <zone-id>
--name <domain>` creates the sending entry but **does not install the DNS records**:

```bash
cf email-sending subdomains create   -z <zone-id> --name <domain>   # entry only
cf email-sending subdomains dns get  <subdomain-id> -z <zone-id>    # records needed + DKIM value
cf email-sending subdomains dns fix  <subdomain-id> -z <zone-id>    # ⚠️ do NOT run blindly
```

**`dns fix` writes the FULL record set including its own `_dmarc`** — and Cloudflare's
version is `v=DMARC1; p=reject;` with **no `rua` tag**. On a domain that already has a DMARC
record this either produces two `_dmarc` TXT records (invalid per RFC 7489 — reporting and
enforcement both stop) or, if it wins, drops to `p=reject` **without reports**, killing the
DMARC alerting pipeline and risking rejection of legitimate mail.

Safe procedure:

1. Back up first: `cf dns records list -z <zone-id> --per-page 200 > backup.json`.
2. Read the exact records and DKIM value from `subdomains dns get` — take the DKIM string
   from there, never retype or invent it (they are long RSA keys).
3. POST each missing record via the DNS API: 3× MX `cf-bounce.<domain>` (with the reported
   priorities), TXT SPF `cf-bounce.<domain>`, TXT DKIM `cf-bounce._domainkey.<domain>`.
   The server usually installs the MX records itself — list existing records first and skip
   anything already present rather than POSTing duplicates.
4. **Leave `_dmarc` untouched.**
5. Verify with `dig` per record, including that `_dmarc` still shows the original
   `p=none` + `rua` — DNS is authoritative, the CLI does not apply anything for you.

Then confirm the send: `cf email-sending limits get` should flip from `null/null` to a real
quota, and a test send validates end-to-end. Check SPF/DKIM `pass` and `Return-Path`
(`bounces@cf-bounce.<domain>`) in the received message headers — that is what proves the
records are right, not the API's success response.

## Step 7 — "can this domain RECEIVE mail?" is not answered by the MX records

MX present + Routing `status: ready` does **not** mean mail is accepted for the address the
user has in mind. Two more facts are required, and both come from step 4's commands:

```bash
cf email-routing settings get        -z <zone-id>   # enabled / status: ready
cf email-routing rules list-account                  # account-level: real forwarding rules
cf email-routing rules catch-all get -z <zone-id>    # what happens to UNMATCHED addresses
```

Verdict matrix:

| Condition | Answer to "can it receive?" |
|---|---|
| Explicit rule `a@domain → forward [dest]` | **Yes, but only that address** |
| Catch-all `enabled: false` + `action: drop` | Unmatched addresses are **silently discarded** |
| Catch-all `enabled: true` | Any address on the domain is accepted |
| Routing `enabled: true` but no rule and catch-all off | MX answers, mail disappears |

So the honest answer to the user is shaped "**yes — but only `<address>`**; everything else is
dropped", not a bare "yes". `cf email-routing rules list` has no bare subcommand and exits with
a help block plus an error — use **`rules list-account`** for the real rules (it returns rules
for every zone in the account, so filter by `zone.name`).

## Read-only by default

The whole sequence above is read-only. Anything that creates or updates a record is a
**write** — present the finding and the proposed change, and get the user's explicit go-ahead
first. Report live-checked facts, never a confident-sounding guess: if a probe comes back
empty or errors, say so rather than inferring the configuration from partial output.

## Pitfalls

- **Concluding "domain not in this account" from page 1** — walk the pages first (step 1).
- **Reporting an auth/permission failure when the zone NAME was the problem** (step 2).
- **Treating routing records as proof of sending** (step 4) — the most common wrong verdict.
- **Assuming an enabled Routing setup accepts mail** — check the catch-all (step 4).
- **Quoting pricing/limits from memory** — this product is in beta and the numbers move;
  retrieve the docs pages and treat any figure as provisional.
- **Answering "can it receive?" from MX alone** — read the rules and the catch-all; a domain
  can be MX-ready and still drop nearly all mail (step 7).
- **Reading a forwarding rule's address from `name`** — the pattern is in
  `matchers[].value`; `name` is just the rule's label.
