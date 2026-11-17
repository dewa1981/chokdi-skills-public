---
name: flight-fare-search
description: "Use when asked for flight fares/tickets (cari tiket)."
version: 1.0.0
metadata:
  hermes:
    tags: [travel, flights, fares, browser, google-flights]
    category: productivity
---

# Flight Fare Search

One-off "find me a ticket from A to B on date D" lookups. Bang travels often
(BKK ↔ Chiang Rai/Mae Sai, Penang, Medan), so this class repeats.

## Step 0 — pin the dates FIRST (non-negotiable)

Run this in the CURRENT turn, every time:

```bash
export TZ=Asia/Jakarta; date '+%A, %d %B %Y · %H:%M WIB'
```

- Never compute "besok"/"tanggal 20"/"minggu depan" from a timestamp captured
  earlier in the session. A long session spans several days, so a stale "today"
  silently shifts every date you search.
- **Cross-check "today" with a SECOND independent read before you lock the dates**
  (`python3 -c "import datetime;print(datetime.datetime.now())"`, `date -u`, or the
  mtime of a file the scheduler just wrote under `/opt/data/cron/output/`). A single
  `date` read has come back days-to-weeks off mid-session, and the error only surfaced
  when the user pushed back — by then the whole search was priced on the wrong dates.
  Two agreeing reads cost seconds; a wrong search costs the answer its credibility.
  State the date you searched for in the reply so the user can catch a mismatch instantly.
- Restate the resolved dates in the reply ("Minggu 20 Sep", "Senin 21 Sep") so a
  wrong date is visible to Bang immediately instead of after the whole search.
- Bang reads dates closely — a wrong one costs the whole answer its credibility.

## Step 1 — fix the airport pair, not just the city

- **Bangkok has two airports**: DMK (Don Mueang) = low-cost (AirAsia, Lion) and
  BKK (Suvarnabhumi) = full-service. Short-haul ASEAN routes are usually DMK; a
  "Bangkok" search resolves to DMK for them, but SAY which airport the price
  belongs to.
- One-way vs round-trip changes the numbers outright, and the calendar read in
  round-trip mode prices 7-day trips. Default to **one-way** unless a return is
  asked for, and label which one you priced.

## Step 2 — the working retrieval path: browser + CDP on Google Flights

Static extraction cannot do this class of lookup (see the block table in step 3).
Fill the form with real input events:

1. `goto_url("https://www.google.com/travel/flights?hl=en&curr=THB")` then
   `wait_for_load()`.
2. Inputs are addressable by aria-label: `input[aria-label='Where from?']`,
   `input[aria-label='Where to? ']`, `input[aria-label='Departure']`. The labels
   CHANGE once a value is set ("Where from? Bangkok DMK") — re-dump
   `document.querySelectorAll('input')` after each step instead of reusing a
   selector that worked one step ago.
3. Focus an input by clicking it with a REAL mouse event at its centre:
   `el.getBoundingClientRect()` for x/y, then
   `cdp('Input.dispatchMouseEvent', type='mousePressed'|'mouseReleased', x=…, y=…)`.
   `fill_input` alone does not register on this React form.
4. `ctrl+A` (`Input.dispatchKeyEvent` keyDown/keyUp, `windowsVirtualKeyCode=65`,
   `modifiers=2`) then `cdp('Input.insertText', text="Don Mueang")`.
5. Click the airport in the suggestion list: gather
   `li[role=option],div[role=option]` and pick the entry whose text contains the
   airport name. That same list also carries trip-type options ("Round trip",
   "One way", "Economy") — matching on index 0 clicks a trip type and wastes a step.
6. Switch to **One way** before reading any price (click the text node).
7. The monthly calendar renders a **price per date** — that alone answers "which
   of these dates is cheapest". Read it before opening any result list.
8. To open one date's results: click the date cell whose `innerText` matches
   `/^20\s*฿/` (day number then price), click `Done`, then click `Search` with a
   real mouse event at its bounding rect. A plain JS `.click()` on Search leaves
   you on the calendar with no results.
9. Read `document.body.innerText` from `"Search results"` onward: carrier,
   departure/arrival, duration, stops, price — plus the insight line "prices are
   unlikely to drop below X", which is worth quoting to Bang.

## Step 3 — when the primary path is blocked

| Source | Behaviour from the server IP |
|---|---|
| Google Flights via `web_extract` / Jina Reader | landing page or "Loading results" — the form needs interaction |
| Kiwi.com | 403 denied |
| Skyscanner | bot captcha (also through Jina) |
| Trip.com search deep-link | "whaleguard block" |
| KAYAK via Jina | renders ~25%, results arrive after the snapshot |
| Trip.com **route pages** | render fine — good for schedules (carriers, flight numbers, block times), NOT for dated fares |

Split the job by data type: **schedules** → route/option pages read statically;
**dated fares** → the browser form-fill in step 2. Don't re-try an OTA that already
refused — go straight to the browser path.

## Step 4 — report shape Bang expects

Short, plain text (LINE renders no markdown). Per date: clock times → carrier →
duration/nonstop → price; flag the cheapest; then ONE recommendation line; then
the caveats (which airport, one-way or return). Finish with the Google Flights link
so he can book. State the currency that was displayed instead of silently
converting — prices come back in the account's currency, not Bang's.

## Related

- Watching one route for a price drop over days is a different job:
  `product-price-monitor` (cron tick, state file, alert on threshold).
- Trip admin around the same journeys: `thai-immigration-admin`.
