---
name: thai-home-land-planning
description: "Thai land+home plans: zones, fences, irrigation."
version: 1.0.0
platforms: [linux]
---

# Thai Home & Land Planning (rural plot, low-maintenance for solo owner)

Recurring class for Patty (Pong Pha, Mae Sai, Chiang Rai — 2 rai plot, building
a neoclassical 2-storey home, budget 2.5–5M THB). Also applies to any rural
Thai land-development question: how to divide the land, fence it, stop grass,
water the garden, place outbuildings.

## Key math (double-check every time)
- 1 ไร่ (rai) = 1,600 m² → 2 rai = **3,200 m²**
- 1 ตารางวา (tarang wah) = 4 m² → 200 ตารางวา = **800 m²**
- Plot approx 80 × 40 m for 2 rai (adjust to actual chanote shape)

## Zoning principle (the one rule that makes it "manageable alone")
> **ยิ่งใกล้บ้านยิ่งต้องดูแลน้อย (หิน/ผ้าดำ/รั้วดี) — ยิ่งไกลยิ่งปล่อยธรรมชาติ**
(Closer to house = hardscape + zero-mow; farther = leave natural, 1–2 visits/yr)

Standard 3-zone template for 2 rai:
| Zone | Use | Size | Care load |
|---|---|---|---|
| A (south, house side) | house + garden + parking | ~800 m² (200 sq.wah) | 0/week: black fabric + gravel |
| B (middle) | fruit orchard (banana/mango/coconut/jackfruit) | ~1,200 m² | mow 4×/yr (~800 THB/visit) |
| C (back/north) | natural forest ("ป่ารกดีแล้ว") | ~1,200 m² | 1×/yr (hire brush-cutter) |
Total must equal plot size exactly — verify with arithmetic; users miscount.

Annual running cost target: ~6,700 THB/yr (~560 THB/month).

## Cost references (THB, 2026)
- **Black weed barrier (ผ้าดำคลุมดิน)**: PP woven 70 gsm ~3–5 THB/m² (2–3 yr);
  HDPE 100 gsm ~5–8 THB/m² (3–5 yr, UV-stabilised — recommend this).
  Standard roll 2×100 m = 200 m². 800 m² ≈ 4 rolls ≈ 3,000–8,000 THB
  + pins/edge-bury +1,000–3,000. Under-house footprint needs no fabric.
- **Fencing**: wire mesh around whole 2 rai ~50–80K; solid/half-solid
  concrete fence around house zone only (2 m high) + steel gate + CCTV.
  Rationale: protect boundary from cattle/trespassers cheaply, then secure
  the house zone properly. Two-layer fencing is the recommended answer when
  asked "fence all 2 rai or just the house area?".
- **Drip irrigation**: DIY (40–60 trees) 2,500–4,500 THB parts (PE pipe 16mm,
  drippers, fittings, timer 300–800, filter 200–400); DIY kit 1,500–3,000;
  hired 5,000–15,000. Prerequisite: water source (well/tank/pump) — check
  FIRST, it can cost 5–20K extra. DIY is fine for home scale; start Zone A,
  expand to B or hire for B.
- **Outbuilding (soundproof + gym annex)**: structure+roof 300–500K,
  acoustic insulation+door 80–150K, rubber floor 20–40K, 2 AC+elec 60–100K
  → ~500–800K. Build with the main house contract to save 20–30%.

## Outbuilding placement rules (noise-generating rooms)
- Separate building, NEVER attached to the house (bass/vibration + guest traffic).
- Place at the NW corner of Zone A: farthest from bedrooms (Snow sleeps 2F),
  farthest from street/neighbours, sound fires into the orchard (Zone B absorbs).
- Keep ≥15 m from house; plant bamboo/tree buffer along the west fence.
- Combine party/singing room + gym in ONE annex sharing a wall (saves 1
  acoustic wall). Include a small toilet.

## Drawing plans (PIL diagrams with Thai text)
When asked to draw the plan as an image (PIL, no browser):
- **Thai text renders as tofu (□) in DejaVu/FreeSans** — must use a Thai TTF.
  If `/opt/data/fonts/NotoSansThai.ttf` is missing:
  `curl -sL -o /opt/data/fonts/NotoSansThai.ttf "https://github.com/google/fonts/raw/main/ofl/notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf"`
  Put the Thai font FIRST in the FONT_PATHS list; verify with vision_analyze
  after rendering (tofu gives no error — only a visual check catches it).
- Always anchor with 2-char anchors ("mm"/"lm"); keep right-hand text column
  clear of the plan rectangle (RX ≥ 40px past X1) to avoid overlap.
- Deliver via `MEDIA:/path.png`.

