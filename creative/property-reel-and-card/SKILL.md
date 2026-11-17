---
name: property-reel-and-card
description: Use when making property listing reels, cards or proposals.
version: 1.0.0
author: chokdi_staging
license: proprietary
metadata:
  tags: [property, video, ffmpeg, namecard, pil, real-estate]
  related_skills: [still-to-motion-clip, banner-judi-chatgpt-plan, reel-editing-ffmpeg]
---

# Property Reel + Agent Name Card (proven build)

## When to use
- Client agent (e.g. Chloe, Malaysia) sends unit photos and wants a Facebook/TikTok reel.
- Request for a business/name card for a property agent.
- Request for a **rental proposal / listing one-pager** as PDF or Word (section below).
Talk-visibility rule: on client groups keep the topic to property only. Client-facing documents are
written in **English** (this client asks in English); internal chat with Bang stays Indonesian.

## Reel from stills (ffmpeg, ~5 min, no cost)
Canvas **1080x1920, 30fps**. Per photo: pre-scale `scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840`
then `zoompan=z='min(zoom+0.0012,1.18)':d=150:s=1080x1920` (reverse the zoom on alternate scenes).
Text band: two `drawbox` layers (black@0.28 + black@0.34) at the bottom, then `drawtext`
headline 74px bold + subline 46px gold (#E8C77A), both with `alpha='if(lt(t,0.5),t/0.5,1)'` fade-in.
Join scenes with `xfade=transition=fade:duration=0.6:offset=<n*(scene-0.6)>` (offset must accumulate
scene−xfade, else clips overlap). End card = `color=c=0x0B0B0F` + name/role/WhatsApp + a "SAMPLE" line.
Mux music with `-c:v copy -c:a aac -shortest -movflags +faststart`.

**Music:** no reliable free MP3 host from this server (FreePD returned no links). Synthesise a soft bed
with numpy (sine pad chords, slow attack/release, tanh soft-clip, stereo offset 12 ms, 1.2 s fades) —
royalty-free and controllable.

### Pitfalls that cost time
- **Check the photo actually matches its label.** A "kitchen" slot pulled a 1960s bathroom from
  Wikimedia; a mismatched label in a property reel destroys credibility. QC every frame with
  `vision_analyze` before sending, and drop a scene instead of mislabelling it.
- Wikimedia Commons search needs filtering: skip titles containing `.pdf`, `(IA `, `plans` — PDF page
  thumbnails come back as .jpg and slip through.
- Do not AI-generate interiors for real listings (beds/walls warp). AI only for hero/artwork + cards.

## Investment brief / market-comparison PDF (HTML+Tailwind → Gotenberg)

Different artefact from the rental proposal below: this one sells **the market**, not one unit — filed
transactions, KPI cards, comparison table. Numbers come from `malaysia-property-market-data`.

**Structure that passed review (2 pages A4):**
- p1: header (agent brand · prepared date · data source) → gold hairline → **4 KPI cards** (median price ·
  median psf · transaction count · window) → psf-basis footnote → unit profile bullets + positioning card →
  **filed sales table** → "before you make an offer" checklist (fills the lower third so the page is not
  half empty — an unfilled A4 looks unfinished).
- p2: comparison table (subject vs the competing area) → 3–4 comparables → "if you are selling / if you are
  buying" cards → **data notes** (window, sample size, 6–12 month lag, not a valuation).
- Every number must be a filed record; state `n` and the window next to the table. Asking prices are a
  separate, clearly-labelled section — never inside the transacted table.

**Build/QC:** Tailwind + Google Fonts (Playfair/Inter) via CDN, render with `gotenberg-html-pdf-ops`
(margins 0, page divs 210×297mm, `page-break-after`), then watermark with `stirling-pdf-ops`.
Starter file with both themes + all section slots: `templates/investment-brief-a4.html` — copy it, fill the
`{{PLACEHOLDER}}`s, add `class="light"` on `<body>` for the printable variant.
Screenshot the same HTML through Gotenberg to QC layout with `vision_analyze` before sending the PDF.

**Client-facing PDF rules (this client):**
- Always ship a **white-background variant** as the printable one and keep the dark-gold as the "premium"
  option — asking "background ga bisa putih?" means print is the real destination.
- **Watermark every client PDF** (WA number + trace token, light-safe colours). An unwatermarked proposal
  is a document the client can forward as their own.
- Localise on request: EN is the default; BM/中文 (and 廣東話 for spoken intros) are expected for Malaysian
  clients — keep one template and swap copy, don't rebuild the layout per language.

## Name card (PIL, print-ready)
Size **1050x600 px @300dpi = 3.5x2 in**. Fonts: download Playfair Display (name), Montserrat (labels),
Cormorant Garamond (monogram) from `github.com/google/fonts/raw/main/ofl/...` — DejaVu alone looks cheap.
Layout: name 104px, gold rule ~y=318 (**must sit clear of descenders**, 4px below baseline reads as an
underline), role 24px tracked, location 19px, monogram 380px at 20 alpha on the right.
Back: contact rows + QR (qrcode lib, `border=2`, white card with 16px pad) + "SCAN TO WHATSAPP".
Ivory variant: gold must be darkened to ~#8A6A1E or small labels vanish in print.
Add a left-to-right alpha scrim behind the contact column when the artwork is textured (marble veins sit
exactly where the phone number goes).
Export: PIL `save(pdf, save_all=True, append_images=[back], resolution=300)` = exact print size.

## Rental proposal document (PDF or Word)

Two pages maximum: **page 1 = the deal, page 2 = photos**. Build it from a generator script so the
text is re-renderable and the photo swap is a re-run, not a redesign.

1. **Take the client's own numbers verbatim** into a fact strip at the top — monthly rent, security
deposit (months), utility deposit, furnishing, transport link. Never re-derive or "improve" them.
2. **Compute the move-in total in code**, print it, and never hand-add: `rent*3 + utility + first_month`.
3. **Money table needs an explicit note.** A row "monthly rent RMx" plus a row "first month RMx" makes a
   reader sum to more than the stated total. Show recurring rent as *reference only* and state in one line
   that the total due at signing = deposits + first month.
4. **Connectivity claims come from the operator, not from listing ads.** Quote bridge length, station
   entrance, opening year and the line from the official page; listing text is not a source.
5. **Add a market-comparison line**: current asking band for comparable units at that project, plus what
   would justify a premium (built-up, floor, furnishing, parking bays). Label asking vs transacted.
6. **Photo page**: 2×3 grid. The generator scans `photos/` and embeds whatever is there, otherwise renders
   labelled placeholder cells. Drop-in swap, no layout work later.
7. **Deliver** the PDF (WeasyPrint) and/or the DOCX (python-docx), MEDIA path on its own line. Say which one.

Fact pack + reusable bullet copy (deposit norms, benchmark rents, pre-signing checklist):
`references/malaysia-rental-proposal-facts.md`.

### WeasyPrint PDF build (proven, 3 listings × EN/ZH)
Generator: `/opt/data/property_kl/nexis/make_pdf_proposals.py` — one `PROPS` entry per unit (rent, beds, sqm/sq ft,
car park, condition, link copy, why-bullets, market band); it emits EN + ZH from the same dict, so a new unit is a
one-line addition. `python3 make_pdf_proposals.py` → `/opt/data/property_kl/nexis/pdf/<slug>-<EN|ZH>.pdf`.

- **Real fonts, not DejaVu.** Playfair Display 700 + Montserrat 400/600 are TTF files in `nexis/fonts/`, registered
  with `@font-face { src: url('file:///…') }`. Download trick: `curl` the Google Fonts CSS **with the default curl UA**
  (a browser UA returns woff2, an ancient IE UA returns EOT — both unusable); the CSS then lists `.ttf` URLs.
- **Chinese needs a CJK family or you ship tofu.** This box has only `WenQuanYi Zen Hei` (no Noto Sans SC): declare
  `font-family: Montserrat, "WenQuanYi Zen Hei"` so Latin/numerals keep Montserrat and CJK falls through.
- **Palette that passes review:** ink `#191B20`, gold `#E8C77A` for rules/badges, `#96762F` for gold as *text* on white
  (bright gold on white is illegible), ivory panels `#FBF9F4`.
- **Fact strip labels must describe what the value is:** `CONDITION / Brand new` is fine, but `CONDITION / Fully
  furnished` reads wrong — use `FURNISHING`, and swap the fourth box to `CAR PARK / Not included` when that is the fact.
- **Fill page 1 or it looks unfinished.** Sections: hero (eyebrow, Playfair title, price block right, gold hairline)
  → fact strip → two columns (money table + connectivity diagram) → why-bullets → pre-signing checklist →
  "Viewing and next steps" (2 columns). Without the last block a 5-bullet page ends two-thirds down the sheet.
- **Diagram node needs the full name** — `name.split()[0]` renders "SUNWAY Level 1" instead of "Sunway Nexis Level 1".
- **Price with a qualifier wraps badly in a wide box:** `RM 3,700 (negotiable)` needs the space before the bracket and a
  smaller font in the fact box (`9.6pt` vs `10.5pt`) or "PER MONTH" collides with it.
- **Footnote text counts as shipped copy.** "The unit is tenanted/vacant as shown" is a contradiction a reviewer will
  catch — say "condition as shown in the photos" unless you know the actual status.

QC loop that works: render each PDF with `pypdfium2` (install with `uv pip install --python "$(command -v python3)"
--target <dir>` — the venv python has PIL and weasyprint, `/usr/bin/python3` has weasyprint but no PIL), then read the
PNG with `vision_analyze` asking specifically about font, overlap, fact-box labels and arithmetic. Every pass found a
real defect (wrong label, stray whitespace, contradictory line).

**Contact band with brand icons (client requirement).** A slim dark band under the hero carrying WhatsApp + WeChat
beats plain text. Logos: `curl https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{whatsapp,wechat}.svg` (CC0) → take the
single `<path d="…">` and inline it as `<svg viewBox="0 0 24 24">` inside a 19px circle badge (`#25D366` / `#07C160`).
WeasyPrint renders inline SVG fine — no image files needed. Rules learned:
- Number must be `font-size:12pt; font-weight:600; white-space:nowrap` — at 13pt with a long `+60 …` it wraps onto two
  lines and the divider drifts; the label stays small (6.9pt, gold, letter-spaced) so the number dominates.
- Do not append a "(placeholder)"/"(test)" tag next to the number: in the flex band it lands in the middle of the strip
  looking like a debug artifact. Mark dummies with obviously fake digits instead (`+60 12-000 0000`).
- **Adding the band costs ~1 block of height — page 1 then overflows into a third page.** Fix by moving the
  "Viewing and next steps" block to the bottom of page 2 (after Terms); do not simply shrink fonts until it fits, or the
  document ends up with two different type scales. Re-proof page count after ANY header addition: `len(pdfium.PdfDocument(f))`
  must stay 2 for every file, EN **and** ZH (EN copy is longer and overflows first).

### Proposal pitfalls
- **"Photos attached below" with no photo in the message.** Check the media cache for files newer than the
  message before believing either side; if nothing arrived, say it plainly in the first line of the reply
  and ship labelled placeholders. Do not substitute stock or another agent's listing photos and do not
  quietly deliver a text-only file the client did not ask for.
- **Official press photos of an MRT link bridge are opening-ceremony shots** — group photos, cake photos,
  atrium crowds. Unusable in a document. Replace with a labelled diagram row
  (`Station Entrance B → 80 m covered bridge → Development L1`) which reads cleaner anyway.
- **Valuation reality check before defending a rent.** If the quoted rent sits above the visible asking band,
  put the honest line in the document ("justified if larger / higher floor / two car parks") instead of
  writing copy that pretends the price is market rate.

## Env notes (staging)
- `python3` has no pip. Install packages with `uv pip install --python "$(command -v python3)" --target <dir>`
  and set `PYTHONPATH=<dir>:/opt/data/pylibs`. The interpreter that carries PIL + weasyprint is a venv one under
  `/root/.hermes/installs/*/environments/*/venv/bin/python3`; `/usr/bin/python3` has weasyprint but no PIL.
- **Wheels are ABI-specific**: a package installed for `/usr/bin/python3` (cp312) will not import in the 3.14
  venv. Install with the same interpreter you will run, or the import fails on the other one.
- ChatGPT Plan (openai-codex) generates **images only** — no video. Use it for banner/thumb/name-card art,
  ffmpeg for motion.
- **Marketing visuals must be AI-designed, not assembled from type.** Hand-typeset PIL cards were rejected
  outright ("jelek desainnya, suruh ChatGPT yang desain"). Route name cards, covers and posters through
  `banner-judi-chatgpt-plan` (short text on flat artwork renders with correct spelling; long strings and
  phone numbers do not — overlay those yourself). Keep PIL for print mechanics (crop to 3.5×2in, contact
  block, QR) on top of the AI artwork.

## Delivery
Send MP4 + card previews as MEDIA paths, plus an honest limits note: no auto-posting to
PropertyGuru/iProperty/Facebook (no account access, duplicate-listing rules), photos decide quality,
and documents are drafts for the agent/lawyer to review.
