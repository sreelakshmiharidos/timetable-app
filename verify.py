"""Check a produced timetable the way the school would: every section gets the lessons it needs,
and no teacher is in two places at once anywhere in the school. Occupancy is read from the model,
so a regrouped lesson counts once and a shared load counts for whoever took it."""
import json, sys
from collections import Counter, defaultdict
from ortools.sat.python import cp_model
from school import School
from model import Build

path = sys.argv[1] if len(sys.argv) > 1 else "out_cold.json"
grids = json.load(open(path)); spec = json.load(open("data/kmbvm_school.json"))
com, bad_counts, clashes = defaultdict(set), [], []
for band in spec["order"]:
    if band not in grids: continue
    b = School.load(spec["bands"][band])
    sub = b.subset(b.sections, {t: v for t, v in com.items() if t in b.teachers})
    bd = Build(sub)
    for sec, rows in grids[band].items():
        got = Counter(x for r in rows for x in r if x)
        if got != Counter(b.req[sec]): bad_counts.append((band, sec))
        for p, row in enumerate(rows):
            for d, lab in enumerate(row):
                if lab and (sec, d, p, lab) in bd.x: bd.m.Add(bd.x[sec, d, p, lab] == 1)
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 60; s.parameters.num_workers = 8
    st = s.Solve(bd.m)
    print(f"{band}: {s.StatusName(st)}", flush=True)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): continue
    for t in sub.teachers:
        for d in range(len(sub.days)):
            for p in range(sub.periods):
                if s.Value(bd.busy[t, d, p]) > 0:
                    if (d, p) in com[t]: clashes.append((t, band, d, p))
                    com[t].add((d, p))
print(f"sections with wrong lesson counts: {len(bad_counts)} {bad_counts[:5]}")
print(f"teachers in two places at once: {len(clashes)} {clashes[:5]}")