## Project / plot risk check (น้ำท่วม + แผ่นดินไหว) — "บ้านโครงการนี้ปลอดภัยไหม / เทียบ 2 โครงการ"
Patty buys in housing projects as well as building on her own land, and asks whether a
project is safe from floods and earthquakes. **Measure the ground — do not summarise the
brochure.** Full command set: `references/project-risk-geo-check.md`.
1. **Get real coordinates.** Developer project pages and property portals embed them:
   regex `(?:lat|lng|latitude|longitude)["']?\s*[:=]\s*["']?(-?\d{1,2}\.\d{3,})`.
   Nominatim resolves Thai project names only sometimes; fall back to the developer page
   → portal (nayoo.co, home.co.th, thinkofliving) → the address's ตำบล centroid.
2. **Elevation** (`api.opentopodata.org/v1/srtm30m?locations=lat,lon`, free, no key) — use it
   for RELATIVE ranking between sites only. SRTM noise is ±5 m, so never turn one reading
   into "ต่ำกว่าระดับคลอง 3 ม.".
3. **Water distance** (Overpass `way(around:R,lat,lon)["waterway"]` + `["natural"="water"]`) —
   name the nearest creek and its distance. 400–1,200 m to a คลอง/ลำน้ำ means the plot sits
   in that creek's flood plain; keep the creek's name, local flood reporting is per-creek.
4. **Haversine between the competing projects.** Under ~1 km = same micro-location → flood and
   quake exposure are EQUAL; say that plainly, then move the decision to price, developer,
   contract, resale (that is what she actually has to choose on).
5. **Cross-check floods per ตำบล, not per city** — which ตำบล flooded in the big years, and did
   the highway in front of the project flood (and how deep). Chiang Rai floods most years.
   The same ตำบล can have one หมู่ under water and another dry — pair the news with steps 2–3.
6. **Quake:** count the province's active faults and past damaging events; within one city the
   real differentiator is construction standard (มยผ.1301/1302) + soil, NOT the plot.
7. **Old river channel = red flag.** If OSM shows a name like "ลำน้ำกกเก่า" next to the site,
   it is a former channel: alluvial soil, slow drainage, spreads when creeks top out.
8. **Her own land usually wins on flood.** City project land ≈ 391–394 m vs her Pong Pha plot
   ~405 m — say so, and pair it with the quake-side warning (Mae Sai/Pong Pha sits near faults).
9. **Sample a GRID, not a point, when the question is "จะท่วมไหม"** — centre + 8 compass points
   at ~300 m/~1 km + N–S/E–W transects every 500 m. Flat relief (5–10 m over 2 km) means
   standing-water risk, not flash flood; the lowest compass point is where the water leaves.
   Recipe and interpretation rules: §2b of `references/project-risk-geo-check.md`.

## Province-level screen ("ย้ายไปจังหวัดไหนแล้วปลอดภัย/สบายใจ")
The question sometimes jumps scale — from "this project" to "which province is safe from both
floods and earthquakes". Answer in this order: **state that no province is 100% safe on either
axis**, then intersect the two official lists (provinces crossed by the 16 active fault groups ×
low-flood provinces over 10 yrs) and sanity-check the provincial seat's elevation. Survivors of
both axes are บุรีรัมย์ and สุรินทร์. Full data, province lists and traps:
`references/thailand-hazard-screen-data.md`.

## Buying a project instead of self-building — supporting the decision
This is a standing decision, not an open question: self-build costs rise faster than her budget
(materials +5.8% YoY; her own estimate ≈4.97–6.81M against a 2.5–5M ceiling), while a project
locks the price and carries a contract + warranty. **Do not re-open the build-vs-buy debate** —
help her buy safely: put the true budget lines (fees, insurance, inspection, furniture, buffer)
and the flood / quake / legal checklists in front of her as a printable `.docx`. Recipes:
`references/project-home-purchase-playbook.md`.

## Where the money comes from — cash, a partner, or crypto (source of funds)
A **cash purchase** (no mortgage) moves the whole "prove where the money came from"
burden onto the buyer: no bank filters the payment, yet กรมที่ดิน and the receiving bank
do ask, and the AML threshold for cash-equivalent flows sits around **5M THB** — exactly
where a 2.5–5M house lands. Whenever the funding is a partner's transfers and/or crypto
sold for baht, run the funding workstream **in parallel with the project choice**: the
one-line money path, the gift ceiling (ม.42(17): **10M THB/yr from a non-spouse**, 20M
from a registered spouse — ask the marital status before quoting), the crypto cost-basis
records (ม.40(4)(ฌ), receipt-date price, ledger fields per the Revenue announcement), the
**upstream jurisdiction** when the donor's money started abroad (shares sold in one country,
banked in another currency, then turned into crypto — each hop needs its own evidence, and the
donor's tax residence decides which tax authority owns that layer), and
the deliverables (docx checklist · xlsx ledger · bilingual gift letter).
Full playbook, document lists and pitfalls: `references/property-purchase-funding-crypto.md`.

