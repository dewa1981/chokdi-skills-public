---
name: malaysia-johor-relocation
description: "Use when Patty asks about moving to Malaysia/Johor."
version: 1.0.0
author: Patty (Hermes agent)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [malaysia, johor, property, school, visa]
---

# Malaysia / Johor relocation research (Patty)

Context: Patty's older sister lives in Johor and is buying at **Redhill @ Seri Alam** (Bandar Seri Alam, Masai).
Patty is weighing a move to Johor vs staying in Chiang Rai (house plan at Pong Pha). Verified facts below — re-check prices/terms before quoting, they move.

## When to Use
- Patty asks where her sister's house/project is, or for its coordinates.
- She asks for condos or schools (kindergarten/international) near her sister in Johor.
- She asks about moving to or living in Malaysia, visas (Student/Guardian/MM2H), or working there.
- She sends a Malaysian property document (invoice, SPA, progress billing) for checking.
- She compares Malaysia with Chiang Rai on cost, schools or safety.

## Anchor location
- **Redhill @ Seri Alam** (marketing name "Alam Heights"): Jalan Tasek 45, Bandar Seri Alam, 81750 Masai, Johor. Developer **Redhill Frontier Sdn Bhd** (Reg 201601034368 / 1231397-U, No.85 Jalan Harmonium 35/1, Taman Desa Tebrau, 81100 JB, tel 07-351 7642). Freehold, 231 units on 23.87 acres, 2-storey terrace 20'x70'; sister's lot PTO 230736, H.S.(D) 596406, price RM798,000; completion ~Q4 2028.
- Coordinates ≈ **1.5009, 103.8807** (derived from OSM road data — ±300–500 m; confirm the actual lot with the developer / land office).
- Sister's current address: Taman Gaya, Ulu Tiram ≈ 1.5698, 103.8038 (11.5 km from Redhill).

## Driving distances from Redhill
Masai 4 km/9 min · Pasir Gudang 8 km/11 min · JB city 20 km/22 min · JB CIQ (Singapore) 25 km/25 min+customs · Senai Airport 39 km/36 min · Taman Gaya 18 km/18 min.

## Condos near Seri Alam
- **Midas @ Seri Alam** (Persiaran Seri Alam, Masai) — closest real data point, ~2.6 km from Redhill. Freehold, non-bumi, completed 2023, 35 floors, 1,609 units; 2BR 667 sqft ~RM330k, 3BR 840 sqft **RM330k–440k**, entry ~RM230k, auction reserve RM340k; rent **RM1,400–1,800/mo** partly furnished; pool, gym, playground, jogging track, minimart.
- Citrine Residenz (Seri Alam) — transacted ~RM545k. Anjung Seri (Persiaran Seri Alam) — listed ~RM560k. Opal Residenz Section 2 and Bandar Alam Masai (Era Universe) — newer launches.
- Amenities: Lotus's Seri Alam 1.3 km · Hospital Pasir Gudang (govt) 2.6 km · KPJ Pasir Gudang Specialist (private) 3.1 km.

## Schools for Snow (distance from Redhill)
- **Tadika Matahari – Seri Alam**, Jalan Tasek 52 — 0.3 km (kindergarten; best fit for a toddler). Little Caliphs Bandar Seri Alam.
- Japanese International School (Persiaran Seri Alam) 1.6 km · SMK Seri Alam 1 km.
- Repton International School (Seri Alam, ex-Excelsior), Jalan Purnama — 3 km, British curriculum, 20-acre campus. Some sources say the Masai campus rebranded to **Invictus International School** in 2024 (English National Curriculum/Cambridge, **RM25,500/yr Foundation → RM56,500/yr Y13**) — verify which entity operates now.
- UniWorld International School, Bandar Seri Alam business precinct · Foon Yew High School (Seri Alam) 3 km (Chinese).
- Chiang Rai comparison: **CRIS** (ages 3–18) ~THB 170,250–404,600/yr; **โรงเรียนอนุบาลเมืองเชียงราย EP (AMCR EP)** — MOE-approved English Program, far cheaper. Note: JB international-school fees land in the same range as CRIS, so "move for the language" is a weak economic argument.

## Visa reality (Malaysia, Thai citizen)
- Thai passport: 30 days visa-free; no long-stay route while Snow is under 3.
- **Student Pass is issued from age 3+** (pre-school and up) → Snow (1y7m in Sep 2026) cannot hold one yet.
- **Guardian Pass (LTSVP for one parent of a student)** — child must attend a private/international school and hold a Student Pass first; 1 year, renewable; **no work allowed**; needs proof of funds (bank statements) and a refundable bond (RM10,000 for many nationalities; confirm for Thai).
- Other paths: MM2H (large fixed deposit), Employment Pass, or studying herself.
- Practical implication: a real move targets when Snow turns 3; until then it is 30-day tourism + exits.

## Foreign-buyer rules (Johor) — decisive for Patty
- Non-citizen price floors: **strata RM1,000,000 · landed ~RM2,000,000** + mandatory written **state consent** (s.433B NLC). A RM400k–800k terrace or condo therefore **cannot be bought in a Thai citizen's own name**.
- Non-citizen transfer stamp duty **flat 8%** (residential, from 1 Jan 2026); Johor foreign levy **3%, min RM30,000**. Malay reserve / Bumi-quota units are closed to non-citizens.
- Workable routes: rent, or buy in a Malaysian relative's name and rent from them (clear written agreement).

## Progress-billing / invoice checks (developer payments)
- Progress invoices must be paid into the developer's **HDA (Housing Development Account)** in the developer's exact name — never an individual/agent account. Computer-generated invoices carry no signature, so phone the office to get the account number and keep the company-stamped receipt.
- Verify the project's **APDL** (KPKT/Teduh) and that the SSM registration number matches the SPA; check whether the unit is a Bumi lot (needs a release letter).
- Standard SPA progress stages are architect-certified; ask for the Architect's Certificate referenced in the covering letter.

## Method / tooling
- Geocode with `https://photon.komoot.io/api/?q=<place>&limit=5` (Nominatim 403, Overpass 406 from this host); driving distance/time with `https://router.project-osrm.org/route/v1/driving/lon,lat;lon,lat?overview=false`; haversine in Python for straight-line checks. Always state that coordinates are approximate and how to confirm the exact lot.
- Listing sites (mudah.my, propertyguru.com.my, iproperty.com.my, nuprop.my) do not render in the headless browser — mine prices from web_search snippets instead, and label them as asking prices to be confirmed with the agent.
- Deliver comparisons as a Thai .docx (python-docx via system python3) — Patty prefers Word docs over chat walls of text.
