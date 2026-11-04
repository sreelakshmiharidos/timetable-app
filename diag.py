import json, time
from school import School
from solve import solve
b = School.load("data/kmbvm_6_8.json")
R = [("max 4 in a row", {"type":"max_consecutive","teacher":"ALL","max":4,"lunch_breaks_run":True,"hard":False}),
     ("subject twice a day", {"type":"max_subject_per_day","subject":"ALL","sections":"ALL","max":2,"hard":True})]
for name, rules in (("6-8 alone, no rules", []), ("6-8 alone, with rules", R)):
    r = solve(b, rules, seconds=120); print(f"{name}: {r['status']} in {r['wall']}s", r.get('conflict') or '', flush=True)
