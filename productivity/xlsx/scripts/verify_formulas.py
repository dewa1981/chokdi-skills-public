#!/usr/bin/env python3
"""Verify that an .xlsx formula model actually calculates, without LibreOffice.

openpyxl never evaluates formulas and `soffice` is frequently absent on a VPS.
This loads the workbook with the `formulas` package, calculates the whole model
in pure Python, and compares the requested cells with expected values.

Install:  pip install formulas      (heavy: pandas + numpy + schedula)

Usage:
    python scripts/verify_formulas.py model.xlsx --list
    python scripts/verify_formulas.py model.xlsx --sheet OFFICE --check 'C11=752.5'
    python scripts/verify_formulas.py model.xlsx --sheet OFFICE --dump 11 12 23

Exit code 0 = all checks matched, 1 = mismatch, 2 = cell could not be read.

Pick expected values from an INDEPENDENT hand calculation, never from the same
formulas you just wrote — otherwise the check proves nothing.
"""
import argparse
import sys
import warnings

warnings.filterwarnings('ignore')


def load_model(path):
    import formulas
    xl = formulas.ExcelModel().loads(path).finish()
    return xl.calculate()


def value_of(sol, path, sheet, cell):
    """Cells come back as arrays/None; unwrap to a scalar."""
    key = "'[%s]%s'!%s" % (path.rsplit('/', 1)[-1], sheet, cell)
    hit = sol.get(key)
    if hit is None:  # case-different sheet names still resolve usually; try scan
        up = key.upper()
        for k, v in sol.items():
            if k.upper() == up:
                hit = v
                break
    if hit is None:
        return None
    try:
        return hit.value[0][0]
    except Exception:
        return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('workbook')
    ap.add_argument('--sheet', default=None)
    ap.add_argument('--check', action='append', default=[],
                    help="EXPECTED like 'C11=752.5' (cell=value)")
    ap.add_argument('--dump', nargs='*', type=int, default=None,
                    help='row numbers to print (needs --sheet)')
    ap.add_argument('--list', action='store_true', help='print calculable cell keys')
    a = ap.parse_args()

    sol = load_model(a.workbook)
    if a.list:
        for k in list(sol)[:200]:
            print(k)
        print('total keys:', len(sol))
        return 0

    bad = 0
    for item in a.check:
        if '=' not in item:
            print('SKIP (no =):', item)
            continue
        cell, expected = item.split('=', 1)
        cell = cell.strip()
        sheet = a.sheet
        if '!' in cell:
            sheet, cell = cell.split('!', 1)
        got = value_of(sol, a.workbook, sheet, cell)
        try:
            ok = got is not None and abs(float(got) - float(expected)) < 0.01
        except (TypeError, ValueError):
            ok = False
        print('%-18s %-6s expected=%-14s got=%s  %s'
              % (sheet, cell, expected, got, 'OK' if ok else 'MISMATCH'))
        if not ok:
            bad += 1

    if a.dump and a.sheet:
        for row in a.dump:
            cols = 'CDEFGAB'
            print('row %-4d' % row,
                  ' | '.join('%s%s=%s' % (c, row, value_of(sol, a.workbook, a.sheet, '%s%d' % (c, row)))
                             for c in cols))

    if a.check and bad:
        print('%d mismatch(es)' % bad)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
