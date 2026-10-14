"""Build one instance per band from the school's own workbook.

Decisions, all recorded in the instance under `assumed`:
  * every teacher named in a cell is busy in that period (a split class means several
    teachers are occupied, e.g. SCI LAB under UPR/REM/TSD is physics, chemistry and biology
    in three rooms);
  * in grades 11-12 a blank cell after a laboratory continues it (a double period), any other
    blank is a free period;
  * the break falls after period 5.
"""
import json, re, sys
from collections import Counter, defaultdict
from parse_xl import read_band

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]; LUNCH_AFTER = 5
ALIAS = {"MAT": "MTS", "SCILAB": "SCI LAB", "ATR/CRAFT": "ART/CRAFT", "KVLAB/YOGA": "KV LAB/YOGA"}
BANDS = {"11_12": "class 11& 12", "9_10": "CLASS 9 AND 10", "6_8": "class 6-8"}


def norm(x):
    x = re.sub(r"\s+", " ", str(x).strip().upper())
    return ALIAS.get(x, x)


def build(path, sheet, name, doubles_from_blank):
    rows, n = read_band(path, sheet)
    periods = n // len(DAYS)
    req, assign, doubles, blocks = {}, {}, set(), defaultdict(set)
    for sec, (subs, teas) in rows.items():
        subs = [norm(x) for x in subs]; teas = [norm(x) for x in teas]
        c = Counter(); who = defaultdict(Counter); last = None
        for i, lab in enumerate(subs):
            if i % periods == 0: last = None
            if lab:
                c[lab] += 1; last = lab
                for t in [x for x in teas[i].split("/") if x]:
                    who[lab][t] += 1
            elif last and doubles_from_blank and "LAB" in last:
                c[last] += 1; doubles.add(last); last = None
            else:
                last = None
        req[sec] = dict(c)
        # keep every teacher that takes this subject for this section
        assign[sec] = {lab: sorted(v) for lab, v in who.items()}
    for i in range(n):
        here = defaultdict(list)
        for sec, (subs, _) in rows.items():
            lab = norm(subs[i])
            if lab: here[lab].append(sec)
        for lab, secs in here.items():
            if len(secs) >= 2 and "/" in lab:
                blocks[lab] |= set(secs)
    # Two different things look alike in the grid. Inside one section, several teachers in a
    # cell means the class splits and all of them are busy (SCI LAB under UPR/REM/TSD: physics,
    # chemistry and biology in three rooms). Across sections, the same block label in the same
    # slot means the sections regroup, and each teacher takes one group, not all of them.
    shared_out = []
    for lab, secs in blocks.items():
        takers = sorted(secs)
        pool = sorted({t for s in takers for t in assign[s].get(lab, [])})
        if len(takers) >= 2 and pool:
            while len(pool) < len(takers):
                pool.append(f"X-{lab[:6]}-{len(pool)+1}")
            for i, sec in enumerate(takers):
                assign[sec][lab] = [pool[i]]
            shared_out.append(lab)

    return {"name": name, "days": DAYS, "periods": periods, "lunch_after": LUNCH_AFTER,
            "sections": sorted(req, key=lambda s: (len(s), s)), "subjects": sorted({x for r in req.values() for x in r}),
            "requirements": req, "assignment": assign, "unstaffed": [],
            "assumed": {"break_after_period": LUNCH_AFTER,
                        "all_named_teachers_busy": True,
                        "blank_after_lab_is_a_double": bool(doubles_from_blank),
                        "double_subjects": sorted(doubles),
                        "blocks": {k: sorted(v) for k, v in blocks.items()},
                        "block_teachers_shared_out": sorted(shared_out),
                        "split_cells_book_every_teacher": True}}


if __name__ == "__main__":
    src = "../xl/classes.xlsx"
    for key, sheet in BANDS.items():
        sc = build(src, sheet, f"KMBVM Pottore (grades {key.replace('_', ' and ')})",
                   doubles_from_blank=(key == "11_12"))
        json.dump(sc, open(f"data/kmbvm_{key}.json", "w"), indent=1)
        nt = len({t for d in sc["assignment"].values() for ts in d.values() for t in ts})
        pairs = sum(len(d) for d in sc["assignment"].values())
        multi = sum(1 for d in sc["assignment"].values() for ts in d.values() if len(ts) > 1)
        print(f"{key}: {len(sc['sections'])} sections, {len(sc['subjects'])} subjects, {nt} teachers, "
              f"{pairs} section-subject pairs ({multi} taught by more than one), "
              f"{len(sc['assumed']['blocks'])} blocks")
