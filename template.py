"""The school-facing input format: one workbook a timetable coordinator fills in.

Six tabs, and only one of them is long:

  Read me       worked examples in this school's own labels
  School        one row per band: days, periods a day, which period the break follows
  Classes       one row per class, and the period its day ends after if it is a short one
  Teaching      one row per subject a class takes: how many periods, who teaches it, and the
                three things that cannot be guessed from the grid (see below)
  Fixed slots   anything that always happens at a named time
  Rules         everything else, in plain English, marked must or preference

The Teaching tab is designed around the four structures of the data model, because those are
exactly what a grid cannot distinguish and a person can:

  all at once?     yes  -> the class divides and every teacher named is busy in that period
                   no   -> the teachers named share the week between them, one per lesson
  split of week    when they share, how many lessons each takes, in the same order
  joins classes    other classes whose students join this lesson, so the teachers are busy once

A row may name several classes at once (`9A-9D`, `9A, 9B`, `grade 9`), which is how the same
curriculum is entered once for a whole grade rather than once per class.
"""
import re
from collections import defaultdict
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HEAD = Font(bold=True, color="FFFFFF")
FILL = PatternFill("solid", fgColor="2F5D50")
NOTE = Font(italic=True, color="6B6B63")
TABS = ["Read me", "School", "Classes", "Teaching", "Fixed slots", "Rules"]


# ---------------------------------------------------------------- expanding class lists
def classes_in(text, known):
    """`9A-9D`, `9A, 9B`, `grade 9` or `9A` to a list of classes."""
    out, text = [], str(text or "").strip()
    for part in [p.strip() for p in text.split(",") if p.strip()]:
        m = re.fullmatch(r"(?:grade\s*)(\w+)", part, re.I)
        if m:
            out += [c for c in known if c.rstrip("ABCDEFGH") == m.group(1)]; continue
        m = re.fullmatch(r"(\w+?)([A-H])\s*-\s*(?:\1)?([A-H])", part, re.I)
        if m:
            g, a, b = m.group(1), m.group(2).upper(), m.group(3).upper()
            out += [c for c in known if c.startswith(g) and a <= c[len(g):].upper() <= b]; continue
        out.append(part)
    seen = []
    for c in out:
        if c not in seen: seen.append(c)
    return seen


def _rng(secs):
    """The shortest way of writing a set of classes: 9A-9D rather than four rows."""
    by = defaultdict(list)
    for s in secs: by[s.rstrip("ABCDEFGH")].append(s)
    bits = []
    for g, here in sorted(by.items()):
        letters = sorted(x[len(g):] for x in here)
        run = len(letters) > 1 and all(ord(b) - ord(a) == 1 for a, b in zip(letters, letters[1:]))
        bits.append(f"{g}{letters[0]}-{g}{letters[-1]}" if run and len(letters) > 2
                    else ", ".join(g + l for l in letters))
    return ", ".join(bits)


# ---------------------------------------------------------------- writing
def _sheet(wb, name, headers, widths):
    ws = wb.create_sheet(name)
    ws.append(headers)
    for i, (h, w) in enumerate(zip(headers, widths), 1):
        ws.cell(1, i).font = HEAD; ws.cell(1, i).fill = FILL
        ws.cell(1, i).alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"; ws.row_dimensions[1].height = 30
    return ws


def _yesno(ws, col, last=400):
    dv = DataValidation(type="list", formula1='"yes,no"', allow_blank=True)
    ws.add_data_validation(dv); dv.add(f"{col}2:{col}{last}")


