"""The rules the school stated, as typed forms."""


def rules_for(b):
    """The rules Jyothy Tr stated, as typed forms."""
    out = [("no teacher more than four periods in a row",
            {"type": "max_consecutive", "teacher": "ALL", "max": 4,
             "lunch_breaks_run": True, "hard": False})]
    labs = [s for s in b.subjects if "LAB" in s]
    doubles = [s for s in labs if all(b.req[c].get(s, 0) % 2 == 0 for c in b.sections if s in b.req[c])]
    for s in doubles:
        out.append((f"{s} is a double period",
                    {"type": "double_period", "subject": s, "sections": "ALL",
                     # their own grid runs six lab doubles across the break, so a double is
                     # not required to sit wholly on one side of it
                     "across_break": True, "hard": True}))
    for s in labs:
        out.append((f"no {s} in the first period",
                    {"type": "subject_not_in_periods", "subject": s,
                     "sections": "ALL", "periods": [1], "hard": True}))
    for s in ("PT", "YOGA", "GAMES"):
        if s in b.subjects:
            out.append((f"no {s} in the first period",
                        {"type": "subject_not_in_periods", "subject": s,
                         "sections": "ALL", "periods": [1], "hard": True}))
            out.append((f"{s} at most once a day",
                        {"type": "max_subject_per_day", "subject": s,
                         "sections": "ALL", "max": 1, "hard": True}))
    for s in b.subjects:
        if s in doubles: continue
        out.append((f"{s} never twice in a row",
                    {"type": "no_consecutive_same_subject", "subject": s,
                     "sections": "ALL", "hard": False}))
    return out


