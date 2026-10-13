"""Layer 2 (v0.2): the translator. Turns validated constraint forms into CP-SAT
constraints over a School. Every user rule is guarded by its own switch literal so
that conflicts can be extracted and preferences can be dropped."""
from ortools.sat.python import cp_model

RULE_TYPES = {
    "max_consecutive":          ["teacher", "max", "lunch_breaks_run"],
    "max_per_day":              ["teacher", "max"],
    "teacher_unavailable":      ["teacher", "days", "periods"],
    "subject_not_in_periods":   ["subject", "sections", "periods"],
    "max_subject_per_day":      ["subject", "sections", "max"],
    "no_consecutive_same_subject": ["subject", "sections"],
    "max_gaps_per_day":         ["teacher", "max"],
    "require_midday_gap":       ["teacher", "periods", "min_lessons"],
    "fixed_slot":               ["subject", "sections", "days", "periods"],
    "double_period":            ["subject", "sections", "across_break"],
}


class Build:
    def __init__(self, school):
        self.s = school
        self.m = cp_model.CpModel()
        S, D, P = school.sections, range(len(school.days)), range(school.periods)
        self.x = {(c, d, p, sub): self.m.NewBoolVar(f"x_{c}_{d}_{p}_{sub}")
                  for c in S for d in D for p in P for sub in school.req[c]}
        # base structure
        for c in S:
            for d in D:
                for p in P:
                    self.m.Add(sum(self.x[c, d, p, sub] for sub in school.req[c]) <= 1)
            for sub, n in school.req[c].items():
                self.m.Add(sum(self.x[c, d, p, sub] for d in D for p in P) == n)
        # teacher occupancy: a teacher may take several (section, subject) pairs
        self.busy = {}
        for t in school.teachers:
            for d in D:
                for p in P:
                    e = sum(self.x[c, d, p, sub] for (c, sub) in school.taught[t])
                    self.busy[t, d, p] = e
                    self.m.Add(e <= 1)             # one room at a time
        self.idle = {}
        self.switch = {}

    # ---- idle-period indicators, built lazily (needed by gap rules) ----
    def _idle(self, t):
        if t in self.idle: return self.idle[t]
        D, P = range(len(self.s.days)), range(self.s.periods)
        out = {}
        for d in D:
            before, after = {}, {}
            for p in P:
                b = self.m.NewBoolVar(f"before_{t}_{d}_{p}")
                a = self.m.NewBoolVar(f"after_{t}_{d}_{p}")
                pre = [self.busy[t, d, q] for q in range(p)]
                post = [self.busy[t, d, q] for q in range(p + 1, self.s.periods)]
                self.m.Add(sum(pre) >= 1).OnlyEnforceIf(b)
                self.m.Add(sum(pre) == 0).OnlyEnforceIf(b.Not())
                self.m.Add(sum(post) >= 1).OnlyEnforceIf(a)
                self.m.Add(sum(post) == 0).OnlyEnforceIf(a.Not())
                g = self.m.NewBoolVar(f"idle_{t}_{d}_{p}")
                # idle  <->  busy before AND busy after AND not busy now
                self.m.AddBoolAnd([b, a]).OnlyEnforceIf(g)
                self.m.Add(self.busy[t, d, p] == 0).OnlyEnforceIf(g)
                # converse: busy before and after, and not idle  =>  teaching now
                self.m.Add(self.busy[t, d, p] >= 1).OnlyEnforceIf([b, a, g.Not()])
                out[d, p] = g
        self.idle[t] = out
        return out

    def add_rule(self, label, f):
        """f is a validated form dict. Returns the switch literal."""
        on = self.m.NewBoolVar(f"rule_{label}")
        self.switch[label] = (on, f)
        S, D, P = self.s.sections, range(len(self.s.days)), range(self.s.periods)
        secs = S if f.get("sections") in (None, "ALL") else f["sections"]
        teachers = self.s.teachers if f.get("teacher") in (None, "ALL") else [f["teacher"]]
        t_ = f["type"]

        if t_ == "max_consecutive":
            k = f["max"]
            for t in teachers:
                for d in D:
                    for start in range(self.s.periods - k):
                        win = range(start, start + k + 1)
                        if f.get("lunch_breaks_run") and self.s.lunch_after and \
                           start < self.s.lunch_after <= start + k:
                            continue
                        self.m.Add(sum(self.busy[t, d, p] for p in win) <= k).OnlyEnforceIf(on)

        elif t_ == "max_per_day":
            for t in teachers:
                for d in D:
                    self.m.Add(sum(self.busy[t, d, p] for p in P) <= f["max"]).OnlyEnforceIf(on)

        elif t_ == "teacher_unavailable":
            for dn in f["days"]:
                d = self.s.days.index(dn)
                for p in f["periods"]:
                    self.m.Add(self.busy[f["teacher"], d, p - 1] == 0).OnlyEnforceIf(on)

        elif t_ == "subject_not_in_periods":
            for c in secs:
                if f["subject"] not in self.s.req[c]: continue
                for d in D:
                    for p in f["periods"]:
                        self.m.Add(self.x[c, d, p - 1, f["subject"]] == 0).OnlyEnforceIf(on)

        elif t_ == "max_subject_per_day":
            for c in secs:
                subs = list(self.s.req[c]) if f["subject"] == "ALL" else [f["subject"]]
                for d in D:
                    for sub in subs:
                        if sub not in self.s.req[c]: continue
                        self.m.Add(sum(self.x[c, d, p, sub] for p in P) <= f["max"]).OnlyEnforceIf(on)

        elif t_ == "no_consecutive_same_subject":
            for c in secs:
                subs = list(self.s.req[c]) if f["subject"] == "ALL" else [f["subject"]]
                for d in D:
                    for sub in subs:
                        if sub not in self.s.req[c]: continue
                        for p in range(self.s.periods - 1):
                            self.m.Add(self.x[c, d, p, sub] + self.x[c, d, p + 1, sub] <= 1
                                       ).OnlyEnforceIf(on)

        elif t_ == "max_gaps_per_day":
            for t in teachers:
                g = self._idle(t)
                for d in D:
                    self.m.Add(sum(g[d, p] for p in P) <= f["max"]).OnlyEnforceIf(on)

        elif t_ == "require_midday_gap":
            # a gap only makes sense on a day the teacher actually works: min_lessons
            # says how many lessons a day must have before the rule applies.
            rng = [p - 1 for p in f["periods"]]
            k = int(f.get("min_lessons", 1))
            for t in teachers:
                g = self._idle(t)
                for d in D:
                    works = self.m.NewBoolVar(f"works_{t}_{d}_{label}")
                    load = sum(self.busy[t, d, p] for p in P)
                    self.m.Add(load >= k).OnlyEnforceIf(works)
                    self.m.Add(load <= k - 1).OnlyEnforceIf(works.Not())
                    self.m.Add(sum(g[d, p] for p in rng) >= 1).OnlyEnforceIf([on, works])

        elif t_ == "fixed_slot":
            for c in secs:
                if f["subject"] not in self.s.req[c]: continue
                for dn in f["days"]:
                    d = self.s.days.index(dn)
                    for p in f["periods"]:
                        self.m.Add(self.x[c, d, p - 1, f["subject"]] == 1).OnlyEnforceIf(on)
        elif t_ == "double_period":
            # every lesson of this subject is part of a block of exactly two consecutive
            # periods; blocks may not straddle the lunch break unless across_break is set.
            P_ = self.s.periods
            for c in secs:
                sub = f["subject"]
                if sub not in self.s.req[c]: continue
                for d in D:
                    st = {}
                    for p in range(P_ - 1):
                        if not f.get("across_break") and self.s.lunch_after and \
                           p + 1 == self.s.lunch_after:
                            continue          # a block starting here would cross the break
                        st[p] = self.m.NewBoolVar(f"dbl_{label}_{c}_{d}_{p}")
                    for p in range(P_):
                        cover = [st[q] for q in (p - 1, p) if q in st]
                        self.m.Add(self.x[c, d, p, sub] == sum(cover)).OnlyEnforceIf(on)
        else:
            raise ValueError(f"unknown rule type {t_}")
        return on
