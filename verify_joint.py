import json, time
from collections import Counter, defaultdict
from school import School
from solve import solve

spec = json.load(open("data/kmbvm_school.json"))
bands = {k: School.load(spec["bands"][k]) for k in spec["order"]}
d = {"name": "KMBVM Pottore", "days": bands["9_10"].days, "periods": bands["9_10"].periods,
     "lunch_after": bands["9_10"].lunch_after, "sections": [], "subjects": [],
     "requirements": {}, "assignment": {}, "unstaffed": []}
for b in bands.values():
    d["sections"] += b.sections
    d["requirements"].update({s: b.req[s] for s in b.sections})
    d["assignment"].update({s: {k: list(v) for k, v in b.assign.get(s, {}).items()} for s in b.sections})
d["subjects"] = sorted({x for r in d["requirements"].values() for x in r})
sc = School(d); print(sc.summary(), flush=True)
R = [("R1", {"type": "max_consecutive", "teacher": "ALL", "max": 4, "lunch_breaks_run": True, "hard": True}),
     ("R2", {"type": "max_subject_per_day", "subject": "ALL", "sections": "ALL", "max": 2, "hard": True}),
     ("R3", {"type": "shared_resource", "subject": "LIB", "sections": "ALL", "max_at_once": 1, "hard": True})]
t0 = time.time(); r = solve(sc, R, seconds=420)
print("joint:", r["status"], r["wall"], "s", r.get("conflict") or "", flush=True)
if r.get("ok"):
    busy = defaultdict(list); bad = []
    for sec, g in r["grids"].items():
        if Counter(x for row in g for x in row if x) != Counter(sc.req[sec]): bad.append(sec)
        for p, row in enumerate(g):
            for dd, sub in enumerate(row):
                for t in (sc.teachers_of(sec, sub) if sub else ()): busy[t, dd, p].append(sec)
    print("sections:", len(r["grids"]), "| count errors:", len(bad),
          "| teacher double-bookings:", sum(1 for v in busy.values() if len(v) > 1), flush=True)
    json.dump({s: g for s, g in list(r["grids"].items())[:1]}, open("sample_out.json", "w"))
print("total", round(time.time()-t0, 1), "s", flush=True)
