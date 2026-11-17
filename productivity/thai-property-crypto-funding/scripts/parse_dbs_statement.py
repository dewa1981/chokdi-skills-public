#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse DBS/POSB *Consolidated Statement* PDFs into transactions by column position.

Reading order loses the debit/credit/balance distinction, so amounts are classified by
word x-coordinate. Calibrated for DBS/POSB Consolidated Statement layout:
  withdrawal ~ x 340-420, deposit ~ x 430-500, running balance > 500.
If a future layout shifts, print one page with coordinates and adjust the bands.

Usage:
  python parse_dbs_statement.py stmt1.pdf [stmt2.pdf ...] [--csv out.csv]

Needs pymupdf. Run it with an interpreter that has pymupdf (find a venv that does):
  find / -maxdepth 7 -type d -name pymupdf -path '*site-packages*' 2>/dev/null

Output: per-file summary (account, as-at date, closing balance, counts, in/out totals),
every credit line, and optional CSV. Compare the printed totals with the statement's own
"Total Balance Carried Forward" line before trusting the parse.
"""
import csv
import re
import sys

import pymupdf

AMT = re.compile(r"^[\d,]+\.\d{2}$")
W_MAX, D_MAX = 420.0, 500.0  # upper x bound for withdrawal / deposit columns


def parse(path):
    doc = pymupdf.open(path)
    first = doc[0].get_text()
    acc = re.search(r"Account No\.?\s*([\d\-]+)", first)
    as_at = re.search(r"as (?:at|of)\s+(\d{1,2} \w{3} \d{4})", first)
    txns = []
    for page in doc:
        rows = {}
        for x0, y0, x1, y1, w, _b, _l, _n in page.get_text("words"):
            rows.setdefault(round(y0, 0), []).append((x0, w))
        cur = None
        for y in sorted(rows):
            pairs = sorted(rows[y])
            words = [w for _x, w in pairs]
            if not words:
                continue
            if re.match(r"^\d{2}/\d{2}/\d{4}$", words[0]):
                cur = {"date": words.pop(0), "desc": [], "wd": None, "dep": None, "bal": None}
                pairs = pairs[1:]
            if cur is None:
                continue
            for x, w in pairs:
                if AMT.match(w):
                    if x < W_MAX:
                        cur["wd"] = cur["wd"] or w
                    elif x < D_MAX:
                        cur["dep"] = cur["dep"] or w
                    else:
                        cur["bal"] = w
                else:
                    cur["desc"].append(w)
            txns.append(cur)
    # the statement's own totals row sits in the same columns -> must be dropped
    txns = [t for t in txns if "Total Balance Carried" not in " ".join(t["desc"])]
    seen, uniq = set(), []
    for t in txns:
        key = (t["date"], tuple(t["desc"][:4]), t["dep"], t["wd"])
        if key not in seen:
            seen.add(key)
            uniq.append(t)
    for t in uniq:
        t["wd"] = float(t["wd"].replace(",", "")) if t["wd"] else 0.0
        t["dep"] = float(t["dep"].replace(",", "")) if t["dep"] else 0.0
        t["desc"] = " ".join(t["desc"])
    return {
        "path": path,
        "account": acc.group(1) if acc else None,
        "as_at": as_at.group(1) if as_at else None,
        "closing": uniq[-1]["bal"] if uniq else None,
        "txns": uniq,
    }


def main(argv):
    csv_out = None
    if "--csv" in argv:
        i = argv.index("--csv")
        csv_out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if not argv:
        print(__doc__)
        return 1
    all_rows = []
    for path in argv:
        r = parse(path)
        dep = sum(t["dep"] for t in r["txns"])
        wd = sum(t["wd"] for t in r["txns"])
        print("=" * 70)
        print(f"{path}\n  account={r['account']} as_at={r['as_at']} closing={r['closing']}")
        print(f"  credits={sum(1 for t in r['txns'] if t['dep']):>2}  total_in={dep:,.2f}"
              f"  debits={sum(1 for t in r['txns'] if t['wd']):>2}  total_out={wd:,.2f}")
        for t in r["txns"]:
            if t["dep"]:
                print(f"    +{t['dep']:>12,.2f}  {t['date']}  {t['desc'][:88]}")
            all_rows.append({"file": path, "account": r["account"], "date": t["date"],
                             "deposit": t["dep"], "withdrawal": t["wd"], "balance": t["bal"],
                             "description": t["desc"]})
    if csv_out:
        with open(csv_out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)
        print(f"\nCSV: {csv_out} ({len(all_rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
