# New-build handover inspection → defect tracker

Use when a Thai developer hands over a house/unit and the buyer has an inspector's report
(`ตรวจบ้านก่อนรับมอบโอน`) or asks "what do I do with this report?".

## Reading the report

Inspectors in this market deliver a tall PDF: a project/owner header block, a colour-symbol
legend, then a table of numbered items (`ลำดับที่`, `ตำแหน่ง ห้องหรือพื้นที่ตรวจสอบ`, photo,
`รายละเอียดงาน`) with a verdict per row.

- The PDF's **text layer is often glyph-mangled** (Thai combining marks split out of order, e.g.
  `ตรวจคณ ุ`, `ผนังปน ู`). It is still fully usable: read it for *which item numbers failed* and
  *which room*, and cross-check against the room sequence (ภายนอก → ห้องโถง → ห้องนั่งเล่น →
  ห้องครัว → ห้องน้ำ → ห้องนอน 1…4 → บันได → ชั้น 2) rather than trying to reconstruct prose.
- **Scanned-only pages**: render at 300 dpi and OCR with the Thai model
  (`tesseract img stdout -l eng+tha --psm 3`). OCR of a 64-hex TxID is never trustworthy; leave it
  blank and ask for a copy instead.
- Item numbering is the shared vocabulary with the contractor — quote `ลำดับที่ 59`, not "the
  bathroom ceiling".
- **Check the round number in the body, not the filename.** The body header says
  `ตรวจสอบมาตรฐานงานก่อสร้าง ครั้งที่ N`; a file named "ครั้งที่ 2" may contain a ครั้งที่ 1
  report. Ask for the latest round if they disagree.

## What "ผ่าน" looks like (do not re-litigate these)

Roof structure + drone roof-tile survey, septic tank / inspection sumps (`ถังแซท`, `บ่อพัก`),
full electrical check (outlets, water-heater circuit), and water-tightness tests in every bathroom.
Say these passed and move on — the buyer's anxiety is about the failing list.

## The failing list has a predictable shape

Almost everything that fails in a new-build is **finishing**, not structure:

| Bucket | Typical finding | What to demand |
|---|---|---|
| Ceiling | bathroom ceiling cracked, joint tape visible, board seams | re-tape, skim, repaint fully (report often specifies the coat count) |
| Plaster | hairline cracks in skim coat, uneven texture, topcoat not the real paint body | remove/level the real area, then repaint the whole surface |
| Paint | walls/ceilings uneven, patches, brush marks | redo with proper surface prep + tinting, whole-wall coverage |
| Sealant | silicone/grout not full-depth, smeared, not a straight line | strip and re-seal, then clean residue |
| Steel/metal | gate/railing colour uneven, sanding marks at joints | refinish and repaint the full run |
| Frames/doors | frames dirty, paint uneven, seals incomplete | clean frames, repaint, re-seal |
| Tiles | grout lines incomplete | re-grout, clean |

Group by bucket, not by room, when reporting to the user: 130 numbered items collapse into ~7
groups, and that is the only form a contractor will act on.

## Tracker deliverable

Build an `.xlsx` (never hand-edit an existing one; regenerate from a script) with:

- Sheet 1 `สรุปผลตรวจ` — inspector, owner, project, inspection date, round, item count, and four
  verdict lines (ผ่าน / เร่งด่วนมาก / งานเก็บผิว / เงื่อนไขในรายงาน).
- Sheet 2 `รายการตามแก้` — columns `หมวด | ลำดับในรายงาน | ปัญหา | สิ่งที่ต้องให้แก้/ขอ |
  ความเร่งด่วน | สถานะแก้แล้ว ☐ | วันที่แก้ | ตรวจซ้ำผ่าน`. Colour the urgency cell
  (red = ด่วนมาก, amber = ด่วน/ปานกลาง). Leave the status columns empty for the contractor to tick.

## Re-inspection rules to state out loud

- Nothing is "fixed" on the strength of a chat message: **re-inspect the exact item numbers**
  before signing the transfer, and photograph before/after each one.
- Ask whether the SPA holds a retention amount; if it does, do not release it before the re-check.
- Flag what the report does **not** cover so nobody assumes it did: ground-fill level versus flood
  level, site drainage and outfall, roof material brand/thickness, insulation under the roof, and
  (for a unit in a live site) how many months of construction continue next door.
- Name the resulting risk in flood terms rather than as a pass/fail: a flat, low-relief plot is
  protected by drainage design, not by elevation, and "no water stains yet" only means one wet
  season so far.
