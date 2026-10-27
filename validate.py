"""Is the school's own timetable feasible in our model? Fix every lesson to where they put it."""
import json
from ortools.sat.python import cp_model
from school import School
from model import Build
import hints as H
from derive_all import RAW, read_csv, norm, layout, DAY_PERIODS
spec=json.load(open("data/kmbvm_school.json"))
bands={k:School.load(v) for k,v in spec["bands"].items()}
for k,b in bands.items():
    at,_,_=layout(DAY_PERIODS.get(k, [b.periods]*len(b.days)))
    rows,n=read_csv(RAW[k])
    h={(sec,)+at[i]: norm(lab) for sec,(subs,_) in rows.items() if sec in b.sections
       for i,lab in enumerate(subs) if norm(lab)}
    bd=Build(b)
    placed=0
    for (sec,d,p),sub in h.items():
        if (sec,d,p,sub) in bd.x: bd.m.Add(bd.x[sec,d,p,sub]==1); placed+=1
    s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=60; s.parameters.num_workers=8
    st=s.Solve(bd.m)
    print(f"{k}: their timetable fixed in {placed} cells -> {s.StatusName(st)}", flush=True)
