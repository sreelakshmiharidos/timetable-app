"""School data model (v0.2): a school is sections, subjects, weekly requirements and
teacher assignments, loaded from JSON. Teachers are assigned to (section, subject)
pairs, not to a subject globally."""
import json
from collections import defaultdict


class School:
    def __init__(self, d):
        self.name = d["name"]
        self.days = d["days"]
        self.periods = d["periods"]
        self.lunch_after = d.get("lunch_after")
        self.sections = d["sections"]
        self.subjects = d["subjects"]
        self.req = {s: dict(v) for s, v in d["requirements"].items()}
        # A (section, subject) may name several teachers: when the class splits, all of them
        # are busy in that period. Older instance files hold a single name, so accept both.
        raw = d.get("assignment") or {}
        if not isinstance(raw, dict):
            raise ValueError("this school file's 'assignment' should be "
                             "{section: {subject: teacher or [teachers]}}")
        self.assign = {}
        for sec, m in raw.items():
            if not isinstance(m, dict):
                raise ValueError(f"assignment for section {sec} should be "
                                 f"{{subject: teacher or [teachers]}}, found {type(m).__name__}")
            self.assign[sec] = {k: ([x for x in v if x] if isinstance(v, (list, tuple))
                                    else ([v] if v else []))
                                for k, v in m.items()}
        # slots that do not exist: grades 1-5 have a zero period on Thursday only, so every
        # other day's zero period is closed
        # entries are (day, period) for the whole school, or (section, day, period) for one
        # section: in a single solve the secondary grades have no zero period but grades 1-5 do
        self.closed = {tuple(x) for x in d.get("closed", []) if len(x) == 2}
        self.closed_for = defaultdict(set)
        for x in d.get("closed", []):
            if len(x) == 3: self.closed_for[x[0]].add((x[1], x[2]))
        self.doubles = list(d.get("doubles") or [])
        self.fixed = [list(x) for x in (d.get("fixed") or [])]
        self.unstaffed = [tuple(x) for x in d.get("unstaffed", [])]
        # How a (section, subject)'s lessons are divided between teachers when more than one
        # takes them: {section: {subject: {teacher: lessons}}}. Absent means the class splits
        # in the period and every named teacher is busy for the whole subject.
        self.load = {s: {k: {t: int(n) for t, n in v.items()} for k, v in m.items()}
                     for s, m in (d.get("teacher_load") or {}).items()}

        # groups of sections whose students regroup for one lesson taught by one teacher
        self.block_groups = [{"subject": g["subject"], "sections": list(g["sections"])}
                             for g in (d.get("block_groups") or [])]
        # lessons different sections take together with one teacher, found from their own grid
        self.co_taught = [[tuple(x) for x in g] for g in (d.get("co_taught") or [])]
        self.committed = {t: {tuple(x) for x in v} for t, v in d.get("committed", {}).items()}
        self.teachers = sorted({t for v in self.assign.values() for ts in v.values() for t in ts})
        self.taught = defaultdict(list)          # teacher -> [(section, subject)]
        for sec, m in self.assign.items():
            for sub, ts in m.items():
                for t in ts:
                    self.taught[t].append((sec, sub))

    @classmethod
    def load(cls, path):
        return cls(json.load(open(path)))

    @property
    def slots(self):
        return len(self.days) * self.periods

    def teachers_of(self, section, subject):
        return self.assign.get(section, {}).get(subject, [])

    def teacher_of(self, section, subject):
        ts = self.teachers_of(section, subject)
        return "/".join(ts) if ts else None

    def subset(self, sections, committed=None):
        """A school containing only these sections, optionally with teacher time already
        committed elsewhere: {teacher: {(day_index, period_index), ...}}."""
        d = {"name": f"{self.name} [{', '.join(sections)}]", "days": self.days,
             "periods": self.periods, "lunch_after": self.lunch_after,
             "sections": list(sections), "subjects": self.subjects,
             "requirements": {c: self.req[c] for c in sections},
             "assignment": {c: self.assign.get(c, {}) for c in sections},
             "unstaffed": [list(x) for x in self.unstaffed if x[0] in sections],
             "doubles": list(self.doubles), "fixed": [list(x) for x in self.fixed],
             "closed": ([list(x) for x in self.closed]
                        + [[c, d, p] for c in sections for d, p in self.closed_for.get(c, ())]),
             "teacher_load": {c: self.load[c] for c in sections if c in self.load},
             "co_taught": [[list(x) for x in g if x[0] in sections] for g in self.co_taught],
             "block_groups": [{"subject": g["subject"],
                               "sections": [x for x in g["sections"] if x in sections]}
                              for g in self.block_groups
                              if len([x for x in g["sections"] if x in sections]) >= 2],
             "committed": {t: [list(x) for x in v] for t, v in (committed or {}).items()}}
        return School(d)

    def summary(self):
        return (f"{self.name}: {len(self.sections)} sections, {len(self.subjects)} subjects, "
                f"{len(self.teachers)} teachers, {len(self.days)}x{self.periods} slots, "
                f"{len(self.unstaffed)} unstaffed (section, subject) pairs")