Three rules that decide whether the purchase actually happens:
- **Shrink the donor ask to two signed pages + a photo of his ID.** His historical broker/exchange
  records are the wall most buyers hit; a signed **donor's declaration of source of funds** naming
  his income sources (rental income from property he owns abroad, investments, salary) replaces
  them in practice. Never let "เอกสารจากแฟนหายาก" stall the plan — the buyer's own statements plus
  two signatures are the normal Tier-1 set.
- **Her own gold bars are the cleanest funding source she has** — a gold-shop receipt needs no
  donor chain at all. Unit math, the ~0.3% bar spread and the sell-only-the-shortfall rule are in
  the reference.
- **When the house she loves costs more than the cash on hand, engineer the payment, not the
  price:** developer ผ่อนดาวน์ (~0%, 12–24 months) buys the saving time, and the transfer date is
  negotiable at contract stage. Once she says the other models are not what she likes, the job is
  to fund THAT house — not to re-pitch a cheaper one.

When asked **"can I sell it all at once?"**, answer with mechanics rather than a rule: one
large inflow, exchange withdrawal limits, and USD-pegged FX/issuer risk against a baht-priced
purchase → sell a first tranche to open the paper trail, hold the rest until the price is known,
finish in 4–8 tranches before transfer day.

**Cashing out is its own workstream, and the exchange side decides whether the money arrives in
time.** Verify the account's real daily THB-withdrawal limit in the withdrawal screen (a loyalty /
"Privilege / ระดับ Gold / ปริมาณซื้อขายสะสม" screenshot proves nothing about limits), keep each
tranche under the ~5M THB reporting line *while telling the bank what it is for* (declared tranches
are ordinary risk management; splitting to avoid reporting is structuring), warn the receiving
bank's branch manager 2–3 weeks ahead, and re-read the state fee measure before budgeting the
transfer fee — while the measure runs it is **0.01%** (not 2%) on a home ≤7M THB, i.e. ~550 THB
instead of ~110,000 on a 5.5M house. Mechanics and the cost stack:
`references/property-purchase-funding-crypto.md`.

## Rebuilding a "รูปบ้าน/รูปสีที่เราเคยคุยกัน" after the cache is cleared
She asks for a render or colour card weeks after it was made, and profile image caches get
emptied — the artifact may be gone even though the work is not.
1. **Look for the generator before saying anything is lost.** `/opt/data/scripts/make_*.py` and
   `edit_house_v*.py` survive; re-run them (repair the input path to whatever image still exists).
   `house_debug_v*.jpg` in the same folder is often the last surviving recoloured render.
2. **Rebuild the durable artifact: a colour-spec card (PIL).** One row per surface — swatch block +
   Thai label + hex/RGB + the product/เบอร์สี reference and a usage note (กันน้ำ/กันเชื้อรา, ชายคา,
   มือจับทองเหลือง). Thai font `NotoSansThai.ttf`; verify by OCR/vision before sending.
3. **Ship a bundle, not a lone file:** card PNG + cleaned render + a regenerated `.docx` spec
   (patch out any `add_picture()` path pointing at a deleted cache file, embed the new card instead).
4. **Removing a baked-in debug overlay** (green/red box on an old render) needs no scipy: mask by
   channel dominance (`g > r+35 and g > b+35` for green), then iteratively replace masked pixels with
   the mean of non-masked 4-neighbours via `numpy.roll` for ~10–14 passes; confirm the leftover mask
   count is ~0 before sending.
5. Say what you rebuilt and from what ("cache ถูกล้าง → สร้างการ์ดสีใหม่จากสเปกที่ตกลงกัน") — never a
   bare "ไฟล์หายแล้ว", and never a fabricated "นี่คือไฟล์เดิม".

## Pitfalls
- Users miscount land area (e.g. "what's the leftover 400 m²?" when zones
  already sum exactly to the plot) — re-verify arithmetic kindly, show the
  sum table, don't invent a use for non-existent land.
- Solo-mom/low-time users: batch answers into tables + budgets; offer the
  next concrete artifact (checklist doc, shopping list, updated drawing).
- Feng shui matters to this user: front door south, no back door, stove NW —
  keep the south entrance axis clear when placing buildings.
- District-level flood news is NOT plot-level risk: the same ตำบล can be listed as flooded via
  one หมู่ while the project's หมู่ is dry. Always pair the headline with elevation + creek distance.
