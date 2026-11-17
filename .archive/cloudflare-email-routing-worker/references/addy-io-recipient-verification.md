# Addy.io Alias Forwarding — Recipient Verification Quirks

Addy.io (app.addy.io) is the user's alias/forwarding layer: every bank account
registers an alias like `nurulna348@alloh.addymail.com`, and Addy forwards
inbound mail to configured **Recipients** (real inboxes). In the bank-notif
architecture, the target recipient is `banknotif@banknotif.com` (a Cloudflare
Email Routing domain) so mail flows to the Telegram worker — the user's main
Gmail stays untouched.

## Two-step recipient flow (this is the trap)

1. **Recipients must EXIST & be VERIFIED before they can be attached to an
   alias.** Typing an unregistered address in the "Update Alias Recipients"
   modal shows "No results found" and refuses to save.
2. Order matters:
   - a) Menu **Recipients** → Add Recipient → `banknotif@banknotif.com` →
      submit.
   - b) Addy emails a verification to that address. For a **familiar** domain,
      the email has a clickable link. For an **unfamiliar** domain (fresh
      Cloudflare domain, never seen by Addy) the email says: *"reply to this
      email within 24 hours from the same address"* — there is NO link in
      email #1, and the link only arrives in a **second** email after the
      reply.
   - c) The worker auto-replies (see templates/mail2telegram_worker.js: detect
      `from` contains `verify.addy.io` + subject `/verify your email/i`, then
      `message.reply(new EmailMessage(to, from, rawMime))`). `EmailMessage`
      MUST be imported from `"cloudflare:email"` or the reply silently no-ops.
   - d) Click the verification link from the second email → recipient
      **Verified** (green badge in the Recipients table).
   - e) Now Aliases → edit alias → Recipients → the address appears in the
      picker → check it → Update. NEVER remove the old recipients (main-Gmail
      forwards) — only add.

## Other quirks

- "Resend email" re-sends the same reply-required email until the reply is
  received; re-run Resend after deploying the auto-reply worker.
- Reply must come from the SAME address the verification went to
  (`banknotif@banknotif.com`) — that's why a worker reply works and a manual
  reply from any other inbox does not.
- The user's standing concern: never expose the main Gmail (ban = all bank
  transactions die). Addy + Cloudflare worker keeps Gmail completely out of
  the path.
