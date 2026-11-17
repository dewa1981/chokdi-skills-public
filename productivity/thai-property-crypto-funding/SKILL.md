---
name: thai-property-crypto-funding
description: Use when crypto/gift funds buy Thai property.
version: 1.0.0
author: Patty (pattysnow448)
license: MIT
metadata:
  hermes:
    tags: [thailand, property, crypto, aml, tax, bank]
    related_skills: [thai-immigration-admin, xlsx, docx]
---

# Thai property purchase funded by crypto / foreign gift

## When to Use

- Cash (no-mortgage) purchase of Thai property funded by selling USDT/crypto and/or a gift
  from a non-spouse partner living abroad.
- A developer or bank suggests taking a **50% mortgage so the land-office transfer passes**
  (buyer shows no provable income and has a foreign partner) — see "When the land office is the
  risk" below before answering.
- A developer, bank, or land officer asks for source-of-funds documents, or the user asks
  who to hand documents to and when.
- Planning where and how to sell the crypto (exchange choice, rounds, limits, fees, records).
- Questions about the THB 5M threshold, the 10M gift exemption, crypto gains tax, or the
  0.01% transfer fee.

The job: move money from donor to developer along a path that reads clearly, with the
paperwork ready before anyone asks for it. The hard part is never the money — it is proving
a **single, readable money path** to the developer, bank, and land office.

## Core principle: one path, readable end to end

`donor -> exchange account in the BUYER's own name -> sold to THB -> buyer's bank account -> cashier's cheque / own-name transfer -> developer`

Every leg must exist in the buyer's own name. Use this single story, in the same words,
every time someone asks.

Hard bans (state these to the user, they prevent frozen accounts):

- never cash, never a third party's account, never an exchange in someone else's name
- no large P2P with strangers, never share OTP
- never split payments or sales to **hide** a total — selling in planned rounds is fine,
  hiding the aggregate is what turns a paperwork issue into an AML case. Always answer
  truthfully, including the total.
- the buyer must not post financial screenshots in public groups/pages

## When the rules bite (Thailand, 2026)

- **≥ THB 5,000,000** in one transaction / aggregate inflow: source-of-funds documents are expected.
- Since Jul 2026 the Bank of Thailand and the SEC specifically scrutinise **USDT / crypto
  inflows ≥ THB 5M** (grey-money crackdown) — keep each sale and each bank inflow clearly
  under 5M and prepare the trail anyway.
- Gift from a person who is **not** a legal spouse is income-tax exempt up to **THB 10M per
  tax year** (Revenue Code s.42(17)); spouses get 20M. Keep the year's total under the
  ceiling; if a further transfer would breach it, receive it in the next tax year.
- Gains on crypto sold through a licensed Thai exchange are s.40(4)(ฌ): gain = sale value
  − cost (value on the day each unit was received). Licensed exchanges withhold tax
  (commonly 15% of the gain) and issue the certificate. Loss = no tax, but the cost basis
  still must be recorded. Ask a Thai accountant once whether filing a combined PND.90 to
  reclaim the withheld 15% beats treating it as final.
- **Government fee measure (1 Jul 2569 – 30 Jun 2570, not 2027):** transfer registration drops
  from 2% to **0.01%** AND mortgage registration from 1% to 0.01%, for a Thai-national individual
  buyer, when price + appraised value ≤ THB 7M and the loan ≤ THB 7M, and only if transfer and
  mortgage are registered **in the same transaction** (a mortgage registered later pays the full
  1%). On a 5.5M home with a 2.75M loan: ~550 + ~275 THB instead of ~110,000 + ~27,500. Loan
  agreement stamp duty 0.1% of the loan (~2,750) still applies; discharge later costs ~50 THB per
  plot + 5 THB request. Always re-read the measure's window before budgeting — it has been
  extended year by year, so the end date in an older note may be stale.

## Document set (five tiers — build all of it, hand over only what is asked)