def write_workbook(bands, path, rules=()):
    """bands: {band key: instance dict}. Writes the template, filled from those instances."""
    wb = openpyxl.Workbook(); wb.remove(wb.active)

    ws = wb.create_sheet("Read me")
    ws.column_dimensions["A"].width = 30; ws.column_dimensions["B"].width = 96
    for a, b in [
        ("How to fill this in", ""),
        ("", "One row per subject a class takes, on the Teaching tab. Everything else is short."),
        ("", "A row can cover several classes at once: 9A-9D, or 9A, 9B, or grade 9."),
        ("Worked examples", "from this school's own timetable"),
        ("A normal subject",
         "classes 9A-9D | subject SS | periods 8 | teachers AVR | all at once no | joins blank"),
        ("A class that divides",
         "classes 9A | subject SCI LAB | periods 1 | teachers UPR, REM, TSD | all at once YES. "
         "The class splits three ways and all three teachers are busy that period."),
        ("Two classes that pool",
         "classes 6A | subject DMD | periods 1 | teachers V, A, S | all at once yes | "
         "joins classes 6B. 6A and 6B come together and divide into dance, music and drawing."),
        ("An elective block",
         "classes 11E | subject M/IP/P | periods 7 | teachers DKP, SMT, DAN | all at once yes | "
         "joins classes 11F, 11G."),
        ("Two teachers sharing a subject",
         "classes 12B | subject ENG | periods 6 | teachers ANR, BIN | all at once NO | "
         "split of week 5, 1. One of them takes each lesson, not both."),
        ("A laboratory in a double",
         "classes 11C | subject CS/CHE LAB | periods 2 | teachers SMT, NMV | all at once yes | "
         "double period yes."),
        ("A class that leaves early",
         "On the Classes tab, 11A and 11B have 'day ends after period' 6, because those students "
         "go to outside coaching after the break. Nothing is scheduled for them after that."),
        ("A day of a different length",
         "On the School tab, grades 1-5 have a zero period on Thursday. Give the longest day's "
         "number of periods and say which days are short on the Rules tab."),
        ("If you are unsure", "Write it on the Rules tab in your own words. The system will read "
                              "it back to you and ask if it is not sure what you meant."),
    ]:
        ws.append([a, b])
        if a and not b: ws.cell(ws.max_row, 1).font = Font(bold=True, size=13)
        else: ws.cell(ws.max_row, 1).font = Font(bold=True); ws.cell(ws.max_row, 2).alignment = Alignment(wrap_text=True)

    ws = _sheet(wb, "School", ["band", "days", "periods a day", "break after period",
                               "days with a zero period before the first"], [14, 30, 13, 15, 30])
    for k, sc in bands.items():
        shut0 = {x[0] for x in sc.get("closed", []) if len(x) == 2 and x[1] == 0}
        early = sorted(set(range(len(sc["days"]))) - shut0) if shut0 else []
        ws.append([k, ", ".join(sc["days"]), sc["periods"], sc.get("lunch_after"),
                   ", ".join(sc["days"][d] for d in early) or None])

    ws = _sheet(wb, "Classes", ["class", "band", "day ends after period (blank = full day)"],
                [12, 14, 36])
    for k, sc in bands.items():
        shut = defaultdict(set)
        for x in sc.get("closed", []):
            if len(x) == 3: shut[x[0]].add(x[2])
        for s in sc["sections"]:
            ends = min(shut[s]) if shut.get(s) else None
            ws.append([s, k, ends])

    ws = _sheet(wb, "Teaching",
                ["classes", "subject", "periods a week", "teachers", "all at once?",
                 "split of week", "joins classes", "double period?"],
                [18, 20, 14, 26, 12, 14, 18, 14])
    _yesno(ws, "E"); _yesno(ws, "H")
    for k, sc in bands.items():
        joins, split_in = {}, {}
        for g in sc.get("co_taught", []):
            for (c, sub) in g: joins[c, sub] = [(x, s2) for (x, s2) in g if (x, s2) != (c, sub)]
        for c, m in (sc.get("teacher_load") or {}).items():
            for sub, shares in m.items(): split_in[c, sub] = shares
        doubles = set(sc.get("doubles") or sc.get("assumed", {}).get("double_subjects", []))
        aligned = {(c, g["subject"]) for g in sc.get("block_groups", []) for c in g["sections"]}
        # one row per identical (subject, teachers, flags) across the classes of a grade
        rowsmap = defaultdict(list)
        for s in sc["sections"]:
            for sub, n in sorted(sc["requirements"][s].items()):
                ts = tuple(sc["assignment"].get(s, {}).get(sub, []))
                at_once = len(ts) > 1 and (s, sub) not in split_in
                key = (sub, n, ts, at_once,
                       tuple(sorted(split_in.get((s, sub), {}).items())),
                       tuple(sorted(joins.get((s, sub), []))), sub in doubles,
                       (s, sub) in aligned or not joins.get((s, sub)))
                rowsmap[key].append(s)
        for key, secs in sorted(rowsmap.items(), key=lambda kv: (kv[1][0], kv[0][0])):
            sub, n, ts, at_once, shares, join, dbl, same_time = key
            order = [t for t, _ in shares] or list(ts)
            ws.append([_rng(secs), sub, n, ", ".join(order),
                       "yes" if at_once else "no",
                       ", ".join(str(v) for _, v in shares) if shares else None,
                       ", ".join(c if s2 == sub else f"{c} ({s2})" for c, s2 in join) or None,
                       (None if not join else "yes" if same_time else "no"),
                       "yes" if dbl else None])

    ws = _sheet(wb, "Fixed slots", ["subject or activity", "classes", "day", "period"],
                [24, 22, 12, 10])
    for k, sc in bands.items():
        for lab, secs, d, p in sc.get("fixed", []):
            ws.append([lab, _rng([c for c in secs if c in sc["sections"]]),
                       sc["days"][d], p + 1])

    ws = _sheet(wb, "Rules", ["rule, in your own words", "must or preference"], [78, 20])
    dv = DataValidation(type="list", formula1='"must,preference"', allow_blank=True)
    ws.add_data_validation(dv); dv.add("B2:B200")
    for text, hard in (rules or []):
        ws.append([text, "must" if hard else "preference"])
    wb.save(path); return path


