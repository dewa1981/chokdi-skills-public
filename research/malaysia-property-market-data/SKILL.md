---
name: malaysia-property-market-data
description: Use when quoting Malaysia property transaction prices.
version: 1.0.0
author: chokdi_staging
license: proprietary
metadata:
  tags: [malaysia, property, brickz, napic, shoplot, valuation]
  related_skills: [kl-property-daily-report]
  hermes:
    tags: [malaysia, property, brickz, napic, shoplot, valuation]
    related_skills: [kl-property-daily-report]
---

# Malaysia Property Market Data (transacted vs asking)

## Rule zero
The client asks for "latest transactions". Malaysia's transacted data is filed **after stamp duty is paid**, so
"latest" = the newest filed month, typically **6–12 months behind today**. Always state the window
(e.g. "Apr 2025 – Mar 2026") and the latest filed date. Never present asking prices as transacted.

## Sources that work

| Need | Source | Notes |
|---|---|---|
| Transacted aggregates (free) | `brickz.my/transactions/<residential|commercial>/<state>/<town>/` | median psf, median price, P25/P75, tx count, latest filed date |
| Per-project transacted | `brickz.my/transactions/commercial/<state>/<town>/<project>/<landed|non-landed>/<type>/` | free tier = project-level median only |
| Per-unit detail | Brickz paid report / PropertyGuru DataSense | needs client subscription — ask for a CSV export, never their password |
| Official | NAPIC (napic.jpph.gov.my) | quarterly, lagged, detailed data paid |
| Asking prices | PropertyGuru, iProperty, listin.my, shoplotmalaysia.com | label clearly as ASKING |
| Historical narrative | theedgermalaysia.com articles | check the article date before quoting |

## Method
1. `web_extract` the Brickz town page; the clean markdown contains the Quick Facts block and a project
table (project, tenure/type, median psf, median price, filed transactions).
2. Pull the subject project row plus 3–4 neighbouring comparables, each in the window **its own page** reports.
3. Open the **project sub-page** (`…/transactions/commercial/<state>/<town>/<project>/landed/shoplot/`): the free
tier lists **5 dated rows** with address, tenure, built-up, price and psf — enough for a real transaction table.
Rows past 5 are masked; write "shows 5 of N rows" in the deliverable instead of implying it is complete.
4. Sanity-check psf: on landed commercial Brickz psf = **price ÷ land area**, not built-up
   (RM4.10M ÷ 1,650 sf land = 2,485 psf, while the same unit is ≈RM855 psf on 4,797 sf built-up). Quote the
   basis explicitly — a client comparing a land-basis psf against a built-up psf reads a 3x price gap that
   does not exist.
4. Add current asking prices from portals as a separate section.
5. Add a dated historical series (The Edge) for trend, labelled with its year.

## Snapshot — Kota Damansara (window Apr 2025 – Mar 2026, pulled Nov 2026)
- Kota Damansara commercial overall: 53 tx, 16 projects, median **RM2,638,000**, median psf **RM1,358**
  (P25 RM1,504,500 / P75 RM3,800,000).
- **Dataran Sunway shoplot: 11 tx, median RM4,100,000, median psf RM2,485**, last filed 12 Mar 2026
  (freehold + leasehold). The 2,485 psf is per **land** area (1,650 sf); on built-up (4,797 sf) it is ≈RM855.
  Filed free rows: 30 Apr 4.10M · 13 May 4.10M · 13 May 3.75M · 16 May 3.375M · 26 May 3.18M — a 29% spread
  inside one month, so position/floor/tenancy drive price, not a single psf number.
- The Strand: RM3.59M / 2,301 psf (12 tx). Seksyen 6 KD: RM3.3M / 1,378 psf. Damansara Promenade:
  RM1.8M / 1,093 psf. Sunway Giza: RM4.625M / 1,039 psf.
- Asking (same period): 3-storey 4,500 sf RM6.0M (~RM1,333 psf); 3,300 sf from RM8.0M (~RM2,424 psf);
  12,309 sf RM11.8M (~RM959 psf).
- Historical (The Edge, Oct 2022): 4,797 sf 3-storey average transacted 2017 RM3.0M → 2019 RM2.74M →
  2021 RM3.36M; 4-storey RM8–9M; ground-floor rent then RM3–5 psf.

## ROI matrix report (shoplot buy-and-hold)

Proven generator: `/opt/data/property_kl/nexis/make_roi_report.py` (WeasyPrint, 2 pages, same design system as the
rental proposals). Use when a client gives an asking price plus several rent scenarios and wants ROI.

- **Build the scenario table as rent matrix, not one number:** each row = ground floor rent, upper floors fixed,
total/month, gross/year, gross yield, net yield, payback. Clients negotiate the ground floor, so show the spread.
- **Net yield formula that survives scrutiny:** gross − 1 month vacancy − 5% management − fixed opex (assessment +
quit rent, insurance, repairs). Say which three items the opex covers; an unexplained "net" gets challenged.
- **Always add the acquisition stack:** stamp duty (1% ≤100k, 2% 100k–500k, 3% 500k–1m, 4% above 1m) and legal fees
under **SRO 2023** (1.25% of first RM500k + 1% of next RM7m, effective 15 Jul 2023, SST extra). Pre-2023 scale
(1%/0.8%/0.7%/0.6%) still appears in old calculators — using it understates fees by ~30% and the client's solicitor
will catch it.
- **Financing view is the honest part:** instalment on 80% at 4.5%/30y ÷ price ≈ 0.405% of price per month, so a ~4.4%
gross-yielding asset is negatively geared. Show 20/30/40% down rows with cash-in (down + duties) and cash-on-cash.
- **Price sensitivity beats argument:** recompute yield at asking and at 2–3 lower prices; convert the gap into ringgit
(each RM100k off ≈ +0.11% net yield) instead of saying "too expensive".
- **Label assumptions in the document** — built-up area is usually unknown on a shoplot listing, so state the assumed
sq ft on the page and put it on the verify list with tenure and existing tenancy.

## Pitfalls
- Brickz page is long; `web_extract` truncates the middle — raise `char_limit` or read the saved file.
- **The market name is not the filed project name.** Damansara Uptown is filed as **SS21 DAMANSARA UTAMA**
  under town **PETALING JAYA**, and a guessed URL silently redirects to `/search/?keyword=…`. When the
  extract comes back as a search page, use its rows to find the real project + town, then rebuild the URL.
- **Area pages do not share a window.** One town page can report 12 months (Apr 2025–Mar 2026) while another
  reports 14 (Aug 2025–Sep 2026), and project pages add their own dates. Quote the window per project; never
  present a cross-area table as if both rows came from the same period.
- **Small n collapses the quartiles.** With ~11 transactions P75 can equal the median (e.g. 3.65M / 4.10M / 4.10M) —
  do not call that "a tight range"; say n is small and the spread is indicative.
- psf across different built-ups/floors is not comparable; always pair psf with the unit size band **and** the
  area basis (land vs built-up).
- Free Brickz numbers are aggregate plus 5 sample rows. Do not invent the masked rows; offer to process the
  client's own CSV export instead.
- Don't quote rental yields without a rent sample (asking rent ≠ achieved rent).
