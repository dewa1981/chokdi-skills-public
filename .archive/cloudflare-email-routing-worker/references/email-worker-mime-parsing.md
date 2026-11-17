# Email Worker MIME Parsing (Cloudflare)

`message.raw` is a ReadableStream of the **entire raw MIME message INCLUDING
headers** (Received, ARC, SPF, DKIM, Authentication-Results...). If you strip
HTML without splitting headers first, your Telegram notification is flooded
with header spam and the real body (e.g. a verification link) gets truncated
away. The v1 worker made exactly this mistake — output was pure headers.

## The recipe (proven in v4 template)

1. **Read stream → text**: collect chunks into Uint8Array, `TextDecoder().decode`.
2. **Split headers/body** at the FIRST `\r\n\r\n`:
   `headerBlock = raw.slice(0, sep)`, `bodyPart = raw.slice(sep + 4)`.
3. **Content-Type / boundary**: regex `content-type:\s*([^\r\n]+)` from header
   block, then `boundary="?([^";]+)"?` for multipart.
4. **Multipart**: split body on `--boundary`; for each part, split its own
   headers/body, pick the part whose Content-Type is `text/plain` (fallback
   `text/html`), decode per its Content-Transfer-Encoding.
5. **Decode**: `base64` → strip whitespace → `atob` → bytes → TextDecoder.
   `quoted-printable` → strip `=\r?\n` soft line breaks → `=HH` hex decode.
6. **HTML→text**: drop `<style>/<script>/<head>` blocks, convert `<br>` and
   closing `</p|div|tr|h1-6|li>` to `\n`, extract `<a href>` as ` [url] `,
   strip remaining tags, decode `&nbsp; &amp; &lt; &gt; &#39; &quot; &mdash;
   &ndash; &hellip;`, collapse whitespace, truncate to ~2500 chars.

## Verification-email trap

Addy.io's first "Verify Your Email Address" email looks like plain text but is
actually multipart — the plain part contains NO link, only "reply to this
email". Do not hunt for a link in email #1; the link arrives in a SECOND email
only after the worker replies.

## Notes

- Plain-text bodies (no `<` tag) skip HTML cleaning, just normalize newlines.
- Keep truncation AFTER cleaning so links survive in the first 2500 chars.
- Log worker failures with `console.log` and also ping Telegram so the user
  sees failures without opening the CF dashboard.
