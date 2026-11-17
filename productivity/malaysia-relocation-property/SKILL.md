---
name: malaysia-relocation-property
description: "Use when the user asks about Malaysia living or property."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [malaysia, property, visa, johor, relocation, thai]
---

# Malaysia relocation, property & travel ops

For Thai users making Malaysia decisions — entry, long stay, buying/renting, schooling, and checking developer paperwork. Thresholds and fees move: treat every number here as "last verified", and re-check the official source before money moves.

## When to Use

Load this skill when any of these appear:

- A Malaysia travel or entry question (MDAC, visa-free days, how long they can stay, onward ticket).
- A Malaysia property document arrives — an invoice, SPA, booking receipt, title or plot number — or a question about buying vs renting a house/condo in Johor or anywhere in Malaysia.
- The user asks "where is this project?", wants coordinates, or wants options (condo, kindergarten, school, hospital) near an address in Malaysia.
- A relocation idea: moving to Malaysia, long-staying there, or enrolling a child in a Malaysian school.

## Answer order (always)

1. Lead with the direct answer in one or two lines, in the user's language (Thai for Patty).
2. Then structured bullets — this user reads on Telegram: bullets and short labelled lines, **never tables**.
3. Quote money in **RM and THB together** (mark the conversion approximate).
4. Put any visa/legal constraint that can cost money or kill the deal **before** the shopping list — never as a closing footnote.
5. Volunteer the downside. This user asks "what's the catch?" when you don't, and rejects sugar-coating.

## Entry and short stay

- **MDAC (Malaysia Digital Arrival Card)**: mandatory for every traveller including infants, submitted online within **3 days before arrival**, free, only at `imigresen-online.imi.gov.my/mdac/main`. Tell the user to screenshot the confirmation — immigration may ask where there is no signal.
- Thai passport: **30 days visa-free**. Count from the **entry stamp date, not the flight date** — ask the user to read the stamp, then compute the last exit day and set reminders (mid-trip plus ~6 days before expiry).
- Travelling visa-free with **no onward/return ticket** is a real boarding risk — the airline can refuse check-in. Advise buying a cheap outward ticket as proof of onward travel.
- Overstay = daily fine and blacklist risk. Mention once; do not lecture.

## Renting vs buying as a non-citizen

- Johor purchase floors for non-citizens: **strata RM1,000,000 / landed RM2,000,000** — and published guides disagree (some quote RM1m for landed). **Never give one confident number**: state both floors and require written confirmation from the state land office before any booking fee.
- Extra non-citizen costs: **flat 8% stamp duty on residential** (from 1 Jan 2026), **Johor levy 3% or RM30,000 whichever is higher** (from 1 Jul 2025), state consent (Kebenaran Pindah Milik, s.433B National Land Code) before transfer can be registered, and processing measured in months. Financing typically 60–70% LTV.
- Off-limits at any price: Malay reserve land, Bumiputera-quota units, low/medium-low-cost housing. Medini (Iskandar Puteri) is the well-known strata exemption — verify per project and per unit.
- Most mid-market Johor stock sits **below** the foreign floor, so the practical answer for a Thai buyer is: **rent**, or **the Malaysian-citizen relative buys and rents it to them** on a documented tenancy. Never propose nominee or trust arrangements.
- Rental anchor, Bandar Seri Alam: 3-bed 840 sq ft serviced residence ≈ RM1,400–1,800/month; same stock sells at RM230,000–440,000.

## Verifying a developer progress invoice

Computer-generated and unsigned is NORMAL for Malaysian progress billing — that alone is not the red flag. What matters:

