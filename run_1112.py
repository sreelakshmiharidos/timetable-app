"""v0.6 run: solve grades 11-12 with their real structure, then 9-10 against it."""
import json, time
from school import School
from solve import solve, commitments

sr = School.load("data/kmbvm_11_12.json")
A = json.load(open("data/kmbvm_11_12.json"))["assumed"]
rules = []
for lab, secs in A["blocks"].items():                     # elective blocks, per grade
    for g in ("11", "12"):
        here = sorted(s for s in secs if s.startswith(g))
        if len(here) >= 2:
            rules.append((f"block {lab} {g}", {"type": "parallel_block", "subject": lab,
                                               "sections": here, "hard": True}))
for lab in A["double_subjects"]:                          # every laboratory is a double period
    secs = sorted(s for s in sr.sections if sr.req[s].get(lab, 0) >= 2
                  and sr.req[s][lab] % 2 == 0)
    if secs:
        rules.append((f"double {lab}", {"type": "double_period", "subject": lab,
                                        "sections": secs, "across_break": False, "hard": True}))
rules.append(("max 4 in a row", {"type": "max_consecutive", "teacher": "ALL", "max": 4,
                                 "lunch_breaks_run": False, "hard": True}))
print(f"{len(rules)} structural rules for grades 11-12")
t0 = time.time(); r = solve(sr, rules, seconds=240)
print("11-12:", r["status"], r["wall"], "s", r.get("conflict") or "")
if r.get("ok"):
    com = commitments(sr, r["grids"])
    print("teachers committed by 11-12:", len(com))
    sj = School.load("data/kmbvm_9_10.json")
    jr = [("max 4 in a row", {"type": "max_consecutive", "teacher": "ALL", "max": 4,
                              "lunch_breaks_run": False, "hard": True}),
          ("no subject more than twice a day", {"type": "max_subject_per_day", "subject": "ALL",
                                                "sections": "ALL", "max": 2, "hard": True})]
    shared = set(com) & set(sj.teachers)
    print("teachers shared with 9-10:", len(shared))
    r2 = solve(sj.subset(sj.sections, {t: com[t] for t in shared}), jr, seconds=240)
    print("9-10 against fixed 11-12:", r2["status"], r2["wall"], "s", r2.get("conflict") or "")
    print("total", round(time.time() - t0, 1), "s")