# ---------------------------------------------------------------- reading
def read_workbook(path):
    wb = openpyxl.load_workbook(path, data_only=True)

    def rows(tab):
        ws = wb[tab]; it = ws.iter_rows(values_only=True); next(it, None)
        return [r for r in it if r and any(x is not None and str(x).strip() for x in r)]

    def txt(x): return str(x).strip() if x is not None and str(x).strip() else ""
    def yes(x): return txt(x).lower().startswith("y")

    struct = {}
    for r in rows("School"):
        days = [d.strip() for d in txt(r[1]).split(",")]
        early = [d.strip() for d in txt(r[4] if len(r) > 4 else "").split(",") if d.strip()]
        struct[txt(r[0])] = {
            "days": days, "periods": int(r[2]),
            "lunch_after": int(r[3]) if r[3] is not None else None,
            # a zero period exists only on the days named, so on every other day it is closed
            "shut": [[d, 0] for d, name in enumerate(days) if early and name not in early]}
    band_of, ends = {}, {}
    for r in rows("Classes"):
        band_of[txt(r[0])] = txt(r[1])
        if len(r) > 2 and r[2] is not None: ends[txt(r[0])] = int(r[2])
    known = list(band_of)

    req = defaultdict(dict); assign = defaultdict(dict)
    load = defaultdict(dict); pairs = set(); align = set(); doubles = defaultdict(set)
    for r in rows("Teaching"):
        secs = classes_in(r[0], known); sub = txt(r[1])
        if not secs or not sub: continue
        n = int(r[2]); ts = [t.strip() for t in txt(r[3]).split(",") if t.strip()]
        at_once = yes(r[4] if len(r) > 4 else None)
        shares = [int(x) for x in re.findall(r"\d+", txt(r[5] if len(r) > 5 else ""))]
        join = []                               # [(class, subject)]
        for part in [p.strip() for p in txt(r[6] if len(r) > 6 else "").split(",") if p.strip()]:
            m = re.fullmatch(r"(.+?)\s*\((.+)\)", part)
            label = m.group(2).strip() if m else sub
            for c in classes_in(m.group(1) if m else part, known): join.append((c, label))
        together = txt(r[7] if len(r) > 7 else "")
        together = True if not together else yes(r[7])
        if len(r) > 8 and yes(r[8]):
            for s in secs: doubles[band_of.get(s, "")].add(sub)
        for s in secs:
            req[s][sub] = n; assign[s][sub] = list(ts)
            if len(ts) > 1 and not at_once:
                if len(shares) == len(ts): load[s][sub] = dict(zip(ts, shares))
            for other in join:
                pairs.add(frozenset({(s, sub), other}))
                if together: align.add(frozenset({(s, sub), other}))
    # classes that join a lesson form one group per connected set, and separately the subset of
    # those that must also run at the same time
    def merge(links):
        out = []
        for pair in links:
            s = set(pair); hit = [g for g in out if g & s]
            for g in hit: out.remove(g); s |= g
            out.append(s)
        return out
    groups, aligned_groups = merge(pairs), merge(align)

    fixed = [(txt(r[0]), classes_in(r[1], known), txt(r[2]), int(r[3]))
             for r in rows("Fixed slots") if txt(r[0]) and r[3] is not None]
    rules = [(txt(r[0]), txt(r[1] if len(r) > 1 else "").lower().startswith("must"))
             for r in rows("Rules") if txt(r[0])]

    out = {}
    for band, st in struct.items():
        secs = [s for s, b in band_of.items() if b == band]
        if not secs: continue
        shut = [list(x) for x in st["shut"]]
        shut += [[s, d, p] for s in secs for p in range(ends.get(s, st["periods"]), st["periods"])
                 for d in range(len(st["days"]))]
        co = [[[c, sub] for (c, sub) in sorted(g) if c in secs] for g in groups
              if len([c for (c, _) in g if c in secs]) >= 2]
        out[band] = {
            "name": band, "days": st["days"], "periods": st["periods"],
            "lunch_after": st["lunch_after"],
            "sections": sorted(secs, key=lambda s: (len(s), s)),
            "subjects": sorted({x for s in secs for x in req[s]}),
            "requirements": {s: req[s] for s in secs},
            "assignment": {s: assign[s] for s in secs},
            "teacher_load": {s: load[s] for s in secs if load.get(s)},
            "co_taught": [g for g in co if len(g) >= 2 and all(sub in req[c] for c, sub in g)],
            # classes that join a lesson must run it at the same time, which is what joining
            # means; where their labels differ the lesson is shared but not aligned
            "block_groups": [{"subject": sorted(g)[0][1], "sections": sorted(c for c, _ in g)}
                             for g in aligned_groups
                             if len({sub for _, sub in g}) == 1
                             and len([c for c, _ in g if c in secs]) >= 2
                             and len({req[c].get(sub) for c, sub in g}) == 1],
            "unstaffed": [], "closed": shut,
            "doubles": sorted(doubles.get(band, ())),
            "fixed": [[sub, [c for c in cs if c in secs],
                       st["days"].index(day) if day in st["days"] else 0, p - 1]
                      for sub, cs, day, p in fixed if any(c in secs for c in cs)],
            "assumed": {"from": "the school's filled template"}}
    return out, rules