- Progress payments must go into the developer's **HDA (Housing Development Account)** held in the developer's registered name. An invoice showing **no bank details** is routine; obtain the account by phone from the developer's office and confirm the account name matches the company exactly.
- **Never pay into an individual, agent, or "representative" account.** State it as a hard rule, once, plainly.
- Cross-check: company registration number on the invoice vs the SPA; project **APDL** (Advertising Permit & Developer Licence) via KPKT; whether the lot is a **Bumi lot** (needs a release letter before a non-Bumi can buy); and that the stage billed matches the attached **architect's certificate**.
- Record the due date and set a payment reminder 3–5 days early — late payment accrues interest.

## Long stay with a small child — the realistic roadmap

- **A Malaysian Student Pass starts at age 3** (pre-school and above). Below that age there is no school-based long-stay route, so the parent of a toddler cannot settle on that basis yet. Say this early — it reframes the whole plan.
- The route that fits parent + small child: child enrols in a private/international school → child gets a **Student Pass** → the parent applies for a **Guardian Pass (Long-Term Social Visit Pass)**: one parent, 1 year renewable, **no work permitted**, proof of funds (3 months' bank statements), Malaysian/international health insurance, refundable bond (RM10,000 for many nationalities).
- Other long-stay bases: MM2H (large fixed deposit plus property requirement), Employment Pass (from 1 Jun 2026 EP I/II/III can sponsor dependants — Dependent Pass for spouse and children under 18, LTSVP for parents/adult children), or the user's own Student Pass. Siblings and other relatives give no route at all.
- Timelines matter more than prices: if the plan needs the child at age 3+, deliver a dated roadmap plus what to do meanwhile (30-day entries, or keeping the home base).

## Research workflow: condo and school near an anchor address

1. Nail the **anchor** first. "Near my sister" is ambiguous when she has a current home and a new house under construction 11 km away — ask which one, or show distances for both.
2. Take the project/address from the document the user sent (invoice, title, listing) and geocode it.
3. Compute distances and drive times yourself — recipe in `references/geocode-distance-workflow.md`.
4. Present each option with price band in RM + THB, tenure, built-up area, completion year, facilities, and **km + driving minutes to the anchor** — distance is what the user actually shops on.
5. State precision honestly: road-level geocoding is ±300–500 m. Give the Google Maps link and tell the user the exact lot is confirmed from the title/plot numbers (H.S.(D) / PTO) or the developer.
6. For schools, check the **age cut-off before recommending**: taska/childcare ≈ 0–4, tadika/kindergarten ≈ 3–6, international early years from ~3–4. For a toddler, list kindergartens within ~1 km of the anchor first — they matter more than the international schools.

## Pitfalls

- Do not quote a single foreign-buyer price floor for Johor landed property — the RM1m/RM2m conflict is exactly where deals go wrong; give both and demand written state confirmation.
- Label currency every time. Unexplained RM/THB switching confuses the user and hides the real cost.
- Never infer flood or seismic safety from a project or developer name — risk attaches to the specific lot (land-fill level, distance to the river/coast), not the brand.
- Don't open with a wall of legal caveats: one line of constraint, then the practical path.
- **A defect in a Malaysian rental is a property-law problem, not a visa problem** — never let a leak,
  mould or an unfinished repair justify overstaying; fix the stay legally and pursue the
  landlord/JMB separately (Form 28 in 7 days, then COB → Strata Management Tribunal):
  `references/malaysia-tenancy-defects.md`.

## References

- `references/johor-property-rules.md` — non-citizen thresholds, full fee stack, consent, exceptions, verification checklist, worked cost example.
- `references/malaysia-stay-and-schooling.md` — MDAC, visa-free limits, Student Pass, Guardian Pass/LTSVP document list, MM2H/EP routes, and the Bandar Seri Alam school landscape with fee bands.
- `references/geocode-distance-workflow.md` — photon + OSRM geocoding and drive-time recipe for "what is near X" research.
- `references/malaysia-tenancy-defects.md` — inter-floor leaks, mould and uninhabitable rentals: the Form 28
  timetable, who pays, the JMB charge-back right, COB → Strata Management Tribunal escalation, and what to
  claim from the landlord.
