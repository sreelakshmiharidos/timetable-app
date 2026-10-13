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
        self.assign = {s: dict(v) for s, v in d.get("assignment", {}).items()}
        self.unstaffed = [tuple(x) for x in d.get("unstaffed", [])]
        self.teachers = sorted({t for v in self.assign.values() for t in v.values()})
        self.taught = defaultdict(list)          # teacher -> [(section, subject)]
        for sec, m in self.assign.items():
            for sub, t in m.items():
                self.taught[t].append((sec, sub))

    @classmethod
    def load(cls, path):
        return cls(json.load(open(path)))

    @property
    def slots(self):
        return len(self.days) * self.periods

    def teacher_of(self, section, subject):
        return self.assign.get(section, {}).get(subject)

    def summary(self):
        return (f"{self.name}: {len(self.sections)} sections, {len(self.subjects)} subjects, "
                f"{len(self.teachers)} teachers, {len(self.days)}x{self.periods} slots, "
                f"{len(self.unstaffed)} unstaffed (section, subject) pairs")