1. **Buyer's own** — national ID, bank statement showing the THB from exchange sales,
   exchange trade/withdrawal history (PDF), TxID of every crypto receipt.
2. **Donor** — Gift Letter stating amount + purpose, copy of the donor's ID/passport, and a
   **Donor's Declaration of Source of Funds** (1 page, TH+EN). That declaration is what
   replaces broker/trade statements the donor cannot retrieve — it removes almost all of the
   "my partner's documents are impossible" problem. Ask the donor for only three things:
   signature, ID photo, declaration.
3. **Donor's supporting evidence** — only if pressed: tax withholding slips / exchange
   history, tenancy agreements or rent statements for rental income, broker contract notes.
   Blockchain TxIDs can be re-printed from any explorer forever, so they never get lost.
4. **Buyer's declaration** — 1-page declaration of source of funds, TH+EN.
5. **If the bank pushes** — bank reference letter, exchange letter confirming KYC and sales.

Templates already built for Patty (reuse and re-fill, keep TH+EN pairs):
`/opt/data/คำชี้แจงที่มาของเงิน_ไทย-อังกฤษ.docx`,
`/opt/data/คำรับรองแหล่งที่มาของเงิน_ผู้ให้เงิน_ไทย-อังกฤษ.docx`,
`/opt/data/หนังสือให้เงินและคำขอเอกสาร_ไทย-อังกฤษ.docx`,
`/opt/data/เช็กลิสต์หลักฐานที่มาของเงิน_USDT_ซื้อบ้าน.docx`,
`/opt/data/คู่มือชี้แจงเงินก้อน150000USDT_ซื้อบ้าน.docx`,
`/opt/data/สารบัญแฟ้มเอกสาร_ที่มาของเงิน.docx` (folder cover sheet — put it on top),
`/opt/data/ตารางบันทึกUSDT_และงบซื้อบ้าน.xlsx`,
`/opt/data/ตารางทยอยขายBitkub_แผนซื้อบ้าน.xlsx`,
`/opt/data/แผนการเงินซื้อบ้าน_รายเดือน.xlsx`.
Generator scripts live in `/opt/data/scripts/_make_*.py` — copy the style from there
(Tahoma + python-docx for TH/EN docs, openpyxl with a yellow input block for sheets).
**Re-open every generated .docx/.xlsx before delivering it** and assert on the content: the key
identifiers must be present (TxIDs, amounts, dates) and the Thai text must contain **no stray CJK
characters** — `re.findall(r'[\u4e00-\u9fff]+', text)`. LLM-drafted Thai copy intermittently slips
in Chinese words (任何人, 下一步, 接近); one of those inside a source-of-funds document the user will
hand to a bank poisons trust in the whole file set, so scan and regenerate instead of shipping.
Run those generators with an interpreter that actually has `python-docx`/`openpyxl`: the
`python3` on PATH can be a Hermes profile venv holding neither the packages nor `pip`. Find a
working one first — `find / -maxdepth 7 -type d \( -name openpyxl -o -name docx \) -path
'*site-packages*'` — then invoke that venv's python explicitly. If the venv python cannot import
what the script needs, treat it as a wrong-interpreter problem, not a broken install.

