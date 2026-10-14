"""Read the school's own workbook directly: class grids for every band.

Layout, found rather than assumed: a header row holds the period numbers 1..9 repeated per day;
a section row holds that section's subjects in those columns, and the row under it holds the
teachers. A cell may name several teachers, which means the class splits and all of them are busy.
"""
import re, sys, json
from collections import Counter, defaultdict
import openpyxl

SEC = re.compile(r"^\s*(\d{1,2})\s*([A-H])\s*$")


def _cells(ws):
    return [[c.value for c in row] for row in ws.iter_rows()]


def period_columns(grid):
    best, score = None, 0
    for r, row in enumerate(grid):
        idx = [i for i, v in enumerate(row)
               if str(v).strip() in list("123456789") or (isinstance(v, (int, float)) and 1 <= v <= 9)]
        if len(idx) > score: best, score = (r, idx), len(idx)
    return best


def read_band(path, sheet):
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]
    grid = _cells(ws)
    hdr, cols = period_columns(grid)
    out = {}
    for r, row in enumerate(grid):
        m = SEC.match(str(row[0] or ""))
        if not m or r + 1 >= len(grid): continue
        sec = f"{m.group(1)}{m.group(2)}"
        subs = [str(grid[r][c] or "").strip() for c in cols]
        teas = [str(grid[r + 1][c] or "").strip() for c in cols]
        if sum(1 for x in subs if x) < 10: continue        # not a real section row
        out.setdefault(sec, (subs, teas))
    return out, len(cols)


if __name__ == "__main__":
    for sheet in ("CLASS 9 AND 10", "class 6-8", "class 11& 12"):
        rows, n = read_band("../xl/classes.xlsx", sheet)
        filled = {s: sum(1 for x in v[0] if x) for s, v in rows.items()}
        multi = sum(1 for v in rows.values() for t in v[1] if "/" in t)
        print(f"{sheet:16s} {len(rows):2d} sections, {n} slots/week, filled {min(filled.values())}-{max(filled.values())}, "
              f"{multi} cells naming several teachers")
        print("   ", list(rows)[:12])
