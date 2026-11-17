# Funding a Thai house purchase in cash + proving source of funds

Use when the question is about **how to pay for** the house (budget math, gold, land sale,
installments, gift from a non-spouse partner, crypto → THB, AML/KYC paperwork, tax) rather
than which project to pick. This user (Patty) buys **in cash, in her own name**, funded by
USDT her partner (not registered in marriage) transfers to her — so the whole burden of
proving source of funds sits on her.

## 1. Budget math — always recompute, never reuse a stale total
```
total needed = price + transfer fee + furnishing + reserve(5%)
transfer fee = 0.01% of price  (government measure, residence ≤ 7M THB — see §4)
```
Recompute from scratch every time ONE input changes (price, cash-only, deadline, amount
arriving, gold sold). The user changes these constraints mid-conversation; answering with
the previous plan's numbers is the fastest way to lose her trust. Close every money answer
with the single number that would change the plan (how much gold? how much can you save per
month? when does the transfer land?).

## 2. Routes to close the gap (decision table)
| Route | Speed | Paperwork | Cost |
|---|---|---|---|
| Own cash + accumulated USDT | slow (monthly drip) | heavy (crypto trail) | none |
| Sell gold bars | same day | **lightest** — gold-shop receipt only | only the dealer spread |
| Sell the land plot | 1–3+ months (needs a buyer) | light | transfer fee 2% + specific business tax 3.3% (<5 yr) or 1% WHT + 0.5% stamp |
| Developer 0% installment (ผ่อนดาวน์) | buys 12–24 months of time | light | only if the balance still lands in cash |
| Mortgage | fastest | bank needs provable income | ~30–35k THB/mo per 4.4–4.7M over 20 yr |
Rule: **a gift from a partner is NOT countable income for a mortgage** — banks assess the
borrower's own taxable income, so cash-only is the realistic route for this user, and a
partner-transfer-funded buyer should be told this before they fall in love with a unit
above their cash.

## 3. Source-of-funds document set (the part users fear most)
Explain it as **5 levels** and lead with the fact that levels 1–2 are all that is normally
touched:
1. **Buyer's own (she can always produce these):** ID card · bank statements showing the THB
   arriving from the exchange · exchange trade/withdrawal history (PDF) · TxID (re-printable
   from any block explorer forever).
2. **Donor (only 3 items, signable + photographable — no old files needed):** Gift Letter
   stating amount + purpose · copy of donor ID/passport · 1-page Donor's Declaration of
   Source of Funds.
3. Donor's supporting evidence — only if pressed: exchange tax slips from his country,
   condo tenancy agreements/rental statements, broker contract notes.
4. Buyer's own Declaration of Source of Funds (Thai + English).
5. Bank reference letter / exchange confirmation letter — requested from the branch manager.
**Core rule: never send the user to dig up the donor's broker/bank history first.** The
written declaration substitutes for it — a signed declaration plus whatever documents exist
is normally accepted in place of lost statements. The donor's own tax position is his
problem, not hers; the buyer only has to make the money path readable.
One story, told identically to the bank, the developer and the land office:
gift from a partner (not legally married) who earns rental income from condos abroad plus
investment/trading income → transferred as USDT → sold on a Thai licensed exchange → THB into
her own bank account → paid by cheque/transfer from her own account. Never cash, never a
third party's account, never a large P2P trade.

## 4. Thai rules worth memorising (verify before quoting — measures expire)
- **Gift exemption (ม.42(17)):** gifts by a non-spouse/non-ascendant are exempt up to
  **10M THB per tax year** (20M for a spouse/ascendant). Track the **cumulative total per
  calendar year**: stacking gifts across the ceiling creates tax on the excess, so when the
  running total approaches 10M, receive the rest in the next tax year.
- **Crypto sale:** gain = sale proceeds − cost basis (value at each receipt date, per-lot FX),
  taxed as ม.40(4)(฿) income; losses offset gains in the same year; licensed Thai exchanges
  withhold on gains and issue the certificate; file ภ.ง.ด.90.
- **Transfer/mortgage fee measure:** 0.01% for residences ≤ 7M THB (Thai individual buyer),
  renewed in 1-year windows — worth ~110,000 THB on a 5.5M house vs the normal 2%. Confirm
  the project joins the measure.
- **AML:** cash-type transactions ≥ 5M THB trigger source-of-funds documentation. Handling is
  in §5. Do not advise splitting payments across accounts to stay under it.
- **Gold:** quote the current สมาคมค้าทองคำ buy-back price (bars: ~66,100 THB per baht-weight
  in Oct 2026, spread only ~0.3% vs 5–10% on ornaments). **1 baht-weight = 15.244 g**. A
  gold-shop receipt is the cleanest source-of-funds evidence available to this user.
- **Land near แม่สาย:** ~290k THB/rai for agricultural plots away from the highway, up to
  1.6–3.5M/rai on พหลโยธิน — value her 2-rai plot only after checking title/access/road frontage.

## 5. Receiving a lump sum that crosses 5M THB
- Sell the crypto in **rounds of ≤500k THB** (8–10 rounds over 2–3 weeks), not one trade: it
  keeps the bank statements unremarkable and stays inside exchange limits.
- **Check the exchange's sell/withdraw limits and raise KYC level BEFORE the transfer lands** —
  discovering a daily cap after receiving the money is unrecoverable in a short window.
- **Book the bank branch manager 2–3 weeks ahead** and state the plan (amount, origin, purpose).
  It prevents freezes, and some banks issue a reference letter the developer will accept.
- Closing **before ~20 December** if the purchase must land inside the calendar year: land
  offices, banks and developer sales offices all stall over the Thai New Year break.

## 6. Deliverables that work for this user
- Thai **.docx** (never .md) covering: the one-story script, the bank/project sentence she can
  say verbatim, the 5-level doc set as a tickable list, the do-not-do list, and a dated
  6-step timeline to the transfer date.
- Reusable generators already on disk (re-run or copy; do not rewrite from scratch):
  `scripts/_make_chr_house_plan.py`, `_make_fund_source_checklist.py`,
  `_make_usdt_tracker_xlsx.py`, `_make_gift_letter_bilingual.py`, `_make_fundflow_doc.py`,
  `_make_sof_declaration.py`, `_make_donor_declaration.py`, `_make_lumpsum_guide.py`,
  `_make_house_fund_plan.py` — all under `/opt/data/`, output .docx/.xlsx into `/opt/data/`.
- Offer a month-by-month funding schedule (what to sell when, cumulative total by the transfer
  date) rather than a single lump figure; she decides from the timeline, not the total.

## 7. Pitfalls
- Don't answer a funding question with the previous plan's numbers — re-run the arithmetic
  after every constraint change (price, cash-only, deadline, amount arriving).
- Don't tell her to sell "all" the gold or to use the land: present what each asset unlocks at
  today's price and let her choose; she keeps a hedge deliberately.
- Don't ask the developer for a booking deposit before requesting their KYC/AML document
  checklist — deposits are usually non-refundable if she later cannot complete the payment.
- Don't equate "ผ่อนดาวน์" with an escape from the deadline: it spreads the cash flow but the
  full balance is still due at transfer.
- Don't provide a mortgage as the easy answer for a buyer whose only income is a partner's
  gift.
