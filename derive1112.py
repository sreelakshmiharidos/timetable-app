"""Derive the grades 11-12 instance from the senior grid.

Senior rows differ from 9-10: a blank cell means "the previous lesson continues", which is
how the school writes a double period. Sections are streams, so the curriculum is per section.
Cells naming several teachers are elective blocks shared across sections.

Where the grid is ambiguous we take the most probable reading and record it in `assumed`,
so the assumptions are visible rather than silent.
"""
import json, re, sys
from collections import Counter, defaultdict

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]; PERIODS = 9; LUNCH_AFTER = 4
SUPPORT = {"ASK", "SIG", "SMC", "VIS", "PRC", "REM", "AJK", "NH", "DAN", "BIN", "MNK", "NPT"}
ALIAS = {"MAT": "MTS", "SCILAB": "SCI LAB"}


def norm(x):
    x = re.sub(r"\s+", " ", x.strip().upper())
    return ALIAS.get(x, x)


def load(path):
    rows, assumed = {}, []
    for line in open(path):
        sec, subs, teas = line.rstrip("\n").split("|")
        rows[sec] = ([norm(x) for x in subs.split(",")], [norm(x) for x in teas.split(",")])
    sections = list(rows)
    req, assign, doubles, unstaffed = {}, {}, set(), []
    for sec, (subs, teas) in rows.items():
        c = Counter(); votes = defaultdict(Counter); last = None
        for i, lab in enumerate(subs):
            day_start = i % PERIODS == 0
            if day_start: last = None
            if lab:
                c[lab] += 1; last = lab
                codes = [t for t in teas[i].split("/") if t and t not in SUPPORT]
                if codes: votes[lab][codes[0]] += 1      # most probable: the first real code
            elif last and "LAB" in last:
                # the school writes a laboratory as one cell plus a blank: a double period.
                # any other blank is a free period, not a continuation.
                c[last] += 1; doubles.add(last); last = None
            else:
                last = None
        req[sec] = dict(c)
        assign[sec] = {lab: v.most_common(1)[0][0] for lab, v in votes.items()}
        for lab in c:
            if lab not in assign[sec]:
                assign[sec][lab] = f"X-{lab[:6]}"         # invented teacher, flagged below
                unstaffed.append([sec, lab])
    # A block cell names several teachers (one per group). Giving every section the same
    # teacher would make the block unschedulable, so distinct codes are shared out across the
    # sections that take it, in order. This is an assumption; the grid does not say who takes whom.
    pool = defaultdict(list)
    for sec, (subs, teas) in rows.items():
        for lab, t in zip(subs, teas):
            if lab and "/" in lab:
                for code in t.split("/"):       # block cells may name support staff too
                    if code and code not in pool[lab]:
                        pool[lab].append(code)
    shared_out = []
    for lab, codes in pool.items():
        takers = sorted(s for s in sections if lab in req[s])
        if len(takers) >= 2:
            while len(codes) < len(takers):      # the grid names fewer teachers than groups;
                codes.append(f"X-{lab[:6]}-{len(codes)+1}")   # assume one more teacher per group
            for i, sec in enumerate(takers):
                assign[sec][lab] = codes[i]
            shared_out.append(lab)

    # elective blocks: the same label in the same slot across three or more sections
    blocks = defaultdict(set)
    for i in range(DAYS.__len__() * PERIODS):
        here = defaultdict(list)
        for sec, (subs, _) in rows.items():
            if subs[i]: here[subs[i]].append(sec)
        for lab, secs in here.items():
            if len(secs) >= 3 and "/" in lab and "LAB" not in lab.split("/")[0]:
                blocks[lab] |= set(secs)
    school = {
        "name": "KMBVM Pottore (grades 11 and 12)", "days": DAYS, "periods": PERIODS,
        "lunch_after": LUNCH_AFTER, "sections": sections,
        "subjects": sorted({s for r in req.values() for s in r}),
        "requirements": req, "assignment": assign, "unstaffed": unstaffed,
        "assumed": {
            "blank_cell": "a blank cell continues the previous lesson, i.e. a double period",
            "teacher_for_group_cell": "the first named teacher is taken as the one scheduled",
            "invented_teachers": sorted({assign[s][l] for s, l in unstaffed}),
            "double_subjects": sorted(doubles),
            "blocks": {k: sorted(v) for k, v in blocks.items()},
            "teachers_shared_out": sorted(shared_out),
        }}
    return school


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data_raw/g1112.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "data/kmbvm_11_12.json"
    sc = load(src); json.dump(sc, open(out, "w"), indent=1)
    print(len(sc["sections"]), "sections,", len(sc["subjects"]), "subjects,",
          len({t for d in sc["assignment"].values() for t in d.values()}), "teachers")
    print("slots used per section:", {s: sum(sc["requirements"][s].values()) for s in sc["sections"]})
    print("subjects seen as doubles:", sc["assumed"]["double_subjects"][:12])
    print("blocks:", {k: v for k, v in list(sc["assumed"]["blocks"].items())[:6]})
    print("invented teachers:", len(sc["assumed"]["invented_teachers"]))
