# Asset inventory, Thai title deeds, and what may be disclosed

Use when the buyer lists assets for a loan file (land, condo certificates, savings lottery, gold,
crypto) or sends photographs of title documents to be read.

## Build one asset table, then split it by disclosure

One workbook, two sheets:

1. `ตารางที่ดิน` — one row per plot: deed no. · ไร่ · งาน · ตร.ว. · ตำบล · อำเภอ · จังหวัด ·
   registered owner (confirm) · encumbrances · evidence on hand. Leave unfilled cells yellow so the
   user can complete them from the deed; mark anything you read but are unsure of in orange with
   "ต้องยืนยัน".
2. `ทรัพย์สินรวม` (net worth) — one row per asset: type · detail · value · which document proves it ·
   **used in the bank file (Y/N)**.

Three disclosure tiers, decided with the user, not for them:

- **Disclose** — bank statements/e-statements, savings-lottery certificates in her own name, the
  condo ownership certificate, land titles in her own name, SPA/booking and payment receipts.
- **Keep private** — crypto holdings, gold, anything the user calls her secret savings. When she
  says keep Bitcoin private, remove it from every plan and stop raising it; a bank file built only
  from statement-backed assets is complete, and pushing disclosure after that is pressure, not advice.
- **Family land in someone else's name** — mention as background at most; it cannot be collateral.
- Also drop assets that are underwater (unrealised crypto/gold losses) from the plan rather than
  proposing a sale: liquidating a loss to fund a file that is already funded is a real cost for no gain.

## Thai chanote: the front page is the previous owner

- The `ให้แก่ <name>` line on the front is the **previous** transfer record. The current registered
  owner is entered on the back (ด้านหลัง) or a later page. OCR of the front page therefore returns a
  former owner — do not report the land as someone else's on that basis; ask the user once and expect
  "ชื่อฉันอยู่ด้านหลัง".
- Handwritten figures in the area boxes (ไร่ / งาน / ตร.ว.) are usually unreadable at phone-photo
  resolution. Ask for the numbers instead of inferring them: a wrong area silently corrupts the
  valuation and the net-worth total.
- Capture per plot: deed no., land no., survey sheet (เลขระวาง / หน้าสำรวจ), area, ตำบล/อำเภอ/จังหวัด,
  issue date, owner (front/back confirmed), encumbrances (จำนอง / ภาระจำยอม / ค้ำประกัน), and whether
  it is a full title (น.ส.4) or a lesser claim (น.ส.3ก, ส.ป.ก.).
- Conversions: 1 ไร่ = 4 งาน = 400 ตร.ว. = 1,600 m²; 1 งาน = 100 ตร.ว. = 400 m².
- Rural plots appraise well below their purchase price (commonly 20–40% under market, and the
  land-office price is a third figure again). Never value them from the purchase price, and do not
  lead with rural land as collateral when an in-town condo or the house being bought is available —
  use land as depth in the net-worth picture, not as the security.

## Condo ownership certificate (หนังสือกรรมสิทธิ์ห้องชุด)

States the project name, juristic person, the unit's **usable area in m²**, total building land area
and share value. Read the area off the certificate's own `เนื้อที่ … ตารางเมตร` line, then
cross-check it against the **project's published room-type range** for that bedroom count (e.g.
2-bed 72–77 m²). A number outside that range means you read the wrong field — not that this unit is
exceptional.

Numbers printed inside the parcel/plot diagram are **land segments, never the unit**. A diagram
showing `67.22` and `7.35` m² is a plot split; the unit's usable area was neither — it was **74.57 m²**
(67.22 + 7.35) and matched the project's own 2-bed range. Do not announce a unit area taken from the
diagram and do not announce one below the smallest room type for that bedroom count: both mistakes
shrink the appraisal, and therefore the lendable amount and every number built on it. Have the user
read the area line and confirm it before any document quotes the figure.

Ask for the pages carrying proprietor name, unit/floor and area — the certification page alone proves
nothing.

## Savings lottery (สลากออมสิน) in a loan file

- In the holder's own name it is solid net-worth evidence. The slip photo is **not** evidence: ask
  the user to obtain a bank-issued certificate of holdings / statement (branch or the MyMo app).
- GSB lends up to ~95% of face value against its own slips (สินเชื่อชีวิตสุขสันต์); **other banks do
  not accept the slips as collateral** and count them only as assets. Say which of the two you mean.
- 2-year slips: check the maturity date. An expired slip left unredeemed or unrenewed can stop
  earning interest — one phone call to 1115 or the branch settles it.

## OCR pipeline for Thai official documents

Crop, upscale and contrast-stretch with ffmpeg, then tesseract — this works even when the active
interpreter cannot import PIL:

```
ffmpeg -y -i in.jpg -vf "crop=W:H:X:Y,scale=iw*3:ih*3,format=gray,eq=contrast=1.9" out.png
tesseract out.png - -l tha --psm 6        # psm 6 for lines, psm 7 for a single value
tesseract out.png - -l tha+eng --psm 6    # mixed Thai/English documents
```

- Printed fields read reliably: account numbers, project names, "ซื้ออาคารชุด …", engine/statement
  headings, amounts typed into certificates.
- Handwriting and watermarked or glare-hit pages do not. Two independent reads (vision and
  tesseract) that agree on the digits are usable; when they disagree, ask the user. Never state a
  handwritten amount, a passport number, or an owner name from a single read.
- A vision description is not a source either: it will happily produce a plausible subdistrict, area
  or holder name. Treat it as a hint and confirm every field that changes money or advice.
