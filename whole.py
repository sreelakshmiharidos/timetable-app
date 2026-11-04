"""Build the whole secondary school, bands in order."""
import json, sys, time
from collections import Counter, defaultdict
from school import School
from solve import solve, commitments

CAP = int(sys.argv[1]) if len(sys.argv) > 1 else 180
spec = json.load(open("data/kmbvm_school.json"))
bands = {k: School.load(spec["bands"][k]) for k in spec["order"]}
RULES = [("max 4 in a row", {"type": "max_consecutive", "teacher": "ALL", "max": 4,
                             "lunch_breaks_run": True, "hard": False}),
         ("subject twice a day", {"type": "max_subject_per_day", "subject": "ALL",
                                  "sections": "ALL", "max": 2, "hard": True})]
com, grids = {}, {}
for key, b in bands.items():
    t0 = time.time()
    r = solve(b.subset(b.sections, {t: v for t, v in com.items() if t in b.teachers}),
              RULES, seconds=CAP)
    print(f"{key}: {r['status']} in {r['wall']}s", r.get("conflict") or "", flush=True)
    if not r.get("ok"): sys.exit(1)
    grids[key] = r["grids"]
    for t, s in commitments(b, r["grids"]).items(): com.setdefault(t, set()).update(s)
busy = defaultdict(list); bad = []
for key, g in grids.items():
    b = bands[key]
    for sec, grid in g.items():
        if Counter(x for row in grid for x in row if x) != Counter(b.req[sec]): bad.append(sec)
        for p, row in enumerate(grid):
            for d, sub in enumerate(row):
                for t in (b.teachers_of(sec, sub) if sub else ()):
                    busy[t, d, p].append(f"{sec}:{sub}")
clash = {k: v for k, v in busy.items() if len(set(v)) > 1}
print("sections:", sum(len(g) for g in grids.values()), "| count errors:", len(bad),
      "| teacher double-bookings:", len(clash), list(clash.items())[:2], flush=True)
json.dump({k: v for k, v in grids.items()}, open("whole_out.json", "w"))
