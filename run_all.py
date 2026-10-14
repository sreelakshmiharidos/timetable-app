"""v0.6: solve the secondary school band by band, in the order the committee uses."""
import json, time
from school import School
from solve import solve, commitments

ORDER = ["11_12", "9_10", "6_8"]
com, total = {}, 0.0
for key in ORDER:
    raw = json.load(open(f"data/kmbvm_{key}.json")); sc = School.load(f"data/kmbvm_{key}.json")
    rules = [("max 4 in a row", {"type": "max_consecutive", "teacher": "ALL", "max": 4,
                                 "lunch_breaks_run": True, "hard": True})]
    for lab, secs in raw["assumed"]["blocks"].items():                 # elective / split blocks
        for g in {s[:-1] for s in secs}:
            here = sorted(s for s in secs if s[:-1] == g)
            if len(here) >= 2 and len({sc.req[s].get(lab) for s in here}) == 1:
                rules.append((f"block {lab} {g}", {"type": "parallel_block", "subject": lab,
                                                   "sections": here, "hard": True}))
    for lab in raw["assumed"]["double_subjects"]:                      # laboratories as doubles
        secs = sorted(s for s in sc.sections if sc.req[s].get(lab, 0) % 2 == 0 and sc.req[s].get(lab, 0) >= 2)
        if secs:
            rules.append((f"double {lab}", {"type": "double_period", "subject": lab,
                                            "sections": secs, "across_break": False, "hard": True}))
    mine = {t: v for t, v in com.items() if t in sc.teachers}
    t0 = time.time()
    r = solve(sc.subset(sc.sections, mine), rules, seconds=240)
    total += time.time() - t0
    print(f"{key}: {len(rules)} rules, {len(mine)} teachers already committed -> {r['status']} "
          f"in {r['wall']}s {r.get('conflict') or ''}")
    if not r.get("ok"): break
    for t, slots in commitments(sc, r["grids"]).items():
        com.setdefault(t, set()).update(slots)
print(f"whole secondary school in {round(total,1)}s; {len(com)} teachers scheduled")