**English one-pager for a foreign donor** — `/opt/data/GiftLetter_ภาษาอังกฤษ_ให้แฟนกรอก.docx`
(built by `/opt/data/scripts/_make_gift_letter_en.py`): page 1 how-to in Thai, page 2 the
English Gift Letter with fill-in blanks, page 3 the document checklist. Re-run the generator
instead of hand-editing the .docx. Rules baked in:
- Leave every name/ID/address blank. Never fill the donor's identity from circumstantial data
  (a booking passenger name, a surname inside the child's name, a chat nickname) — if the user
  names the donor, ask for the name **as printed in the passport** before writing it in.
- The letter must never say husband/spouse/คู่สมรส: the couple is unmarried, and that wording is
  what keeps the donation inside the THB 10M s.42(17) exemption. Use "partner" or "the father
  of my child".
- Ask the donor for exactly three things — signed letter, ID/passport image, signed donor
  declaration — and tell the user that count plainly when they ask "how many documents".
  Transfer proof (TxID/slip) and donor-side evidence are tier 2, requested only if pressed.
- When the user asks who some named person is and there is no record, say there is no record and
  ask. Do not infer identity or relationship from circumstantial data, and do not agree with a
  guess.

## Who asks for documents, and when

- **Developer / sales** — at booking and contract (real-estate businesses must do buyer
  KYC). This is the first place the folder is actually handed over.
- **Bank** — only when it asks. Most cases start as a verbal question on the phone;
  documents follow only if the amount or pattern looks unusual.
- **Land office** — at transfer, if the officer asks.
- **Revenue Department** — only on audit; a PND.90 filing does not attach these documents.
- **Exchange** — if it questions the origin of a large crypto deposit.

Calibrate expectations honestly: roughly 90% of cases need only ID + a one-page declaration;
~9% add bank statements or exchange history; ~1% wants the full folder. Preparing for the 1%
removes anxiety without overpromising.

Tell the user to hand over **only what is requested** and never to send ID copies or
financial documents to anyone who contacts them by chat/phone — impersonation of banks and
projects are common.

**Prepare-and-hold is the default posture, and it is legitimate.** Build the folder, keep it
ready (a single PDF set on the phone + one printed set in the bag), and hand it over only when
asked — the duty to ask sits with the developer/bank, not with the buyer. Say that plainly and
skip the moralising: preparing documents and not volunteering them is ordinary practice, not
concealment. The non-negotiables are truthful answers (including the aggregate total), no cash,
no third-party accounts, and no active concealment. Buying in the buyer's own name is also the
lowest-paperwork route — a co-buyer, spouse or relative adds a whole document tier.

## Exchange mechanics (Bitkub and peers)

- **KYC level ≠ loyalty/privilege level.** The privilege page (Gold tiers, KUB Gem points,
  cumulative trading volume) says nothing about limits. Daily deposit/withdraw limits come
  from the KYC level: the deposit/withdraw screen shows "remaining daily withdrawal limit",
  and the web page is `bitkub.com/th/account/level`. When the user cannot find it in the app,
  have them open the THB withdrawal screen (shows the limit) or ask exchange support.
- Sell in planned rounds, **each round below THB 5M**; for ~THB 5M total, four rounds of
  ~1.25M a few days apart is the default, two rounds of ~2.5M if the transfer date is close.
- Selling one lump sum is legal but concentrates price risk, moves the bank statement out of
  pattern, and can hit per-day withdrawal limits.
- Bitkub trading fee ~0.25%; bank withdrawal ~20–35 THB; licensed exchanges cancel VAT on sales.
- Record for every sale: date, USDT sold, rate, THB value, fee, reference/TxID, slip file.
  That table is the cost basis for the PND.90. The user must keep the Thai SIM active while
  abroad to receive the sale OTPs.

## Keep a per-lot source-of-funds ledger (the deliverable that ends the anxiety)

Build one workbook + one Word summary and update them at every transfer, not at the end.
Workbook `/opt/data/ตารางบันทึกUSDT_และงบซื้อบ้าน.xlsx`: sheet `1. บันทึกรับ-ขาย USDT` gets one
รับ row and one ขาย row per lot (the summary sheet's SUMIFs depend on both), plus a
`N. หลักฐานล็อต N` sheet per lot carrying the full chain below. Word
`/opt/data/สมุดบันทึกที่มาของเงิน_ซื้อบ้าน.docx`: sources table, per-lot chain, tax note, next
steps. Generators live at `/opt/data/scripts/_update_source_of_funds*.py` — edit the script and
re-run; never hand-edit the .docx/.xlsx output.

Capture four hops per crypto lot, every field copied character-by-character from the user's
screenshots (never paraphrased, rounded, or reconstructed):

1. **Sending exchange withdrawal** — amount sent, network (BSC/BEP20 etc.), network fee, net
   received, timestamp, **full TxID (0x + 64 hex)** and the recipient wallet address.
2. **Thai exchange deposit** — amount credited, timestamp (usually UTC; add +7 for Thai time),
   deposit/order ID, and the sender label the exchange displays.
3. **Sale to THB** — quantity, matched rate THB/USDT, gross THB, trading fee (~0.25%), net THB,
   matched timestamp, internal TxID.
4. **THB withdrawal to the buyer's bank** — amount, withdrawal fee, net credited, bank + account
   in the buyer's own name, timestamp, internal TxID.

**Cross-check every read with arithmetic before writing it into the file.** Per lot compute
`qty × rate = gross`, `gross − 0.25% = net sale`, `withdrawal − withdrawal fee = bank credit`
and compare against the screenshots. A match within a satang confirms the digits you read; a gap
means a misread digit or — more often — that the lot was sold in **partial fills**. The exchange
chat shows only the last few fill bubbles (89 + 5,006 + 5,000 USDT …), so never sum the bubbles
or infer the lot total from them: the sale receipt and the THB withdrawal are the truth, and a
partial-fill lot stays one รับ row + one ขาย row in the ledger.

**Ask which pot a balance belongs to before counting it.** A wallet screenshot reading
`balance 1,532,563.53 / available 0.00` is not spendable money — `available 0.00` means holds or
a different sub-balance, so keep it out of the house budget until the user explains it. Likewise,
when the user calls a lot "my savings" (เงินเก็บของฉัน) while the ledger says it came from the
donor, record their label verbatim and ask which account they mean; never reclassify a lot's
origin on your own, because the origin is what the s.42(17) ceiling and the whole file rest on.

**Quote one "cash available" figure, and quote only the verified one.** Money available = the
balance(s) confirmed by a bank statement / e-statement. Anything read off an app screenshot, a
wallet, or a platform balance is a *separate* line labelled "not yet verified", never added into
the same total. Adding a wallet screenshot to a statement-backed balance produced a headline
number ~1.5M higher than the account actually held, and the user caught it — the error destroys
trust in every later number in the plan. State the verified total, then list the unverified pots
underneath with what document would promote each one.

Also have the user download the exchange's monthly statement/CSV and the bank statement for the
same day — banks accept those where they merely tolerate screenshots.

Never fabricate an identifier. If a TxID is unreadable, leave the cell blank with "ก็อปจากแอป":
OCR over a 64-hex string produces plausible-looking nonsense, and a wrong TxID in a
source-of-funds file is worse than a missing one. Re-read a TxID twice before writing it down.

Tax shortcut worth stating plainly: coins received and sold **the same day** have cost basis ≈
sale price, so the s.40(4)(ฌ) gain is ~zero and the 15% withholding should be ~zero too — still
collect the withholding certificate (to reclaim any over-withholding on the PND.90) and book the
trading + withdrawal fees as expenses.

Gift-ceiling check at every receipt: convert the year's cumulative USDT at the day's rate and
also state the FX trigger — `THB 10,000,000 ÷ cumulative USDT` is the THB/USDT rate at which the
s.42(17) exemption breaks (240,000 USDT → ~41.7). Recording **received** lots separately from
**planned** ones keeps that arithmetic honest; never merge a promised transfer into the ledger as
if it had arrived.

## Tax (PND.90): settle "must I file?" before explaining "how to file"

Answer in that order — the mechanics are easy, the eligibility question is where users get
frightened. Full export steps, thresholds, penalties and the online walkthrough live in
`references/thai-crypto-pnd90.md`.

- **Donor money never enters the return.** Gifts from a non-spouse are exempt up to THB 10M per
tax year (s.42(17)), so they are not assessable income and need no line in the PND.90.
- **Crypto: assessable amount = gain only** (s.40(4)(ฌ)), never the THB that landed in the bank.
Gain = sale − (value on the day received + buy/sell/transfer fees). Losses on licensed-exchange
trades offset gains inside the same year; they do not carry forward. So say out loud that a
withdrawal of, say, THB 3.4M is a conversion, not income.
- **Filing duty**: for s.40(2)–(8) income the threshold is assessable income above THB 120,000
(single) — 220,000 if married. A year that nets to roughly zero or a loss, with no other income
and no withholding, means **no duty to file**. State that plainly rather than defaulting to "you
must file". Ask about other income first (affiliate commissions, rent, interest above 20,000) —
that is what usually crosses the line, and the user may not think of it as income.
- **Record-keeping duty is separate and always applies** (ประกาศอธิบดี ฉบับที่ 424: coin, date and
time, transaction type, quantity, unit price, THB value, fees, cost). That is the real reason to
keep the ledger — being able to prove a net loss when asked. A user who stops at "no need to
file" and keeps no books has dropped the one obligation that survives.
- **Voluntary filing is a legitimate option**, not a mistake: the receipt proves the activity was
reported (useful when a bank or developer asks), and any withholding comes back. Never file a
fabricated zero to "make it look clean". Deadlines: 1 Jan – 31 Mar of the following year;
e-filing extends to about 8 Apr.
- Timing to recommend: export the yearly report in early January once the year closes, build the
gain/loss book in Jan–Feb, decide file or no-file before 31 Mar. Set a reminder for the export
rather than leaving it to memory.

## Bank and payment practice

- Tell the bank **2–3 weeks ahead** (branch manager or in-app message): "I will sell digital
  assets and receive about THB X into my own account to buy a house." Optional, not legally
  required, but the cheapest insurance against a temporary hold landing on the transfer date.
  If the user skips it, that is fine — they just need the folder ready and must answer the phone.
- Advise answering a bank call truthfully, including the aggregate, and sending the folder the
  same day. Never call back a number from an SMS — use the number on the card.
- Pay the developer with a **cashier's cheque or own-name transfer**; letting the THB sit in
  the buyer's account for a week or two first makes it read as ordinary savings.
- Aim for transfer completion **7–10 days before the deadline**, and never in the last week of
  December (land office, banks, and developer finance teams close for the holidays).

## When the land office is the risk: the loan-assisted purchase

Ask first what the loan is FOR. If the buyer has the cash, a mortgage never improves the
finances — it only adds a bank verification layer on top of the money path. That can still be
the right call, because a cash purchase by a household with no provable income and a foreign
partner is exactly the profile officers now interview, and comparable cases have failed at the
transfer desk. Recommend the loan only when the user (or the salesperson) reports that real
risk, and say plainly that they are paying interest for paperwork comfort, not for money.

Rules for the recommendation:

- It must be a **real loan with real repayment**, never a cosmetic one. Frame the structure as
  "my own money in my own account + a genuine bank loan for the rest", and answer the total
  truthfully. Do not coach anyone to make the cash portion "look smaller" or to disguise a
  payment; a truthful smaller cash leg (because a real loan covers the rest) is fine, hiding the
  aggregate is not.
- **Settle the borrower profile before planning anything**: a full-time caregiver with no salary
  may not qualify alone. A foreign partner as co-borrower or guarantor drags his income in and
  makes the deal read as nominee — keep the property, the SPA and the loan in the buyer's name
  only, and say why.
- **Get "no prepayment penalty, no clawback of the promotional rate" in writing** in the offer
  letter. A salesperson's chat message is not the contract clause; this is the single clause that
  decides whether paying the loan off early is cheap or expensive.
- **Separate the three things a salesperson blends into "ไม่มีค่าธรรมเนียม":** (1) fees waived by the
  project–bank promotion (appraisal, processing, documentation) — real money, get them in writing;
  (2) **interest**, which no promotion waives and is the actual cost of the plan; (3) the
  **prepayment / early-settlement clause**, which is neither a fee nor interest and is what decides
  the cost of exiting early. Ask for all three as one written list, then repeat them back to the
  user in those three buckets — users conflate them and think the loan is free.
- **Guarantor is not co-borrower.** A foreign partner may stand as guarantor — his income and
  overseas assets are exactly what the bank wants to see — but he must not be co-borrower, co-owner,
  or named in the SPA, because that is what converts a legitimate purchase into nominee territory.
  Keep property, contract and loan in the buyer's name only, and say why in one sentence.
- Interest is the real cost (≈THB 151k per year on a 2.75M loan at 5.5%), not the registration
  fees; prepaying early is what keeps it small.
- Nominee is a Thai name holding property for a foreigner's benefit — illegal. A Thai buyer
  paying from her own account, with an exempt gift, and no ownership right for the partner is
  **not** nominee; the file must simply show those four facts.

Costs, question list for the bank, borrower-profile checks and the interview-ready folder:
`references/mortgage-and-land-office.md`. Appraisal-day prep and the honest answer to "does the
appraiser enter the unit" live in the same file. So do the loan-application stages (approval is not
debt; what can still be cancelled at each stage), the salesperson's "backup application" naming the
partner as borrower, how to read "did you try other banks?", and why two bank meetings do not fit
in one afternoon.

Asset inventory, reading Thai title deeds, disclosure tiers (what goes in the bank file and what
stays private), savings-lottery evidence and the ffmpeg+tesseract OCR pipeline for Thai official
documents: `references/asset-inventory-thai-deeds.md`.

When the user forwards the partner's monthly bank statements to build the guarantor file, follow
`references/bank-statement-analysis.md`: classify debit/credit by word x-coordinate (reading order
loses it), never double-count the statement's own total row, fetch the FX rate instead of
remembering it, and give an honest verdict — a low-balance pass-through account with one brokerage
payout is weak evidence however large the numbers look.

For the guarantor's *income* proof, the ranking and the substitutions live in
`references/mortgage-and-land-office.md` ("Guarantor evidence", "The bank's document checklist is
often the wrong one"). Two rules from it are worth carrying in the head: the strongest single page is
the partner's foreign **Notice of Assessment** — a tax portal **Statement of Account** (payments and
penalties) is a different document and does not state income — and a checklist headed
**รายได้ประจำ** is the salaried-employee template, so a buyer with no employer must ask for the
self-employed / other-income / collateral list instead of trying to satisfy lines that cannot exist.
A `REKAP_*` summary workbook you built yourself is a working aid, never evidence: label it as such and
keep the bank's own statements as the file copy.

## After booking: handover inspection gates the transfer

Handover inspection is a separate job from the money path, and a defect list is leverage: the
report itself states the contractor must fix everything and warrant that it will not recur
**before** delivery. Workflow, report decoding, tracker columns and the re-inspection rule live in
`references/handover-inspection.md`. What such reports never cover — ask the project separately:
ground-fill level versus the local flood level (in cm, not adjectives), the project's drainage
(pipe size, sumps, final outfall), and roof material plus insulation spec.

## Pitfalls seen in practice

- **Never let a salesperson file a second application with the foreign partner as BORROWER "in case
  the buyer fails".** A partner-borrower carries the same nominee reading as a partner-owner and puts
  him on the hook for a debt he gains nothing from; submit one application, buyer as sole borrower
  and partner as guarantor. If such a form was already signed, withdraw it before the loan agreement
  is signed. Answer "can I still cancel?" by stage, not with a yes/no — approval is not debt.
- The user's past experience ("last time I bought a 5M condo and only signed a contract") is
  normal: that money was already inside the Thai banking system and predates the crypto
  rules. Explain the delta, do not argue.
- Booking / reservation money is usually non-refundable; warn about paying a large deposit
  before the funding timeline is confirmed, and ask the salesperson for the document
  checklist **before** paying it.
- A donor's inability to produce broker statements is not a blocker — fall back to the
  declaration + TxIDs + the buyer's own bank trail.
- House-model codes (SG4, SGC, SA7, …) are project-internal labels: with no record of the code,
  say so and pull the spec from the **developer's own project page**, never from aggregator
  listings — aggregators mix projects, rename models and drop the promo terms, so their numbers
  look authoritative and are wrong. Quote only what the page states (usable area, bedrooms,
  bathrooms, parking, project size/units/address, start price) and get the price and current
  promo for that exact model from the salesperson. Never infer one model's area, rooms or price
  from a neighbouring model in the same project — the step to 4 bedrooms is often the largest
  price jump in the range.
- A same-day crypto deposit larger than the daily limit needs to be split across days (e.g.,
  100,000 + 50,000 USDT); check the limit on the deposit screen before the donor sends.
- **Read every number from the document's body, never from the filename.** A PDF saved as
  `..._บ้านเลขที่ 289_65_...pdf` can say `บ้านเลขที่ 298/65` inside; the filename is the sender's
  shorthand. Raising a red flag from a filename wastes the user's trust and makes them correct
  you. Same class as reading Thai month abbreviations (ธ.ค./ส.ค./ก.ค./พ.ค.) off a low-resolution
  screenshot: only state a value after reading it in the text, and when a number drives a warning
  or a decision, ask the user to confirm instead of building the warning on the read.
- Thai month abbreviations, house/unit numbers, long hex strings and **personal names** are the
  recurring misreads. For any of them that changes advice, re-crop at 3–5× and read twice before
  concluding.
- **Never re-derive the user's own name (or the donor's) from OCR.** Take it from what the user has
  stated, and when a document appears to show a different name, ask — do not report the reading.
  A watermarked low-resolution statement header read as a different surname triggered a correction
  and an apology, and a name that drives no decision still costs trust when it is wrong. The same
  caution applies to passport data pages of third parties (tenants): transcribe only what the user
  needs, partly mask the number in anything written down, and never paste those images into a group
  or a public page.
