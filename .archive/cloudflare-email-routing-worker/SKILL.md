---
name: cloudflare-email-routing-worker
description: "Use when routing email to Telegram via Cloudflare Workers."
version: 1.0.0
author: Hermes
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Cloudflare, Email Routing, Workers, Telegram, email, notifications]
    related_skills: [gmail-alert-monitor, cloudflare-workers-api]
---

# Cloudflare Email Routing → Worker → Telegram

Build a Gmail-free email-to-Telegram notification pipeline: a domain on Cloudflare
Email Routing catches ALL inbound email and hands it to an Email Worker, which
parses the MIME body and posts a clean notification to a Telegram bot.

Working example deployed for Coco/Bang: domain `banknotif.com` (account
cintasahabat9988@gmail.com), worker `shrill-snowflake-8c85`, bot
@Banknotif99_bot. Chosen over Gmail-API polling (see `gmail-alert-monitor`)
because the user's main Gmail must NEVER be touched (ban risk = all bank
transactions die).

## Architecture

```
Bank email → domain (MX = Cloudflare Email Routing)
  → catch-all routing rule → Email Worker (export default { async email() })
  → parse MIME body → POST api.telegram.org/sendMessage → bot
```

## Steps

1. **Add domain** in Cloudflare (Buy/Add Site). Note the Account ID + Zone ID
   from the dashboard URL — `dash.cloudflare.com/<ACC>/email-service/routing/<ZONE>/...`
2. **Onboard Email Routing**: Build → Email Service → Email Routing →
   "+ Onboard Domain" → pick zone → Continue → "Verify DNS records" →
   **Activate**. Cloudflare auto-adds 3 MX + DKIM TXT + SPF TXT. DNS propagates
   ±5-10 min; status flips to Enabled / DNS Locked.
3. **Create Worker**: Compute → Workers & Pages → Create → "Start with Hello World!"
   → deploy → rename later if desired. Record the worker name + workers.dev URL.
4. **Set env vars** (Settings → Variables): `TELEGRAM_TOKEN` as **Secret**,
   `TELEGRAM_ID` as plain Text. Save/Deploy.
5. **Routing rule**: Email Routing → banknotif.com → Routing rules → edit the
   **Catch-all** row → Action = **Send to a Worker** → pick worker → Save →
   toggle ON. (Or "+ Create routing rule" with pattern `*` @ domain.)
6. **Worker code**: paste the template (see `templates/mail2telegram_worker.js`),
   Deploy. Test by emailing `test@domain` from any inbox — notification arrives
   in the bot within ~1 min.

## Pitfalls

- **"No fetch handler!" in the preview pane is NORMAL** for email-only workers
  (no `fetch()` handler, only `email()`). Ignore it; the worker works fine.
- **`message.raw` is the FULL raw MIME including headers** (Received, ARC,
  SPF, DKIM). Naive HTML-stripping floods the notification with header spam.
  MUST split headers/body at the first `\r\n\r\n`, handle multipart boundaries,
  and decode base64 / quoted-printable — see `references/email-worker-mime-parsing.md`.
- **`EmailMessage` must be imported**: `import { EmailMessage } from "cloudflare:email";`
  at the top of the file. A `typeof EmailMessage !== 'undefined'` guard silently
  SKIPS the reply — the guard hides the missing import instead of surfacing it.
- **`message.reply()` requirements** (from CF docs): incoming email must have
  valid DMARC, reply recipient must equal incoming sender, outgoing sender
  domain must equal the receiving domain, only one reply per event.
- **Email-only worker file delivered as .txt, not .js**: Windows Script Host
  executes downloaded `.js` files → scary "JavaScript compilation error" dialog.
  A `.txt` opens in Notepad for copy-paste.
- **Long code in a Telegram message gets truncated** — deliver code as a
  MEDIA file attachment instead of pasting in chat.
- **Inbound Email Routing is UNLIMITED on the free plan** (the "100/day"
  figure floating around is the OUTBOUND/Email-Sending quota, which this
  pipeline never uses). 100+ aliases/accounts is fine.

## Files

- `templates/mail2telegram_worker.js` — known-good worker: MIME parse → clean
  text → Telegram, plus auto-reply hook for Addy.io verification emails.
- `references/email-worker-mime-parsing.md` — the header/body split recipe,
  multipart + base64 + quoted-printable decoding.
- `references/addy-io-recipient-verification.md` — Addy.io alias-forwarding
  verification quirks (unfamiliar domain → reply-based verification).

## Related

- `gmail-alert-monitor` — Gmail-API polling variant (when Gmail access is OK).
- `cloudflare-workers-api` — deploying workers via API instead of dashboard.
