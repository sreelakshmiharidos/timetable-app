"""Derive a machine-readable school from the class-wise timetable grid.

Input : data/g910.csv  (one row per section: subjects row | teachers row, 45 cells each)
Output: data/kmbvm_9_10.json  -- sections, subjects, weekly lesson requirements,
        and which teacher takes which (section, subject).

The grid is the school's OUTPUT. What the solver needs is the INPUT that produced it:
how many lessons each section needs of each subject, and who teaches them.
"""
import json, re, sys
from collections import Counter, defaultdict

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
PERIODS = 9
LUNCH_AFTER = 4          # TODO confirm with the school; assumed for now

# labels that mean the same thing
ALIAS = {
    "SCILAB": "SCI LAB", "MAT": "MTS",
    "KVLAB/YOGA": "KV LAB", "KV LAB/COMP": "KV LAB", "KV LAB/YOGA": "KV LAB",
    "ATR/CRAFT": "ART", "ART/CRAFT": "ART",
    "COMP/CRAFT": "COMP", "COMP/YOGA": "COMP",
    "ENG LAB/ROB": "ENG LAB", "D/M/D": "D/M", "KV/AI": "KV",
}
# support / supervision codes that are not class teachers
SUPPORT = {"ASK", "SIG", "SMC", "VIS", "PRC", "REM", "AJK", "NH", "NPT", "MMN", "MNK"}


def norm(label):
    x = re.sub(r"\s+", " ", label.strip().upper())
    return ALIAS.get(x, x)


def load(path):
    school = {
        "name": "KMBVM Pottore (grades 9 and 10)",
        "days": DAYS, "periods": PERIODS, "lunch_after": LUNCH_AFTER,
        "sections": [], "subjects": [], "requirements": {}, "assignment": {},
        "unstaffed": [],
    }
    subjects, assign_votes = set(), defaultdict(Counter)
    for line in open(path):
        sec, subs, teas = line.rstrip("\n").split("|")
        subs = [norm(x) for x in subs.split(",")]
        teas = [x.strip().upper() for x in teas.split(",")]
        assert len(subs) == len(teas) == DAYS.__len__() * PERIODS, (sec, len(subs), len(teas))
        school["sections"].append(sec)
        req = Counter(subs)
        school["requirements"][sec] = dict(req)
        subjects |= set(subs)
        for s, t in zip(subs, teas):
            codes = [c.strip() for c in t.split("/") if c.strip()]
            real = [c for c in codes if c not in SUPPORT]
            if len(real) == 1:
                assign_votes[(sec, s)][real[0]] += 1
    school["subjects"] = sorted(subjects)
    for (sec, s), votes in assign_votes.items():
        school["assignment"].setdefault(sec, {})[s] = votes.most_common(1)[0][0]
    # subjects with no clear single teacher: scheduled, but with no teacher constraint
    for sec in school["sections"]:
        for s in school["requirements"][sec]:
            if s not in school["assignment"].get(sec, {}):
                school["unstaffed"].append([sec, s])
    return school


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "../data/g910.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "data/kmbvm_9_10.json"
    sc = load(src)
    import os; os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(sc, open(out, "w"), indent=1)
    print(f"{len(sc['sections'])} sections, {len(sc['subjects'])} subjects")
    print("teachers found:", len({t for d in sc['assignment'].values() for t in d.values()}))
    print("unstaffed (section, subject) pairs:", len(sc["unstaffed"]))
    tot = Counter()
    for sec, d in sc["assignment"].items():
        for s, t in d.items(): tot[t] += sc["requirements"][sec][s]
    print("busiest teachers in 9-10:", tot.most_common(6))
    print("slots per section:", {s: sum(sc['requirements'][s].values()) for s in sc['sections']})
