# Province-level hazard screen — flood × earthquake (Thailand)

Use when the question changes scale: not "is this project/plot safe" but
**"จังหวัดไหนปลอดภัยจากทั้งน้ำท่วมและแผ่นดินไหว" / "ย้ายไปอยู่ไหนแล้วสบายใจ"**.

## Step order

1. **Answer the premise before the list.** No province is 100% safe on either axis — say it,
   then give the low-risk shortlist. Two official statements back this:
   - กรมทรัพยากรธรณี: 16 กลุ่มรอยเลื่อนมีพลัง cross 23 จังหวัด, and **not being on a fault ≠ safe**
     (far-field shaking reaches fault-free provinces; Samut Prakan felt the 2025 Myanmar quake).
   - ปภ. + สทนช.: over 2020–2024 **every** province in Thailand flooded at least once
     (flash flood, river overflow, or urban ponding).
2. **Screen out the fault provinces** (list below) → fails the quake axis.
3. **Screen in the low-flood provinces** (10-yr summary below) → passes the flood axis.
4. **Intersect**, then sanity-check with the provincial seat's elevation (opentopodata SRTM).
   A "low-flood province" whose capital sits near sea level is only safe in its hill districts.
5. **Close with the rule that dominates both charts:** engineering beats geography —
   มยผ.1301/1302 + pile design + soil test (quake) and fill ≥50 cm above the road + a real
   drainage outfall (flood). A well-built house anywhere beats a badly built house in a "safe" province.

## 16 active fault groups (กรมทรัพยากรธรณี) → provinces crossed

- **เหนือ:** แม่จัน (เชียงราย, เชียงใหม่) · แม่อิง (เชียงราย) · แม่ลาว (เชียงราย) · เวียงแหง (เชียงใหม่) ·
  แม่ทา (เชียงใหม่, ลำพูน, เชียงราย) · เถิน (ลำปาง, แพร่) · พะเยา (พะเยา, เชียงราย, ลำปาง) · ปัว (น่าน) ·
  อุตรดิตถ์ (อุตรดิตถ์)
- **กลาง/ตะวันตก:** เพชรบูรณ์ (เพชรบูรณ์, เลย) · แม่ฮ่องสอน (แม่ฮ่องสอน, ตาก) · เมย (ตาก, กำแพงเพชร) ·
  เจดีย์สามองค์ (กาญจนบุรี) · ศรีสวัสดิ์ (กาญจนบุรี, สุพรรณบุรี, อุทัยธานี, กำแพงเพชร)
- **ใต้:** ระนอง (ระนอง, ชุมพร, พังงา, ประจวบคีรีขันธ์) · คลองมะรุ่ย (กระบี่, พังงา, สุราษฎร์ธานี, ภูเก็ต)

→ Effectively fault-free: ภาคอีสาน (ยกเว้นเลย/เพชรบูรณ์) · ภาคตะวันออก · ที่ราบภาคกลางส่วนใหญ่ ·
กทม./ปริมณฑล · อ่าวไทยตอนบน (ยกเว้นประจวบคีรีขันธ์).

## Low-flood provinces (10-yr summary, ปภ. + สทนช.)

กาญจนบุรี · ราชบุรี · บุรีรัมย์ · สุรินทร์ · สุราษฎร์ธานี · กระบี่ · เพชรบูรณ์ · ตาก

Most fail the quake axis (กาญจนบุรี = เจดีย์สามองค์/ศรีสวัสดิ์ · ตาก = เมย/แม่ฮ่องสอน ·
เพชรบูรณ์ = เพชรบูรณ์ · สุราษฎร์ธานี/กระบี่ = คลองมะรุ่ย) → the survivors of BOTH axes are
**บุรีรัมย์ (~157 m) and สุรินทร์ (~147 m)**: no fault, low flood frequency, inland (no tsunami,
no storm surge), plateau ground.

Runner-ups (no fault, plateau, but expect Chi–Mun river ponding in places):
นครราชสีมา (~184 ม.) · ขอนแก่น · มหาสารคาม · ร้อยเอ็ด · ยโสธร.

## Traps that produced wrong answers before

- **"อยู่ในโผจังหวัดน้ำท่วมน้อย" ≠ พื้นที่สูง.** ราชบุรี is on the low-flood list but its capital
  measures ~8 m — only ที่สูง (สวนผึ้ง/บ้านคา) is genuinely low-risk. Always check the seat elevation.
- Provinces that look safe by flood history but sit on faults: กาญจนบุรี, ตาก, เพชรบูรณ์, กระบี่,
  สุราษฎร์ธานี. Never recommend these off the flood list alone.
- The viral "22 จังหวัดปลอดภัยจากแผ่นดินไหว" list is debunked (Thai PBS Verify) — do not reuse it.
- อยุธยา/ปทุมธานี/นครสวรรค์/สุพรรณบุรี (ที่ราบลุ่มเจ้าพระยา) flood every cycle; the Andaman coast adds
  tsunami exposure. Name these as "เลี่ยง" when she asks.
- **Chiang Rai (her home province) carries 5 faults** (แม่จัน/แม่อิง/แม่ลาว/แม่ทา/พะเยา). Say so plainly
  when comparing "ย้าย vs อยู่", then hand her the choice framed as safety-vs-family-distance.

## Verdict wording

Say **"ความเสี่ยงต่ำทั้ง 2 ด้าน"** — never "ปลอดภัย 100%". Pair the province answer with the
life trade-off (distance from her parents in Chiang Rai, the 2-rai Pong Pha plot) and give two
paths: move for lowest risk, or stay near family and cut risk at the house/plot level.

## Sources (re-check each time — lists change)

- `dmr.go.th` — active-fault map/data (16 groups), province/district lists.
- ของ ปภ. + สทนช. summaries of flood-declaration counts; `riskmap.disaster.go.th` (DDPM, per-ตำบล
  flood risk from the Tambon Smart Team survey) for the drill-down.
- `earthquake.tmd.go.th` — quake bulletins · `chiangrai.thaiwater.net` — per-province water levels
  (path pattern `<province>.thaiwater.net`).
- Thai PBS Verify / anti-fake-news centre for any viral province-safety list before repeating it.
