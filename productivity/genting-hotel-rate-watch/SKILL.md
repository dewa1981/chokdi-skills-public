---
name: genting-hotel-rate-watch
description: "Use when monitoring Genting hotel nightly rates to PDF."
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [hotel, genting, booking, pdf, cron, playwright]
---

# Genting Hotel Rate Watch (Booking.com → PDF → Telegram)

Daily 07:00 MYT PDF of the cheapest sellable nightly rate for First World Hotel,
Grand Ion Delemen and Wyndham Ion Majestic — 7 nights rolling, 2 adults / 1 room, MYR.

## Files
- `/opt/data/hotel_genting/fetch_prices.js` — Playwright-Core fetcher, 21 requests (3 hotels x 7 nights), writes `last_fetch.json`
- `/opt/data/hotel_genting/build_pdf.py` — WeasyPrint A4 dark report, reads `last_fetch.json` + `history.json`, writes `/opt/data/TMP/hotel-genting-<date>.pdf`
- `/opt/data/hotel_genting/history.json` — snapshot per report date, keyed by check-in date (drives the Δ vs previous run)
- `/root/.hermes/scripts/hotel_genting_cron.sh` — wrapper (fetch → pdf → sendDocument), one-per-day marker `.sent-<date>`
- Hermes cron job `Genting Hotel Rate Watch 07:00 MYT` (`0 7 * * *`, tz Asia/Kuala_Lumpur, `no-agent`), chat -1004490902172 thread 62

## The one trick that matters: Booking.com blocks curl, not a browser
- Plain `curl` to booking.com/hotel/... returns **HTTP 202 + 4 KB challenge page** from our IP. Playwright's normal `page.goto` on the *searchresults* page also lands on a challenge.
- Working recipe: launch Chromium, `page.goto('https://www.booking.com/index.en-gb.html')` once to set cookies, then run **every** rate request as an in-page `fetch(url, {credentials:'include'})` via `page.evaluate`. That returns the full server-rendered HTML (900 KB–2.6 MB) with `200`.
- One hotel page + `?checkin=&checkout=&group_adults=2&no_rooms=1&selected_currency=MYR` = one night's rates. ~4 s/request; 21 requests ≈ 90 s total. No pagination, no API key.

## Parsing
- Room table: `<table id="hprt-table">…</table>` — split on `<tr`, each row carries `<span class="prco-valign-middle-helper">MYR 99</span>`; `min()` of those = cheapest sellable rate.
- Room name in the same row: `hprt-roomtype-icon-link…>NAME<`. Keep it — it explains jumps like MYR 1,258 (only suites left that night).
- No table + "unavailable on our site / no availability" text = sold out for those dates → print `no availability`, **never** invent a number.
- Search-results pages (`searchresults.html`) are unreliable for a fixed hotel list: the visible card set changes per date (Ion Delemen dropped out on some dates, and Booking maps "Ion Delemen" to private units like "Genting SkyView ColdSuite AT Ion Delemen"). Pin the **hotel page slugs** instead:
  - `resorts-world-genting-first-world`
  - `grand-ion-delemen`  (the official hotel; slug `ion-delemen` is a different/legacy page without a room table)
  - `wyndham-ion-majestic-genting-highlands`

## Environment pitfalls
- `npx playwright` wants chromium-*1248* but the host cache only has *1234* → always pass `executablePath: '/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome'`, or the launch dies with "Executable doesn't exist".
- `playwright` python module is absent; use `npm i playwright-core` inside the project dir (no browser download) instead of depending on the volatile `~/.npm/_npx/...` cache.
- WeasyPrint needs a resolver: `/usr/bin/python3` has weasyprint but **no PIL**, `uv` venvs have PIL but no weasyprint. Loop over `/root/.hermes/installs/*/environments/*/venv/bin/python3` probing `import weasyprint, PIL` (same pattern as the KL property report).
- User_agent + `locale: en-MY` + `timezoneId: Asia/Kuala_Lumpur` keep the page in RM/English.
- WeasyPrint prints `@page` margin boxes on white unless you set `background` inside `@page`; dark reports need `@page { background:#0d0f12 }` or the page numbers are invisible.
- Flex header with a long right-hand stamp overflows the right margin — cap it (`max-width:62mm; flex:0 0 auto`).

## Verify a change
1. `node fetch_prices.js --days 7 --out /tmp/x.json` → expect `fetched 21/21 OK`.
2. Build the PDF, then render page 1 with pypdfium2 (`uv pip install --target <scratch>/qclibs pypdfium2`) and eyeball it — no cut-off edges, room labels not colliding.
3. `bash -n` the wrapper, run it once, then `tail` `/opt/data/hotel_genting/cron.log` for `sent … to -1004490902172/62`.
4. After a manual test send, **delete `.sent-<date>`** or the 07:00 run will treat the day as already delivered and skip.
