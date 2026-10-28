"""Build one instance per band from the school's own workbook.

Three different things look alike in the grid, and telling them apart is the data model:

  * **An in-section split.** One cell, several teacher names, one section: the class divides
    and goes to several rooms at once (`SCI LAB` under `UPR/REM/TSD` is physics, chemistry and
    biology in three rooms). Every named teacher is busy for every lesson of that pair.
  * **A regroup across sections.** The same label with the same teachers in the same slot in
    two or more sections: those sections' students regroup into activity groups (`DMD` is
    dance, music and drawing for two classes at once under `V/A/S`; `M/IP/P` is maths,
    informatics and psychology for three of 11E-11G). The sections must run it simultaneously,
    and the teachers are occupied once, not once per section.
  * **A shared load.** A plain subject with one teacher per cell but two different teachers over
    the week (12B English: five periods with ANR, one with BIN). One of them takes each lesson,
    and each teacher's share of the week is recorded.

Also recorded in `assumed`: in grades 11-12 a blank after a laboratory continues it (a double
period), any other blank is free; the break falls after period 5.
"""
import csv, json, os, re
from collections import Counter, defaultdict

RAW = {"11_12": "data_raw/g1112.csv", "9_10": "data_raw/g910.csv",
       "6_8": "data_raw/g678.csv", "1_5": "data_raw/g15.csv"}
# how many periods each day holds. Grades 1-5 open with a zero period on Thursday only, so
# that day has ten and the others nine; the missing zero periods are closed slots.
DAY_PERIODS = {"1_5": [9, 9, 9, 10, 9]}


def read_csv(path):
    """The grid as extracted from the workbook: one line per section,
    `section|subject cells|teacher cells`, cells in reading order across the week."""
    rows, n = {}, 0
    for line in open(path):
        line = line.rstrip("\n")
        if "|" not in line: continue
        sec, rest = line.split("|", 1)
        subs, teas = rest.split("|") if "|" in rest else (rest, "")
        subs = next(csv.reader([subs]))
        teas = next(csv.reader([teas])) if teas else [""] * len(subs)
        n = max(n, len(subs), len(teas))
        rows[sec] = (subs, teas)
    for sec, (subs, teas) in rows.items():
        rows[sec] = (subs + [""] * (n - len(subs)), teas + [""] * (n - len(teas)))
    return rows, n

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]; LUNCH_AFTER = 6   # Jyothy Tr: the break falls after six periods
ALIAS = {"MAT": "MTS", "SCILAB": "SCI LAB", "ATR/CRAFT": "ART/CRAFT", "KVLAB/YOGA": "KV LAB/YOGA"}
BANDS = {"11_12": "class 11& 12", "9_10": "CLASS 9 AND 10", "6_8": "class 6-8"}


def norm(x):
    x = re.sub(r"\s+", " ", str(x).strip().upper())
    return ALIAS.get(x, x)


def components(sets):
    """Merge overlapping section sets; disjoint ones stay apart (DMD pairs 8A+8B and 7A+7B are
    two separate regroups of the same label, not one block of four)."""
    out = []
    for s in sets:
        s = set(s); hit = [g for g in out if g & s]
        for g in hit: out.remove(g); s |= g
        out.append(s)
    return out


def layout(day_periods):
    """Reading order of the grid to (day, period), and the slots that do not exist. A short day
    is taken to start one period later, so period numbers line up across the week."""
    periods = max(day_periods)
    at, closed = [], set()
    for d, k in enumerate(day_periods):
        off = periods - k
        at += [(d, off + p) for p in range(k)]
        closed |= {(d, p) for p in range(off)}
    return at, periods, closed


