"""Cold start from the school's filled template, rather than from its finished timetable.

This is the round trip the project promises a school: hand over the template, get a timetable
back. The template here was filled by reverse-engineering their own timetable, so it tests
whether the format can carry everything the school's timetable contains, not whether a teacher
fills it correctly. That second question needs a teacher.
"""
import json, sys, time
from collections import Counter, defaultdict
import template
from school import School
from solve import solve
from rules import rules_for

cap = int(sys.argv[1]) if len(sys.argv) > 1 else 120
spec = json.load(open("data/kmbvm_school.json"))
bands = {k: json.load(open(v)) for k, v in spec["bands"].items()}
path = template.write_workbook(bands, "data/kmbvm_template_filled.xlsx")
back, sheet_rules = template.read_workbook(path)
print(f"template: {path}, {len(back)} bands, {len(sheet_rules)} rules written in prose", flush=True)

com, grids = defaultdict(set), {}
for key in spec["order"]:
    b = School(back[key])
    sub = b.subset(b.sections, {t: v for t, v in com.items() if t in b.teachers})
    rs = rules_for(b)
    r = solve(sub, rs, seconds=cap)
    line = f"{key}: {r['status']} in {r['wall']}s ({len(rs)} rules)"
    if r.get("ok"):
        for t, v in r["busy"].items(): com[t] |= v
        grids[key] = r["grids"]
        bad = [s for s, g in r["grids"].items()
               if Counter(x for row in g for x in row if x) != Counter(b.req[s])]
        line += f" | wrong lesson counts: {len(bad)}"
        if r["broken"]: line += f" | preferences given up: {len(r['broken'])}"
    else:
        line += f" | conflict: {r.get('conflict')}"
    print(line, flush=True)
    if not r.get("ok"): break
if len(grids) == len(spec["order"]):
    json.dump(grids, open("out_template.json", "w"))
    print("written out_template.json", flush=True)
