# Thai PND.90 for crypto-funded buyers — duty, numbers, mechanics

Depth for the "must I file / how do I file" question in `thai-property-crypto-funding`.
Figures and thresholds verified against Revenue Department material in 2026; re-check anything
that drives a real payment before quoting it as current.

## 1. Decide the duty first

| Item | Treatment |
|---|---|
| Gift from a non-spouse | exempt ≤ THB 10,000,000 per tax year (s.42(17)); spouse 20,000,000 → **not** assessable, no line in the return |
| Crypto transfer | assessable = **gain only**, s.40(4)(ฌ) "เฉพาะซึ่งตีราคาเป็นเงินได้เกินกว่าที่ลงทุน" |
| THB withdrawn from the exchange | not income — conversion of an asset |
| Gain | sale − cost; cost = value on the day received **+ fees** (buy, sell, network, bank withdrawal) |
| Losses | offset gains within the same tax year (SEC-regulated exchanges only); never carried forward |
| Filing threshold (single) | assessable income above THB 120,000 for s.40(2)–(8) income; 220,000 if married |
| Withholding | nothing withheld → nothing to reclaim → one less reason to file |

Net-zero or net-loss year with no other income → **no duty to file**. Ask about other income
before saying it (affiliate commissions, rent, interest above THB 20,000); users do not
necessarily think of commission as "income".

## 2. Record-keeping duty (applies even when no filing is due)

ประกาศอธิบดีกรมสรรพากร ฉบับที่ 424 requires anyone earning from crypto transfers to keep books
of the profit/loss and to produce them for examination, with at least:

1. coin/token symbol
2. transfer date and time
3. transaction type
4. quantity
5. unit price
6. THB value
7. THB fees
8. cost

Build this as a sheet in the source-of-funds workbook, one row per transaction, summary line for
the year's net. The purpose is to prove a loss, not to serve the return.

## 3. Deadlines and exposure

- Paper / at the Revenue office: **1 Jan – 31 Mar** of the following year.
- e-Filing (`efiling.rd.go.th`): extended to about **8 Apr**.
- Late or missing: criminal fine up to THB 2,000; uplift 1.5% per month on unpaid tax; penalty
  1–2× the tax if assessed; severe criminal exposure for intentional false statements.
- A PND.90 filing does **not** attach source-of-funds documents — that folder is answered only
  when the bank/developer/land office asks.

## 4. Online filing walkthrough (single filer, crypto income)

1. `efiling.rd.go.th` → register with the 13-digit ID if never filed → log in.
2. Personal income tax → PND.90/91 → "ยื่นแบบ" → choose PND.90.
3. Verify prefilled identity/address; add income under s.40(4)(ฌ) with the **net** figure for the
year (0 when a net loss).
4. Deductions: personal 60,000; child 30,000 each; anything else with evidence (life/health
   insurance, mortgage interest, donations).
5. Review the summary (tax is usually 0 in this profile) → confirm → save the acknowledgement
   PDF as proof of filing.

Alternatives: Revenue office in person (bring the ID), hotline **1161** for a free pre-check,
or an accountant (≈500–2,000 THB) when volume or foreign-sourced cost is messy.

## 5. Getting the numbers out of Bitkub

- **Yearly Report (Tax Purpose) — website only, not the app**: log in → Wallet icon (top right)
  → **History** → tab **"Yearly Report (Tax Purpose)"** → **Request a report** → pick the year →
  **Confirm** → poll the row: Processing → Complete → **Download**; `Failed` usually means no
  transactions that year, so re-request only if that is wrong. The download is a ZIP of
  per-token folders containing CSVs.
- The yearly report is complete **only after the calendar year ends**. Before that, use
  History → Download with an explicit date range for a current statement.
- Tax invoice: History → Download → "Tax invoice" → date range.
- Stamp-ready documents (Transaction History Certificate, Wallet Balance Certificate,
  Certificate of Membership): request through support — the green chat button on the website, or
  the app's "ช่วยเหลือ" button on the Home screen.
- Exchange trades normally deduct only the trading fee (≈0.25%), so no 15% appears on the receipt;
  still collect any withholding certificate and credit it on the return if one was issued.

## 6. What to tell the user, in one paragraph

"Gifts stay outside the return up to 10M a year, and crypto is taxed on the gain, not on the
money you moved to the bank. If the year nets to a loss and you have no other income, you do not
have to file — but keep the transaction book, because that is the record you would show if asked.
Filing voluntarily is also fine and leaves a receipt."
