"""The rules the school stated, as typed forms."""


def rules_for(b):
    """The rules Jyothy Tr stated, as typed forms."""
    out = [("no teacher more than four periods in a row",
            {"type": "max_consecutive", "teacher": "ALL", "max": 4,
             "lunch_breaks_run": True, "hard": False})]
    labs = [s for s in b.subjects if "LAB" in s]
    # a filled template says which subjects are doubles; a grid has to be measured
    stated = getattr(b, "doubles", None)
    doubles = list(stated) if stated else [
        s for s in labs if all(b.req[c].get(s, 0) % 2 == 0 for c in b.sections if s in b.req[c])]
    for s in doubles:
        # Jyothy Tr: a laboratory may run across lunch, the class simply goes to lunch and comes
        # back, but it is not what they want. So the double is required and not crossing the
        # break is asked for as a preference, which the system reports when it cannot be met.
        out.append((f"{s} should not run across lunch",
                    {"type": "double_period", "subject": s, "sections": "ALL",
                     "across_break": False, "hard": False}))
        out.append((f"{s} is a double period",
                    {"type": "double_period", "subject": s, "sections": "ALL",
                     # their own grid runs six lab doubles across the break, so a double is
                     # not required to sit wholly on one side of it
                     "across_break": True, "hard": True}))
    for s in labs:
        # stated without exceptions, and broken once in 37 because they could not avoid it
        # (11A, Monday), so it is a preference rather than a rule
        out.append((f"no {s} in the first period",
                    {"type": "subject_not_in_periods", "subject": s,
                     "sections": "ALL", "periods": [1], "hard": False}))
    for s in ("PT", "YOGA", "GAMES"):
        if s in b.subjects:
            out.append((f"no {s} in the first period",
                        {"type": "subject_not_in_periods", "subject": s,
                         "sections": "ALL", "periods": [1], "hard": True}))
            out.append((f"{s} at most once a day",
                        {"type": "max_subject_per_day", "subject": s,
                         "sections": "ALL", "max": 1, "hard": True}))
    for lab, secs, d, p in getattr(b, "fixed", []):
        here = [c for c in secs if c in b.sections and lab in b.req.get(c, {})]
        if here:
            out.append((f"{lab} is always on {b.days[d]} period {p + 1}",
                        {"type": "fixed_slot", "subject": lab, "sections": here,
                         "days": [b.days[d]], "periods": [p + 1], "hard": True}))
    for s in b.subjects:
        if s in doubles: continue
        out.append((f"{s} never twice in a row",
                    {"type": "no_consecutive_same_subject", "subject": s,
                     "sections": "ALL", "hard": False}))
    return out


