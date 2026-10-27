"""The whole school in one solve: 50 sections across four bands on a common grid. Grades 1-5
open with a zero period on Thursday, the secondary grades never do, so the zero period is
closed for every secondary section."""
import json, sys, time
from school import School
from solve import solve
from rules import rules_for

cap = int(sys.argv[1]) if len(sys.argv) > 1 else 300
spec = json.load(open("data/kmbvm_school.json"))
bands = {k: School.load(spec["bands"][k]) for k in spec["order"]}
periods = max(b.periods for b in bands.values())
d = {"name": "KMBVM Pottore", "days": bands["9_10"].days, "periods": periods,
     "lunch_after": bands["9_10"].lunch_after, "sections": [], "subjects": [],
     "requirements": {}, "assignment": {}, "unstaffed": [], "closed": [],
     "co_taught": [], "block_groups": [], "teacher_load": {}}
for key, b in bands.items():
    # a band with fewer periods keeps its own period numbers and has the surplus slots at the
    # end of the day closed, so every section's model is identical to its own band's
    d["sections"] += b.sections
    d["requirements"].update({s: b.req[s] for s in b.sections})
    d["assignment"].update({s: {k: list(v) for k, v in b.assign.get(s, {}).items()}
                            for s in b.sections})
    d["co_taught"] += [[list(m) for m in g] for g in b.co_taught]
    d["block_groups"] += [{"subject": g["subject"], "sections": g["sections"]}
                          for g in b.block_groups]
    d["teacher_load"].update(dict(b.load))
    for s in b.sections:
        d["closed"] += [[s, dd, p] for p in range(b.periods, periods)
                        for dd in range(len(b.days))]
        d["closed"] += [[s, dd, p] for (dd, p) in b.closed]
d["subjects"] = sorted({x for r in d["requirements"].values() for x in r})
sc = School(d)
print(sc.summary(), flush=True)
rules = rules_for(sc)
t0 = time.time()
r = solve(sc, rules, seconds=cap)
print(f"joint: {r['status']} in {r['wall']}s, total {round(time.time() - t0, 1)}s "
      f"({len(rules)} rules)", flush=True)
if r.get("ok"):
    json.dump({"joint": r["grids"]}, open("out_joint.json", "w"))
    print(f"preferences given up: {len(r['broken'])}", flush=True)
