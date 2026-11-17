# Reading a partner's / guarantor's overseas bank statements

Use when the user forwards a stack of monthly bank statements (the foreign partner's, or her own)
to build the guarantor or income-proof file. The deliverable is a verdict plus an xlsx summary —
not a transcript of the PDFs.

## Step 1 — extract transactions by column position, not by reading order

`page.get_text()` flattens a statement table into a stream where a debit, a credit and the running
balance are indistinguishable. Use word coordinates and classify amounts by x:

```python
import pymupdf
pg = pymupdf.open(path)[1]          # page 1 is the account summary; transactions start p.2
rows = {}
for x0, y0, x1, y1, w, b, l, n in pg.get_text("words"):
    rows.setdefault(round(y0, 0), []).append((x0, w))
```

Calibrate the three x-bands once per bank by printing one page with coordinates, then reuse them.
On DBS/POSB *Consolidated Statement*: withdrawal ≈ x 340–420, deposit ≈ x 430–500, running
balance > 500. A date token at the far left (x ≈ 45) starts a new transaction row; the description
lines that follow belong to it.

**Exclude the summary row.** Every statement ends with `Total Balance Carried Forward:` carrying
the statement's own totals in the same columns as the transactions. If you do not filter that row
by its description, every total doubles — a January statement whose withdrawals were SGD 40,618
parses as 81,236 and nothing about the output looks wrong. Filter on
the description, never on row order.

The ready-made parser is `scripts/parse_dbs_statement.py` (pymupdf; classifies amounts by x-band,
drops the totals row, prints per-file in/out totals and every credit, optional `--csv`). Run it
instead of re-deriving the calibration, and still cross-check its totals against the statement's own
totals row before writing numbers into a deliverable.

## Step 2 — cross-check the parse against the statement's own totals

Each statement prints totals for withdrawals, deposits and the closing balance. Compare your sums
to them before writing anything into a deliverable: an exact match proves the parse; a small gap
is usually the `Interest Earned` / cash-rebate line, which has no description text and therefore
attaches itself to the previous transaction. Re-derive, do not hand-wave the difference.

Silent months exist: a statement with no credits at all is evidence, not a missing file. Say so.

## Step 3 — convert currency with a fetched rate, never a remembered one

```bash
curl -s https://open.er-api.com/v6/latest/SGD   # -> rates.THB, time_last_update_utc
```

Print the rate and its date in the workbook header, and keep the source-currency figures as the
primary numbers with the converted value marked `≈`. A deliverable a bank reads must let anyone
re-derive every conversion.

## Step 4 — the verdict, stated plainly

Score the account on five axes and lead with the conclusion:

1. **Balance trend** — month-end balances, min/max/latest.
2. **Salary account or not** — no regular employer credit means it cannot carry a loan on its own.
3. **Pass-through test** — if outflows ≈ inflows and large telegraphic transfers leave the same
day money arrives, the account shows movement, not wealth. Bankers read that as a conduit.
4. **Recurring vs one-off** — one broker/brokerage payout of six figures is a single event, not
   income; label it that way instead of counting it as monthly capacity.
5. **What is missing** — other accounts the inflows name as their source, the missing months, the
   brokerage statement behind a one-off credit.

Do not oversell a weak guarantor file. The bank will read the same numbers; overstating it in the
chat costs the user credibility at the counter. Deliver "this alone is weak, here is exactly what
closes the gap" instead.

## Step 5 — mine the statement for assets and sources the user forgot

Credit lines name the payer and the amount; incoming transfers name the source bank (e.g.
`OCBC FAST`) — ask for that account rather than concluding there is no income. Outgoing lines name
the counterparty: `MCST <no> #<unit>`, `BADAN PENGURUSAN`, `BAYARAN CUKAI TAKSIRAN`, developer
payments, estate-agent commission. Each becomes a line in the net-worth table.

**Do not turn an `MCST <no> #<unit>` payment into "he owns another property".** That number is the
management corporation and unit the payment is *for* — it may well be the very unit the rent
credits come from, with the owner living in a different development that also appears
(`MCST 4220 02-02` = his residence, `MCST 4609 #05-09` = the rented unit). Worse, a wrong "second
property" in a net-worth table is a claim the user will repeat to a bank. Assign a unit only when
a tenancy agreement, SPA or title names that premises or that management corporation; until then
list it as "unit being serviced — owner/use unconfirmed" and ask.

**Reconcile the rent cycle before calling a month anomalous.** A tenancy agreement that makes rent
payable "on or before the Nth day of each month" plus a deposit equal to one month explains both
shapes that look wrong on first pass: a calendar month with **no** rent credit (the cycle simply
fell outside it) and a month with **two** equal credits (deposit + first month, paid before move-in).
Read the payment-date clause and the deposit clause, then say which credits are rent and which are
deposit. Never tell the user "a month is missing, check another account" from the statement alone.

**A summary workbook is not evidence.** A `REKAP_*` xlsx built by summarising these statements is a
working aid for the chat and for cross-checking totals — a bank wants the statement itself. Keep it
clearly labelled in the file index ("สรุปที่ทำขึ้นเอง — ใช้ยื่นแทน statement ไม่ได้") so nobody hands
it over as if it were a bank document.

## Workbook shape (5 sheets, regenerate by script)

`1. สรุปภาพรวม` (holder, bank, account, period, min/max/latest balance, totals, FX + date, then the
⚠️ observations) · `2. ยอดคงเหลือรายเดือน` (month, as-at date, balance, ≈THB, monthly in/out) ·
`3. เงินเข้า (credits)` with a per-category subtotal block · `4. เงินออกก้อนใหญ่` · `5. ต้องขอเพิ่ม`
(numbered request list with *why it is needed* and current status). Keep the generator under
`/opt/data/scripts/_make_*.py` and re-run it when a new month arrives — never append by hand.

QC before delivering, as with every Thai document in this class: assert on key identifiers and
`re.findall(r'[\u4e00-\u9fff]+', text)` must come back empty.