def build(source, name, doubles_from_blank, day_periods=None):
    rows, n = read_csv(source)
    at, periods, closed = layout(day_periods or [n // len(DAYS)] * len(DAYS))
    assert len(at) == n, (len(at), n)
    where = dict(enumerate(at))
    grid, shut = {}, {}                        # section -> (labels, teacher cells); section -> slots
    for sec, (subs, teas) in rows.items():
        subs = [norm(x) for x in subs]; teas = [norm(x) for x in teas]
        # A section whose day ends early: periods empty on every day of the week, counting back
        # from the end of the day, are not free periods but slots the section does not have.
        # 11A and 11B are empty in periods 7, 8 and 9 all week because those students leave for
        # outside coaching after the break. Computed before laboratory doubles are expanded, so
        # that a blank following a laboratory in the last period they attend is read as going
        # home rather than as the second half of a double.
        gone = set()
        for p in range(periods - 1, -1, -1):
            cells_p = [subs[i] for i, (dd, pp) in where.items() if pp == p]
            if cells_p and not any(cells_p): gone |= {(dd, p) for dd in range(len(DAYS))}
            else: break
        shut[sec] = {(d, p) for (d, p) in gone if (d, p) in set(at)}
        if doubles_from_blank:
            # a blank after a laboratory is the second half of that double period: the class
            # and its teachers are still there, so fill it in before anything else is measured
            last = None
            for i in range(n):
                if where[i][1] == 0 or (i and where[i][0] != where[i - 1][0]): last = None
                if subs[i]: last = i
                elif last is not None and "LAB" in subs[last] and where[i] not in shut[sec]:
                    subs[i], teas[i] = subs[last], teas[last]; last = None
                else: last = None
        grid[sec] = (subs, teas)

    req, cells, slots = {}, defaultdict(list), defaultdict(set)
    slots_by = defaultdict(lambda: defaultdict(set))   # subject -> section -> slots
    doubles = set()
    for sec, (subs, teas) in grid.items():
        c = Counter(); prev = None
        for i, lab in enumerate(subs):
            if i and where[i][0] != where[i - 1][0]: prev = None
            if not lab: prev = None; continue
            c[lab] += 1
            cells[sec, lab].append([t for t in teas[i].split("/") if t])
            slots[sec, lab].add(where[i]); slots_by[lab][sec].add(where[i])
            if prev == lab and doubles_from_blank and "LAB" in lab: doubles.add(lab)
            prev = lab
        req[sec] = dict(c)

    # A regroup: the same teacher code appears in two sections in the same period. Either the
    # two groups are really one class (11A's biology students sit in 11E's biology lesson; 10A,
    # 10B and 10C take their languages together), or the cell is a mistake. The school's labels
    # settle which: groups that share a subject name are merged, the rest are reported.
    def tokens(lab):
        """The subjects a cell names. A laboratory and its subject are the same subject, so
        `BIO LAB` and `BIO` match: that is how 11A's biology group joins 11E's."""
        out = set()
        for x in lab.split("/"):
            x = x.strip()
            if not x: continue
            out.add(x); out.add(re.sub(r"\s*LAB$", "", x).strip() or x)
        return out

    pairs, suspect = defaultdict(int), []
    for i in range(n):
        live = []
        for sec, (subs, teas) in grid.items():
            if subs[i]: live.append((sec, subs[i], {t for t in teas[i].split("/") if t}))
        for a in range(len(live)):
            for b in range(a + 1, len(live)):
                (s1, l1, t1), (s2, l2, t2) = live[a], live[b]
                if not (t1 & t2): continue
                if tokens(l1) & tokens(l2): pairs[(s1, l1), (s2, l2)] += 1
                else: suspect.append((sorted(t1 & t2)[0], where[i][0] + 1, where[i][1] + 1,
                                      (s1, l1), (s2, l2)))
    groups = [{"members": sorted(g)} for g in components([[a, b] for a, b in pairs])]
    for g in groups:
        labs = {lab for _, lab in g["members"]}
        g["subject"] = next(iter(labs)) if len(labs) == 1 else "+".join(sorted(labs))
    in_group = {m for g in groups for m in g["members"]}

    named = any(t for _, teas in grid.values() for t in teas)
    if not named:
        # The primary extract has no teacher codes. A subject that never runs in two sections at
        # once is one specialist serving the whole band (dance, music, drawing, library); every
        # other subject is the section's own class teacher.
        at_once = set()
        for i in range(n):
            seen_lab = Counter(subs[i] for subs, _ in grid.values() if subs[i])
            at_once |= {lab for lab, k in seen_lab.items() if k > 1}
        for sec, (subs, teas) in grid.items():
            for i, lab in enumerate(subs):
                if lab: teas[i] = f"{sec}-CT" if lab in at_once else f"SP-{lab}"
        cells = defaultdict(list); 
        for sec, (subs, teas) in grid.items():
            for i, lab in enumerate(subs):
                if lab: cells[sec, lab].append([teas[i]])

    elsewhere = Counter()                      # (teacher, label) -> lessons anywhere in the band
    for (sec, lab), per_cell in cells.items():
        for cell in per_cell:
            for t in cell: elsewhere[t, lab] += 1

    assign, load = {}, defaultdict(dict)
    for sec in grid:
        assign[sec] = {}
        for lab in req[sec]:
            per_cell = cells[sec, lab]
            pool = sorted({t for cell in per_cell for t in cell})
            assign[sec][lab] = pool
            # one teacher per lesson, so a plain subject with two teachers over the week is a
            # shared load rather than a split class
            if (sec, lab) not in in_group and not any(len(c) > 1 for c in per_cell) and len(pool) > 1:
                share = Counter(t for cell in per_cell for t in cell)
                short = req[sec][lab] - sum(share.values())
                if short > 0: share[share.most_common(1)[0][0]] += short
                # A single appearance by someone who teaches this subject nowhere else is a cell
                # written in the wrong row, not a shared load: PMN takes one English period in
                # 6D and no other English in the school, and she teaches maths. The lesson goes
                # to the teacher who takes the rest, and the cell is reported.
                main = share.most_common(1)[0][0]
                for t, k in list(share.items()):
                    if t == main or k > 1: continue
                    if elsewhere[t, lab] > k: continue
                    suspect.append((t, "-", "-", (sec, lab), ("teaches " + lab + " nowhere else",)))
                    share[main] += k; del share[t]
                    assign[sec][lab] = [x for x in assign[sec][lab] if x != t]
                if len(share) > 1: load[sec][lab] = dict(share)
    # sections only run a lesson at the same time when they need it the same number of times
    # Sections are tied to the same period only where their own grid never separates them:
    # ANR teaches 12B and 12E English together five times a week and apart once, so those two
    # share a teacher but are not one block.
    aligned = [{"subject": g["subject"], "sections": sorted(c for c, _ in g["members"])}
               for g in groups
               if len({lab for _, lab in g["members"]}) == 1
               and len({frozenset(slots[m]) for m in g["members"]}) == 1]

    # Slots the school never moves. Jyothy Tr: the activity periods have to be fixed because
    # outside teachers come in; R3 is common across all of grade 9, whose classes pool and split
    # into Malayalam, Hindi and Sanskrit; PF is a performance for grades 1-5 together in the main
    # auditorium. The grid shows them as a subject that every section taking it takes at exactly
    # the same small set of slots.
    fixed = []
    for lab, m in slots_by.items():
        if len(m) < 3: continue
        here = {frozenset(v) for v in m.values()}
        if len(here) == 1 and len(next(iter(here))) <= 4:
            for (d, p) in sorted(next(iter(here))):
                fixed.append([lab, sorted(m), d, p])

    return {"name": name, "days": DAYS, "periods": periods, "lunch_after": LUNCH_AFTER,
            "sections": sorted(req, key=lambda s: (len(s), s)),
            "subjects": sorted({x for r in req.values() for x in r}),
            "requirements": req, "assignment": assign, "unstaffed": [],
            "fixed": fixed,
            "closed": (sorted(map(list, closed))
                       + sorted([c, d, p] for c in shut for (d, p) in shut[c])),
            "teacher_load": {s: v for s, v in load.items() if v},
            "co_taught": [[list(m) for m in g["members"]] for g in groups],
            "block_groups": aligned,
            "assumed": {"break_after_period": LUNCH_AFTER,
                        "teachers_named_in_source": bool(named),
                        "blank_after_lab_is_a_double": bool(doubles_from_blank),
                        "double_subjects": sorted(doubles),
                        "regroups": len(groups), "regroups_aligned": len(aligned),
                        "fixed_slots": len(fixed),
                        "short_day_sections": {c: len(v) for c, v in shut.items() if v},
                        "suspect_cells": [list(map(str, x)) for x in suspect],
                        "split_cells_book_every_teacher": True,
                        "shared_load_pairs": sum(len(v) for v in load.values())}}


if __name__ == "__main__":
    for key, src in RAW.items():
        sc = build(src, f"KMBVM Pottore (grades {key.replace('_', '-')})",
                   doubles_from_blank=(key == "11_12"),
                   day_periods=DAY_PERIODS.get(key))
        json.dump(sc, open(f"data/kmbvm_{key}.json", "w"), indent=1)
        a = sc["assumed"]
        nt = len({t for d in sc["assignment"].values() for ts in d.values() for t in ts})
        print(f"{key}: {len(sc['sections'])} sections, {len(sc['subjects'])} subjects, {nt} teachers, "
              f"{a['regroups']} regroups ({a['regroups_aligned']} aligned), "
              f"{len(a['suspect_cells'])} suspect cells, "
              f"{a['shared_load_pairs']} shared-load pairs")
