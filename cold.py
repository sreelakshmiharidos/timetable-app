"""Cold start: build the school's timetable from the instance alone, with no reference to the
timetable they already have. Bands are solved in the order the committee works in, each against
the teacher time the earlier bands have already used."""
import json, sys, time
from collections import Counter, defaultdict
from school import School
from solve import solve
from rules import rules_for

CAP = int(sys.argv[1]) if len(sys.argv) > 1 else 120
spec = json.load(open("data/kmbvm_school.json"))
bands = {k: School.load(spec["bands"][k]) for k in spec["order"]}


com, grids, report = defaultdict(set), {}, []
for key in spec["order"]:
    b = bands[key]
    sub = b.subset(b.sections, {t: v for t, v in com.items() if t in b.teachers})
    rs = rules_for(b)
    t0 = time.time()
    r = solve(sub, rs, seconds=CAP)
    line = f"{key}: {r['status']} in {r['wall']}s ({len(rs)} rules)"
    if r.get("ok"):
        for t, v in r["busy"].items(): com[t] |= v
        grids[key] = r["grids"]
        if r["broken"]: line += f" | preferences given up: {len(r['broken'])}"
    else:
        line += f" | conflict: {r.get('conflict')}"
    print(line, flush=True); report.append(line)
    if not r.get("ok"): break

if len(grids) == len(spec["order"]):
    json.dump(grids, open("out_cold.json", "w"))
    print("written out_cold.json", flush=True)
