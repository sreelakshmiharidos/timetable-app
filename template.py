"""The school-facing input format: one workbook, five tabs.

Structure    one row per band: band, days, periods per day, break after period
Sections     section, band
Curriculum   section, subject, lessons per week
Allocation   section, subject, teacher   (one row per teacher; several rows = the class splits)
Groups       block name, subject, sections (comma separated)   -> sections regroup together
Rules        scope, rule (plain English), must/preference

read_workbook() turns it back into one instance per band, so a school can hand us a filled
template instead of a finished timetable.
"""
import json
from collections import defaultdict
import openpyxl

TABS = ["Structure", "Sections", "Curriculum", "Allocation", "Groups", "Rules"]


def write_workbook(bands, path, rules=()):
    """bands: {band_key: instance dict}"""
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    ws = wb.create_sheet("Structure"); ws.append(["band", "days", "periods per day", "break after period"])
    for k, sc in bands.items():
        ws.append([k, ", ".join(sc["days"]), sc["periods"], sc["lunch_after"]])
    ws = wb.create_sheet("Sections"); ws.append(["section", "band"])
    for k, sc in bands.items():
        for s in sc["sections"]: ws.append([s, k])
    ws = wb.create_sheet("Curriculum"); ws.append(["section", "subject", "lessons per week"])
    for sc in bands.values():
        for s in sc["sections"]:
            for sub, n in sorted(sc["requirements"][s].items()): ws.append([s, sub, n])
    ws = wb.create_sheet("Allocation"); ws.append(["section", "subject", "teacher"])
    for sc in bands.values():
        for s in sc["sections"]:
            for sub, ts in sorted(sc["assignment"][s].items()):
                for t in ts: ws.append([s, sub, t])
    ws = wb.create_sheet("Groups"); ws.append(["block", "subject", "sections (regroup together)"])
    for sc in bands.values():
        for lab, secs in sc.get("assumed", {}).get("blocks", {}).items():
            by_grade = defaultdict(list)
            for s in secs: by_grade[s[:-1]].append(s)
            for g, here in by_grade.items():
                if len(here) >= 2: ws.append([f"{lab} {g}", lab, ", ".join(sorted(here))])
    ws = wb.create_sheet("Rules"); ws.append(["scope", "rule", "must or preference"])
    for scope, text, hard in rules: ws.append([scope, text, "must" if hard else "preference"])
    wb.save(path); return path


def read_workbook(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    def rows(tab):
        ws = wb[tab]; it = ws.iter_rows(values_only=True); next(it, None)
        return [r for r in it if r and any(x is not None and str(x).strip() for x in r)]
    struct = {str(r[0]): {"days": [d.strip() for d in str(r[1]).split(",")],
                          "periods": int(r[2]), "lunch_after": int(r[3])} for r in rows("Structure")}
    band_of = {str(r[0]).strip(): str(r[1]).strip() for r in rows("Sections")}
    req = defaultdict(dict); assign = defaultdict(lambda: defaultdict(list))
    for s, sub, n in [(str(r[0]).strip(), str(r[1]).strip(), int(r[2])) for r in rows("Curriculum")]:
        req[s][sub] = n
    for s, sub, t in [(str(r[0]).strip(), str(r[1]).strip(), str(r[2]).strip()) for r in rows("Allocation")]:
        if t: assign[s][sub].append(t)
    groups = [(str(r[0]).strip(), str(r[1]).strip(),
               [x.strip() for x in str(r[2]).split(",")]) for r in rows("Groups")]
    rules = [(str(r[0]).strip(), str(r[1]).strip(), str(r[2]).strip().lower().startswith("must"))
             for r in rows("Rules") if r[1]]
    out = {}
    for band, st in struct.items():
        secs = [s for s, b in band_of.items() if b == band]
        if not secs: continue
        out[band] = {"name": f"{band}", "days": st["days"], "periods": st["periods"],
                     "lunch_after": st["lunch_after"], "sections": sorted(secs, key=lambda s: (len(s), s)),
                     "subjects": sorted({x for s in secs for x in req[s]}),
                     "requirements": {s: req[s] for s in secs},
                     "assignment": {s: {k: v for k, v in assign[s].items()} for s in secs},
                     "unstaffed": [],
                     "assumed": {"from": "uploaded workbook",
                                 "blocks": {b: secs2 for b, _, secs2 in groups
                                            if all(x in secs for x in secs2)}}}
    return out, rules
