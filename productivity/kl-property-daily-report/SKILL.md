---
name: kl-property-daily-report
description: "Use when building the KL property daily PDF report."
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [property, malaysia, pdf, cron, mudah]
---

# KL Property Daily (asking price + rent → PDF → Telegram)

Daily Kuala Lumpur property snapshot built from public listing asking prices
(mudah.my), rendered to a one-page A4-landscape PDF, delivered to Telegram at
08:00 Asia/Kuala_Lumpur (GMT+8).

## Files
- Generator: `/opt/data/property_kl/kl_property_daily.py`
  - `python3 kl_property_daily.py` — scrape + store snapshot + PDF
  - `python3 kl_property_daily.py --from-history [YYYY-MM-DD]` — re-render last
    (or given) snapshot without touching the network. Use this when only the
    layout/template changed.
- History: `/opt/data/property_kl/history.json` (one entry per MYT date; drives Δ1d / Δ7d)
- Wrapper: `/root/.hermes/scripts/kl_property_cron.sh` (resolves a python that can
  `import weasyprint, PIL`, builds, then sends `sendDocument` to chat
  `-1004490902172` thread `2`)
- Cron job: `KL Property Daily 08:00 MYT` (`0 8 * * *`, tz Asia/Kuala_Lumpur, `no_agent`)
- Output: `/opt/data/TMP/kl-property-<date>.pdf` + `.html` (same name)

## Source reality (do not promise more)
- `mudah.my` KL listing pages work with a browser UA + `Accept-Language: en-MY`:
  `https://www.mudah.my/kuala-lumpur/properties-for-sale?q=<kw>` and
  `.../properties-for-rent?q=<kw>`. Each page carries ~40 listings as embedded
  JSON: `"itemOffered":{..."name":"<title>"`, `"addressLocality"`,
  `"name":"Floor Size","value":"<sqft>"`, `"price":"RM <n>"`.
- **PropertyGuru, iProperty, Brickz return HTTP 403 from our IPs** — never build a
  pipeline on them.
- Official transacted (SPA/sold) prices are **quarterly NAPIC/JPPH** only. A daily
  "sold price" does not exist on the open web; label everything asking-price.

## Pitfalls learned
- **429 Too Many Requests** after ~15 rapid requests. Keep ≥3 s between fetches and
  back off 25 s once on 429; a 22-request run with 3 s pacing completes clean.
- `?page=2` / `?o=2` pagination returns no listing data — expand coverage by adding
  *keyword* queries per area instead of paging.
- Two keyword queries per area return overlapping ads → dedupe on
  `(title.lower(), price)` or medians get weighted by duplicates.
- Area keyword overlap silently corrupts comparisons: `Bangsar` query also returns
  "Bangsar South" stock (which is its own area) → keep an `AREA_EXCLUDE` list.
  A wrong exclusion shows up as both a tiny sample and a wild median (Bangsar n=11,
  median RM4.1M) — always eyeball `sale n` per area after editing keywords.
- Rent listings include single rooms; filtering titles on `room|bilik|hostel|roomstay`
  is what keeps the median rent at whole-unit level.
- Gross yield from median-rent ÷ median-price is fine; deriving it from the two
  median RM/sqft figures is NOT (the samples differ) and produces nonsense.
- Cheap legacy flats in an area (e.g. Kerinchi/PPR under "Bangsar South") can push
  area yield to 8%+: mention it rather than massaging the number.
- WeasyPrint path: `PYTHONPATH=/opt/data/pylibs` plus an interpreter that has `PIL`;
  `/usr/bin/python3` has weasyprint but **no PIL**, so probe imports before choosing.
- No `pdftoppm`/`gs`/`fitz` on this host. To eyeball a PDF: `uv pip install --python
  /usr/bin/python3 --target <scratch>/qc_libs pypdfium2`, then render with the venv
  python (it has PIL) and inspect the PNG.
- One-message-per-day guard: wrapper writes `property_kl/.sent-<date>`; re-running the
  job (or `hermes cron run`) regenerates but does not double-post. `FORCE=1` overrides.

## Verify a change
1. `python3 kl_property_daily.py --from-history` → check page count is 1 and render a PNG.
2. `bash -n` the wrapper, then run it once and read `property_kl/cron.log`.
3. `hermes cron run <job_id>` must print `Ran now: succeeded`; `hermes cron list` must
   show the next fire at 08:00 +08:00.
