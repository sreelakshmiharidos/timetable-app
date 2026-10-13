"""System evaluation runs (S3 performance). Prints a table for the report."""
import time, json
from school import School
from solve import solve

sc = School.load("data/kmbvm_9_10.json")
R = {
 "max_consecutive<=4":      {"type":"max_consecutive","teacher":"ALL","max":4,"lunch_breaks_run":False,"hard":True},
 "no_consecutive_subject":  {"type":"no_consecutive_same_subject","subject":"ALL","sections":"ALL","hard":True},
 "subject<=2 per day":      {"type":"max_subject_per_day","subject":"ALL","sections":"ALL","max":2,"hard":True},
 "no games period 1":       {"type":"subject_not_in_periods","subject":"PT","sections":"ALL","periods":[1],"hard":True},
 "labs after period 4":     {"type":"subject_not_in_periods","subject":"SCI LAB","sections":"ALL","periods":[1,2,3,4],"hard":True},
 "gaps<=3 per day":         {"type":"max_gaps_per_day","teacher":"ALL","max":3,"hard":True},
 "midday gap (>=2 lessons)":{"type":"require_midday_gap","teacher":"ALL","periods":[3,4,5,6,7],"min_lessons":2,"hard":True},
}
rows, rules = [], []
for name, f in R.items():
    rules.append((name, f))
    t0 = time.time(); r = solve(sc, rules, seconds=300)
    rows.append((len(rules), name, r["status"], r["wall"], round(time.time()-t0, 1)))
    print(f"{len(rules):2d}  {name:26s} {r['status']:10s} solve {r['wall']:6.2f}s  total {rows[-1][4]:6.1f}s")
json.dump(rows, open("results_timing.json","w"), indent=1)