- SRTM elevation is ±5 m noisy — a single-site reading is not evidence of being below a creek level.
  Use it only to rank sites against each other.
- Overpass rate-limits (429/504). Alternate `overpass.kumi.systems` and `overpass-api.de` with a
  ~5–10 s sleep between sites; if one site silently returns "no river found" you will mis-rank it.
- Avoid claiming "ปลอดภัย" or "อันตราย" from one metric. Report elevation, creek distance, and the
  flooding history as separate lines, then give one bottom line.
- **"ในโผจังหวัดน้ำท่วมน้อย" ≠ พื้นที่สูง** — check the provincial seat's elevation before recommending
  a whole province (ราชบุรี's capital is ~8 m; only its hill districts are low-risk).
- Never write "ปลอดภัย 100%" for a province or plot: no-fault ≠ safe (far-field shaking reaches
  fault-free provinces) and no province was flood-free over 2020–2024. Frame as "ความเสี่ยงต่ำ".
- **Paying cash? The source-of-funds paperwork is part of the deliverable.** No bank filters a
  cash purchase, so the buyer carries the whole proof burden — say it plainly, and hand over the
  money-path + document set (see `references/property-purchase-funding-crypto.md`) instead of
  only the property advice.
- **Re-open a generated `.xlsx` with openpyxl and assert formula↔row alignment before sending.**
  Relative refs drift by one row (an average-rate cell pointing at the balance line, a gain
  subtracting the wrong row) and the totals only look slightly off — the user cannot spot it.
- **Never offer self-build as the paperwork-free option.** Building on her own land skips the
  developer's source-of-funds check but adds permits, engineer/มยผ. drawings, contractor
  management, 8–14 months and 20–30% cost overrun — and the bank trail of the money exists either
  way. State the trade-off once, then keep the project purchase as the plan.
- **Once she names the house she loves, stop pitching cheaper models.** The other units were
  already seen and rejected ("มันไม่ใช่แบบที่ฉันชอบ") — pivot to funding routes (gold, developer
  installments, land sale, loan) instead of re-opening the price.
- **An exchange's loyalty tier is not its KYC limit.** A "Privilege / ระดับ 3 Gold / ปริมาณซื้อขายสะสม"
  screen is a rewards tier and says nothing about how much can be cashed out per day; the answer lives
  in the THB-withdrawal screen ("วงเงินการถอนต่อวันคงเหลือ") or the web account-level page. Published
  limit figures drift between announcements — read the limit from the account, never quote an old
  number from a blog, and say plainly when a figure needs confirming.
- **Watermarked inspection photos: read the address in the overlay before accepting the photo as
  proof of the unit.** TimeMark-style stamps carry time + address + GPS, and the address can name a
  DIFFERENT sister project than the one booked (the unit's own show house / sales office sits in
  another โครงการ). Treat a mismatch as a question for the developer, not as a photo problem — and
  never let a stamped address stand in for the unit number in the contract.
- **The developer publishes the model's rooms/area but not its MATERIALS.** Roof type, insulation,
  window brand and thickness live only in the spec sheet / BOQ, so ask for it in writing (brand +
  model + thickness + insulation type and mm + warranty years) instead of inferring from photos: a
  distant aerial frame reads like metal standing-seam, a drone close-up can look the same, and
  neither survives a contract dispute. If the answer comes as "โปรโมชั่นไม่มีค่าธรรมเนียม", separate
  the three different things in the reply — waived fees, interest (never waived), and the
  prepayment penalty / promotional-rate clawback clause (separate, and the one that matters).
- **A burst of short voice notes is one question, not ten.** Transcribe the whole burst before
  answering, then reply once with everything consolidated; per-note replies bury the decision she
  is actually asking about.

## Support files
- `references/patty-pong-pha-plan.md` — Patty's specific numbers (zones, budgets, promises made).
- `references/project-risk-geo-check.md` — geocode → elevation → creek distance → news cross-check
  recipes, plus the project-comparison table and "questions for the developer" deliverable.
- `references/thailand-hazard-screen-data.md` — province-level flood × quake screen: the 16 fault
  groups by province, the low-flood province list, the cross-reference rule and its traps.
- `references/project-home-purchase-playbook.md` — buy-a-project run-through: true budget lines,
  the flood / earthquake / legal checklists, the 8 steps lot→handover, and the source contacts.
- `references/property-purchase-funding-crypto.md` — when the money arrives as crypto sold for
  baht or a partner's transfers: one-line money path, gift-tax ceilings, crypto cost-basis and
  ledger fields, the document set, the deliverables, and the pitfalls — plus the minimum donor
  ask (declaration instead of historical records), gold-bar liquidation, and the developer
  installment (ผ่อนดาวน์) route for a house priced above the cash on hand.
