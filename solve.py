"""Solve, explain conflicts, and print. v0.2"""
from ortools.sat.python import cp_model
from model import Build


def _solve(school, rules, seconds=60, hard_labels=None, workers=8):
    b = Build(school)
    soft = []
    for label, f in rules:
        on = b.add_rule(label, f)
        if not f.get("hard", True): soft.append(on)
    if soft: b.m.Maximize(sum(soft))
    hard = [b.switch[l][0] for l in (hard_labels if hard_labels is not None
                                     else [l for l, f in rules if f.get("hard", True)])]
    if hard: b.m.AddAssumptions(hard)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = seconds
    s.parameters.num_workers = workers
    st = s.Solve(b.m)
    return st, s, b


def explain_conflict(school, rules, seconds=30):
    core = [l for l, f in rules if f.get("hard", True)]
    st, s, b = _solve(school, rules, seconds, hard_labels=core)
    if st == cp_model.INFEASIBLE:
        idx = set(s.SufficientAssumptionsForInfeasibility())
        core = [l for l in core if b.switch[l][0].Index() in idx] or core
    base, *_ = _solve(school, rules, seconds, hard_labels=[])
    if base not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None                        # the school data itself does not fit
    for l in list(core):
        trial = [c for c in core if c != l]
        st2, *_ = _solve(school, rules, seconds, hard_labels=trial)
        if st2 == cp_model.INFEASIBLE: core = trial
    return core


def solve(school, rules, seconds=60):
    st, s, b = _solve(school, rules, seconds)
    out = {"status": s.StatusName(st), "wall": round(s.WallTime(), 2)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        grids = {}
        for c in school.sections:
            grids[c] = [[next((sub for sub in school.req[c]
                               if s.Value(b.x[c, d, p, sub])), None)
                         for d in range(len(school.days))] for p in range(school.periods)]
        out |= {"ok": True, "grids": grids,
                "broken": [l for l, (on, f) in b.switch.items()
                           if not f.get("hard", True) and not s.Value(on)]}
    else:
        out |= {"ok": False, "conflict": explain_conflict(school, rules) if st == cp_model.INFEASIBLE else None}
    return out


def print_grid(school, grids, section):
    g = grids[section]
    print(f"\n=== {section} ===")
    print("     " + "".join(f"{d:<14}" for d in school.days))
    for p, row in enumerate(g):
        cells = "".join(f"{(x or 'free'):<14}" for x in row)
        print(f"P{p+1:<4}{cells}")