- **A Thai chanote's front page carries the FORMER owner.** The OCR-visible "ให้แก่ <name>" line is
  the previous transfer, not the current holder; the registered owner sits on the back or a later
  page. Never announce that the user's land is in someone else's name on that reading — ask once
  ("ชื่อในโฉนดเป็นชื่อคุณไหม") and expect "ชื่อฉันอยู่ด้านหลัง". Getting this wrong turns the user's own
  assets into a problem they then have to argue about.
- **Any "borrow less" alternative must be arithmetic-checked against verified cash before it is
  offered.** Compute the floor — `min loan = price − verified cash + registration fees` — and only
  present scenarios above it. Offering 30%/23% plans against a 6.5M price and 3.83M verified cash
  produced options that left the buyer 0.7–1.2M short; unsellable options read as the assistant not
  understanding the numbers.
- A guarantor/income-proof file assembled from the partner's statements must be judged on balance
trend, whether it is a salary account, pass-through behaviour, and recurring vs one-off credits —
and reported honestly even when that weakens the plan. Quote currency conversions with the fetched
rate and its date; a remembered rate in a document a bank reads is a defect.
- Statement anomalies need the contract read first. A month with no rent credit, or a month with two
equal credits, is usually the tenancy's payment-date and deposit clauses at work — not a missing
payment. Raising a false alarm on the user's own money costs more trust than the extra minute of
reading. Same discipline for property identity: which unit produced a credit is decided by the
tenancy agreement's premises/management-corporation reference, never by the owner's mailing address
or by a `MCST <no>` payment alone.
