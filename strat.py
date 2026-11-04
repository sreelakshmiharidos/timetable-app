import json, sys, time
from collections import Counter, defaultdict
from school import School
from solve import solve, commitments
import hints as H

mode, cap = sys.argv[1], int(sys.argv[2])
spec = json.load(open("data/kmbvm_school.json"))
bands = {k: School.load(spec["bands"][k]) for k in spec["order"]}
SOFT = ("max 4 in a row", {"type":"max_consecutive","teacher":"ALL","max":4,"lunch_breaks_run":True,"hard":False})
HARD = ("subject twice a day", {"type":"max_subject_per_day","subject":"ALL","sections":"ALL","max":2,"hard":True})

def joint(rules, use_hint):
    d = {"name":"KMBVM","days":bands["9_10"].days,"periods":bands["9_10"].periods,
         "lunch_after":bands["9_10"].lunch_after,"sections":[],"subjects":[],"requirements":{},
         "assignment":{},"unstaffed":[],"block_groups":[]}
    for b in bands.values():
        d["sections"] += b.sections
        d["requirements"].update({s: b.req[s] for s in b.sections})
        d["assignment"].update({s: {k: list(v) for k, v in b.assign.get(s, {}).items()} for s in b.sections})
        d["block_groups"] += [{"subject":g["subject"],"sections":g["sections"]} for g in b.block_groups]
    d["subjects"] = sorted({x for r in d["requirements"].values() for x in r})
    sc = School(d)
    hint = {}
    if use_hint:
        for k, b in bands.items(): hint.update(H.load(k, b))
    t0 = time.time(); r = solve(sc, rules, seconds=cap, hints=hint or None)
    print(f"[{mode}] {r['status']} in {r['wall']}s, total {round(time.time()-t0,1)}s", flush=True)
    if r.get("ok"):
        bad = [s for s, g in r["grids"].items()
               if Counter(x for row in g for x in row if x) != Counter(sc.req[s])]
        print(f"[{mode}] sections {len(r['grids'])}, count errors {len(bad)}", flush=True)
        json.dump(r["grids"], open(f"out_{mode}.json","w"))

def sequence(order, use_hint, rules):
    com = {}
    for key in order:
        b = bands[key]
        hint = H.load(key, b) if use_hint else None
        t0 = time.time()
        r = solve(b.subset(b.sections, {t: v for t, v in com.items() if t in b.teachers}),
                  rules, seconds=cap, hints=hint)
        print(f"[{mode}] {key}: {r['status']} in {r['wall']}s", flush=True)
        if not r.get("ok"): return
        for t, s in commitments(b, r["grids"]).items(): com.setdefault(t, set()).update(s)
    print(f"[{mode}] all bands built", flush=True)

if mode == "joint_base":      joint([], True)
elif mode == "joint_soft":    joint([SOFT], True)
elif mode == "joint_full":    joint([SOFT, HARD], True)
elif mode == "seq_hint":      sequence(["11_12","6_8","9_10"], True, [SOFT, HARD])
elif mode == "seq_tight":     sequence(["6_8","11_12","9_10"], False, [SOFT, HARD])
