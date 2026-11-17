---
name: thai-land-house-planning
description: "Use for Thai land/plot planning (zoning, fences, fabric)."
version: 1.0.0
metadata:
  hermes:
    tags: [thai, land, plot, house, zoning, fence, maintenance]
    category: productivity
---

# Thai Land & House-Plot Planning

Help Patty plan her 2-rai plot at ต.โป่งผา หมู่ 8 อ.แม่สาย เชียงราย (405 m elev,
flood-safe, coords 20.35144670,99.87409731) — and any Thai land-development
question: unit conversions, zoning the plot, fence strategy, weed-barrier
budgets, and layouts that a solo mom can actually maintain.

## When to Use
- User asks about dividing/zoning a land plot (แบ่งโซน), fence (รั้ว) around the
  whole plot vs. just the house zone, or ground-cover fabric (ผ้าดำคลุมดิน)
- User plans the build area, garden, fruit trees, or "what goes where" on the land
- Any Thai land unit or budget question (ไร่ / ตร.วา / ตร.ม., fence/landscape costs)
- Funding the purchase: how much is still missing, whether to sell gold/land, cash-only vs
  ผ่อนดาวน์ vs mortgage, proving source of funds (AML/KYC), and the gift / crypto-sale tax
  position → `references/purchase-funding-and-source-of-funds.md`

## Unit Conversions (memorize — never guess)
- 1 ไร่ = 400 ตร.วา = 1,600 ตร.ม.  → 2 ไร่ = 3,200 ตร.ม.
- 1 ตร.วา (square wah) = 4 ตร.ม.  → 200 ตร.วา = 800 ตร.ม.
- Plot assumed 80 × 40 m for 2 rai unless told otherwise.

## Budget References (2026 Thai market, label as estimates)
- **ผ้าดำคลุมดิน (weed barrier)**: roll 2×100 m = 200 ตร.ม./roll.
  PP 70 gsm ~3–5 บาท/ม² (lasts 2–3 yr) · HDPE 100 gsm ~5–8 บาท/ม² (3–5 yr) ·
  cheap LDPE film ~1–2 บาท/ม² (6–12 mo only — avoid for permanent).
  Add pins/pegs + edge-burying ~1,000–3,000 บาท.
  Full 2 rai ≈ 16 rolls ≈ 12,000–25,000 บาท — almost never worth it.
  House zone only (500–600 ตร.ม.) ≈ 3 rolls ≈ 4,000–6,000 บาท.
- **Fence**: wire mesh + posts around 2 rai (~240 m) ≈ 50,000–80,000 บาท;
  concrete-base half-solid fence around house zone (~120 m) ≈ 120,000–180,000 บาท.
- **Solo-owner annual upkeep** (after build): ~6,700 บาท/yr ≈ 560 บาท/เดือน
  (mow Zone B 4×/yr @ ~800, trim Zone C 1×/yr ~1,500, water/electric ~2,000).

## Zoning pattern for a solo owner (the A/B/C rule)
Rule: **ยิ่งใกล้บ้าน ยิ่งหิน+ผ้าดำ (งาน 0) · ยิ่งไกล ยิ่งปล่อยธรรมชาติ (งานปีละ 1–4 ครั้ง)**
- **Zone A (house + front garden, ~800 ตร.ม. / 200 ตร.วา)**: house + parking +
  fountain + black-fabric-and-gravel everywhere, no lawn → 0 weekly work.
  Main gate faces SOUTH (Patty's Feng Shui: front door south; no back door;
  stove NW). Solid half-fence + CCTV + solar sensor lights + guard dog.
  Avoid ponds/fountains needing cleaning near a toddler.
- **Zone B (fruit orchard, ~1,000–1,200 ตร.ม.)**: กล้วย/มะม่วง/มะพร้าว/ขนุน —
  no watering needed (rain-fed), tilled + legume cover crop instead of fabric;
  hire mowing 4×/yr. Fruit = food + content for the FB page.
- **Zone C (natural back forest, ~1,000–1,200 ตร.ม.)**: leave existing trees,
  add shade trees; don't enter = don't maintain; hire clearing 1×/yr.
  Reserve space here for parents' house (flood-refuge plan from ต.เกาะช้าง 2024).

## Layout rules (from drawing the plan, 2026-08-25)
- Diagram column (left ~40%) and legend/info column (right ~60%) need a clear
  gutter — long headers placed above the diagram column collide with the drawing.
- Leave bottom padding (footer at H-28, not H-10) or text gets clipped.
- Zone labels go ABOVE boundary lines, not inside the area.
- **Verify the rendered PNG with vision_analyze before sending** — Thai tofu,
  text overlap, and clipped edges all pass code-review but fail visually.
- Reusable render script: `scripts/draw_land_plan.py` (Pillow, dark theme,
  Thai font via NotoSansThai — run with PYTHONPATH=/opt/data/pylibs or the
  profile venv). It embeds the zone plan + cost side-panel for Patty's plot.

## Pitfalls
- Don't propose covering ALL 2 rai with fabric — 20K+ baht and looks like a
  black field; cover only the developed zone, mow/hire the rest.
- Cheap (non-UV) fabric rots in Thai sun in ~1 yr; always spec HDPE 100 gsm +
  gravel/wood-chip top layer + buried edges.
- Verify the current date before resolving bare dates like "วันที่ 31" — the
  server runs UTC and the month isn't implied (see reminder-scheduling-cron).
- During construction phase, hiring mowing (~1,000 บาท/เดือน) beats any
  permanent ground cover until the house is built.

## Support Files
- `scripts/draw_land_plan.py` — proven Pillow renderer for Patty's 2-rai zone plan (Thai text + scale bar + cost panel).
- `references/project-house-comparison.md` — comparing Thai project houses vs self-build: data sources, the numeric sales-office questions that decide flood/quake safety, and the Chiang Rai contender table.
- `references/purchase-funding-and-source-of-funds.md` — paying for the house: budget math that must be re-run on every constraint change, the gold/land/mortgage decision table, the 5-level source-of-funds doc set (and why the donor's broker history is never required), Thai gift/crypto tax and fee-measure rules, and how to receive a >5M THB lump sum without tripping AML.
