"""Layer 1: turn one English sentence into a validated constraint form.

The language model picks a type from a fixed menu and fills named fields. It never
writes solver code. Each sentence is read `samples` times independently; disagreement
between readings, or a field the model reports it guessed, is treated as ambiguity.
"""
import json, os, re, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

MENU = {
  "max_consecutive": {"fields": {"teacher": "teacher name or ALL", "max": "int",
      "lunch_breaks_run": "true if the lunch break resets the count"},
      "eg": "No teacher should teach more than 3 periods in a row"},
  "max_per_day": {"fields": {"teacher": "teacher name or ALL", "max": "int"},
      "eg": "Ravi should teach at most 5 periods a day"},
  "teacher_unavailable": {"fields": {"teacher": "teacher name",
      "days": "list of day names", "periods": "list of period numbers"},
      "eg": "Suma cannot teach on Monday mornings"},
  "subject_not_in_periods": {"fields": {"subject": "subject name",
      "sections": "list of sections or ALL", "periods": "list of period numbers"},
      "eg": "No games in the first period"},
  "max_subject_per_day": {"fields": {"subject": "subject name or ALL",
      "sections": "list of sections or ALL", "max": "int"},
      "eg": "No subject more than twice a day"},
  "no_consecutive_same_subject": {"fields": {"subject": "subject name or ALL",
      "sections": "list of sections or ALL"},
      "eg": "Never the same subject twice in a row"},
  "max_gaps_per_day": {"fields": {"teacher": "teacher name or ALL", "max": "int"},
      "eg": "No teacher should have more than 3 free periods in a day"},
  "require_midday_gap": {"fields": {"teacher": "teacher name or ALL",
      "periods": "the periods that count as the middle of the day",
      "min_lessons": "the rule applies on days with at least this many lessons"},
      "eg": "Every teacher should get a free period in the middle of the day"},
  "fixed_slot": {"fields": {"subject": "subject name", "sections": "list of sections or ALL",
      "days": "list of day names", "periods": "list of period numbers"},
      "eg": "Assembly is Friday period 1 for every section"},
  "parallel_block": {"fields": {"subject": "subject name",
      "sections": "list of sections that are grouped together"},
      "eg": "11E, 11F and 11G take their elective at the same time"},
  "shared_resource": {"fields": {"subject": "subject name",
      "sections": "list of sections or ALL",
      "max_at_once": "how many sections may use it in one period (usually 1)"},
      "eg": "Only one class can be in the library at a time"},
  "double_period": {"fields": {"subject": "subject name",
      "sections": "list of sections or ALL",
      "across_break": "true if a double may straddle the lunch break"},
      "eg": "Laboratory periods must be double periods"},
}
COMMON = {"hard": "true = must hold, false = a preference that may be broken",
          "unstated": "list of field names the sentence did NOT state (you guessed them)"}


def prompt(school, sentence):
    return f"""You convert a school timetabling rule into JSON. Do NOT write code.
School: days {school.days}; periods 1-{school.periods}; lunch after period {school.lunch_after}.
Sections: {school.sections}
Subjects: {school.subjects}
Teachers: {school.teachers}

Pick exactly one rule type from this menu and fill its fields:
{json.dumps(MENU, indent=1)}
Every rule also has: {json.dumps(COMMON)}

If the sentence does not state a field, make your best guess AND list that field in "unstated".
If no rule type fits, return {{"type": "unsupported"}}.
Return ONLY a JSON object.

Rule: "{sentence}"
"""


# ----------------------------------------------------------------- providers
def _gemini(text, key, temperature=1.0):
    import requests
    for model in ("gemini-2.5-flash", "gemini-flash-latest"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        cfg = {"temperature": temperature, "responseMimeType": "application/json",
               "maxOutputTokens": 700}
        if "2.5" in model: cfg["thinkingConfig"] = {"thinkingBudget": 0}
        for attempt in range(3):
            r = requests.post(url, headers={"x-goog-api-key": key}, timeout=45,
                              json={"contents": [{"parts": [{"text": text}]}],
                                    "generationConfig": cfg})
            if r.status_code == 404: break
            if r.status_code in (429, 503):
                if attempt == 2: raise RuntimeError("Gemini is rate limiting; wait a minute.")
                time.sleep(5 * (attempt + 1)); continue
            if not r.ok: raise RuntimeError(f"Gemini error {r.status_code}: {r.text[:200]}")
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError("no Gemini model available")


def get_reader():
    def key(n):
        try:
            import streamlit as st
            if n in st.secrets: return st.secrets[n]
        except Exception: pass
        return os.environ.get(n)
    k = key("GEMINI_API_KEY")
    if k: return "Gemini", (lambda p: _gemini(p, k))
    return "built-in (no AI key)", None


# ----------------------------------------------------------------- offline fallback
def offline(school, s):
    t = s.lower()
    nums = [int(n) for n in re.findall(r"\b(\d+)\b", t)]
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "twice": 2}
    nums += [v for w, v in words.items() if re.search(rf"\b{w}\b", t)]
    teacher = next((x for x in school.teachers if x.lower() in t), "ALL")
    subject = next((x for x in school.subjects if x.lower() in t), None)
    if subject is None:                      # try word overlap, e.g. "science lab" -> "SCI LAB"
        best, score = None, 0
        for x in school.subjects:
            w = [p for p in re.split(r"[^a-z]+", x.lower()) if len(p) > 2]
            hit = sum(1 for p in w if p in t or (len(p) > 3 and p[:4] in t))
            if w and hit == len(w) and hit > score: best, score = x, hit
        subject = best
    hard = not any(w in t for w in ("prefer", "ideally", "if possible", "try to"))
    un = [] if any(w in t for w in ("must", "never", "prefer", "ideally")) else ["hard"]
    if subject and ("at the same time" in t or "parallel" in t or "same period" in t):
        secs = [c for c in school.sections if c.lower() in t] or "ALL"
        return {"type": "parallel_block", "subject": subject, "sections": secs,
                "hard": hard, "unstated": un}
    if subject and ("only one" in t or "at a time" in t or "one class" in t):
        return {"type": "shared_resource", "subject": subject, "sections": "ALL",
                "max_at_once": 1, "hard": hard, "unstated": un}
    if "double" in t and subject:
        return {"type": "double_period", "subject": subject, "sections": "ALL",
                "across_break": False, "hard": hard, "unstated": un + ["across_break"]}
    if "same subject" in t or "twice in a row" in t or "back to back" in t:
        return {"type": "no_consecutive_same_subject", "subject": subject or "ALL",
                "sections": "ALL", "hard": hard, "unstated": un}
    if "in a row" in t or "consecutive period" in t:
        return {"type": "max_consecutive", "teacher": teacher, "max": nums[0] if nums else 3,
                "lunch_breaks_run": False, "hard": hard, "unstated": un + ["lunch_breaks_run"]}
    if "middle of the day" in t or "midday" in t:
        mid = list(range(2, school.periods))
        return {"type": "require_midday_gap", "teacher": teacher, "periods": mid,
                "min_lessons": 2, "hard": hard, "unstated": un + ["periods", "min_lessons"]}
    if "free period" in t and ("more than" in t or "most" in t):
        return {"type": "max_gaps_per_day", "teacher": teacher, "max": nums[0] if nums else 3,
                "hard": hard, "unstated": un}
    if ("a day" in t or "per day" in t) and ("subject" in t or subject):
        if "subject" in t and subject is None: subject = "ALL"
        return {"type": "max_subject_per_day", "subject": subject or "ALL", "sections": "ALL",
                "max": nums[0] if nums else 2, "hard": hard, "unstated": un}
    if "a day" in t or "per day" in t:
        return {"type": "max_per_day", "teacher": teacher, "max": nums[0] if nums else 5,
                "hard": hard, "unstated": un}
    if teacher != "ALL" and any(w in t for w in ("not available", "cannot", "can't", "unavailable", "off")):
        days = [d for d in school.days if d.lower() in t] or school.days
        if "morning" in t: per = list(range(1, (school.lunch_after or 4) + 1))
        elif "afternoon" in t: per = list(range((school.lunch_after or 4) + 1, school.periods + 1))
        else: per = list(range(1, school.periods + 1))
        return {"type": "teacher_unavailable", "teacher": teacher, "days": days,
                "periods": per, "hard": hard, "unstated": un}
    if subject:
        if "first period" in t: per = [1]
        elif "last period" in t: per = [school.periods]
        elif "morning" in t: per = list(range(1, (school.lunch_after or 4) + 1))
        else: per = nums or [1]
        return {"type": "subject_not_in_periods", "subject": subject, "sections": "ALL",
                "periods": per, "hard": hard, "unstated": un}
    return {"type": "unsupported"}


# ----------------------------------------------------------------- validation
def clean(school, form):
    from model import RULE_TYPES
    f = dict(form); t = f.get("type")
    if t == "unsupported" or t not in RULE_TYPES:
        raise ValueError("I don't have a rule type for that yet")
    f["hard"] = bool(f.get("hard", True))
    f["unstated"] = sorted(set(f.get("unstated") or []))

    def match(name, options, what):
        if name in (None, "ALL", "all", "All"): return "ALL"
        for o in options:
            if str(name).strip().lower() == o.lower(): return o
        for o in options:
            if str(name).strip().lower() in o.lower(): return o
        raise ValueError(f"{what} '{name}' is not in this school")

    if "teacher" in RULE_TYPES[t]:
        f["teacher"] = match(f.get("teacher"), school.teachers, "teacher")
        if t == "teacher_unavailable" and f["teacher"] == "ALL":
            raise ValueError("this rule needs one named teacher")
    if "subject" in RULE_TYPES[t]:
        f["subject"] = match(f.get("subject"), school.subjects, "subject")
        if t in ("subject_not_in_periods", "fixed_slot", "double_period") and f["subject"] == "ALL":
            raise ValueError("this rule needs one named subject")
    if "sections" in RULE_TYPES[t]:
        c = f.get("sections", "ALL")
        f["sections"] = "ALL" if c in ("ALL", None) or set(c) == set(school.sections) \
            else sorted(match(x, school.sections, "section") for x in c)
    if "days" in RULE_TYPES[t]:
        want = {str(x)[:3].title() for x in (f.get("days") or [])}
        f["days"] = [d for d in school.days if d in want] or school.days
    if "periods" in RULE_TYPES[t]:
        f["periods"] = sorted({int(p) for p in (f.get("periods") or [])
                               if 1 <= int(p) <= school.periods})
        if not f["periods"]: raise ValueError("no valid period numbers in that rule")
    if "max" in RULE_TYPES[t]: f["max"] = int(f["max"])
    if t == "max_consecutive": f["lunch_breaks_run"] = bool(f.get("lunch_breaks_run", False))
    if t == "double_period": f["across_break"] = bool(f.get("across_break", False))
    if t == "require_midday_gap": f["min_lessons"] = int(f.get("min_lessons", 2))
    if t == "shared_resource": f["max_at_once"] = int(f.get("max_at_once", 1))
    if t == "parallel_block":
        # cheap check the solver would take a long time to prove: sections can only run a
        # subject in parallel if they have the same number of lessons of it.
        secs = school.sections if f["sections"] == "ALL" else f["sections"]
        counts = {c: school.req[c].get(f["subject"]) for c in secs if f["subject"] in school.req[c]}
        if len(counts) < 2:
            raise ValueError(f"fewer than two sections take {f['subject']}")
        if len(set(counts.values())) > 1:
            detail = ", ".join(f"{c} has {n}" for c, n in counts.items())
            raise ValueError(f"these sections cannot run {f['subject']} in parallel: {detail} "
                             "lessons a week")
    return {k: f[k] for k in ["type", *RULE_TYPES[t], "hard", "unstated"]}


def _key(f): return json.dumps({k: v for k, v in f.items() if k != "unstated"}, sort_keys=True)


def interpretations(school, sentence, reader=None, samples=3):
    """Returns (options, reason). options = [(form, votes)] most likely first."""
    if reader is None:
        forms = [clean(school, offline(school, sentence))]
    else:
        def one(_):
            try:
                txt = reader(prompt(school, sentence))
                txt = txt[txt.find("{"): txt.rfind("}") + 1]
                return clean(school, json.loads(txt))
            except Exception as e:
                return {"type": "error", "why": str(e)}
        with ThreadPoolExecutor(max_workers=samples) as pool:
            forms = list(pool.map(one, range(samples)))
    good = [f for f in forms if f.get("type") != "error"]
    if not good: raise ValueError(forms[0].get("why", "could not read that rule"))
    votes = Counter(_key(f) for f in good)
    by = {}
    for f in good:
        k = _key(f); by.setdefault(k, dict(f))
        by[k]["unstated"] = sorted(set(by[k]["unstated"]) | set(f["unstated"]))
    opts = [(by[k], n) for k, n in votes.most_common()]
    top = opts[0][0]
    for fld in top["unstated"]:                      # offer the other reading of a guessed yes/no
        if fld != "hard" and isinstance(top.get(fld), bool):
            alt = {**top, fld: not top[fld]}
            if _key(alt) not in {_key(f) for f, _ in opts}: opts.append((alt, 0))
    if len(opts) == 1: return opts, None
    why = "the AI's readings disagreed" if sum(1 for _, n in opts if n) > 1 \
        else "the sentence doesn't say"
    return opts, why


def describe(school, f, notes=True):
    t = f["type"]
    who = "Every teacher" if f.get("teacher") == "ALL" else f.get("teacher")
    secs = "every section" if f.get("sections") == "ALL" else ", ".join(f.get("sections") or [])
    per = lambda ps: "period" + ("s " if len(ps) > 1 else " ") + ", ".join(map(str, ps))
    if t == "max_consecutive":
        s = (f"{who} teaches at most {f['max']} periods in a row; "
             + ("lunch resets the count" if f["lunch_breaks_run"] else "lunch does NOT reset the count"))
    elif t == "max_per_day": s = f"{who} teaches at most {f['max']} periods a day"
    elif t == "teacher_unavailable":
        s = f"{f['teacher']} is not available on {', '.join(f['days'])}, {per(f['periods'])}"
    elif t == "subject_not_in_periods":
        s = f"No {f['subject']} for {secs} in {per(f['periods'])}"
    elif t == "max_subject_per_day":
        sub = "any one subject" if f["subject"] == "ALL" else f["subject"]
        s = f"{secs.capitalize()} has {sub} at most {f['max']} time(s) a day"
    elif t == "no_consecutive_same_subject":
        sub = "the same subject" if f["subject"] == "ALL" else f["subject"]
        s = f"{secs.capitalize()} never has {sub} in two periods in a row"
    elif t == "max_gaps_per_day":
        s = f"{who} has at most {f['max']} free periods between their first and last class each day"
    elif t == "require_midday_gap":
        s = (f"{who} gets a free period within {per(f['periods'])}, "
             f"on days with at least {f['min_lessons']} lessons")
    elif t == "fixed_slot":
        s = f"{f['subject']} is fixed for {secs} on {', '.join(f['days'])}, {per(f['periods'])}"
    elif t == "parallel_block":
        s = (f"{', '.join(f['sections']) if f['sections'] != 'ALL' else 'every section'} "
             f"take {f['subject']} in the same periods as each other")
    elif t == "shared_resource":
        n = f.get("max_at_once", 1)
        s = (f"At most {n} section{'' if n == 1 else 's'} can have {f['subject']} in any one period"
             + ("" if f["sections"] == "ALL" else f" (among {', '.join(f['sections'])})"))
    elif t == "double_period":
        s = (f"{f['subject']} always runs as a double period for {secs}"
             + ("" if f["across_break"] else "; a double may not cross the lunch break"))
    else: s = t
    if not notes: return s
    s += " [MUST]" if f["hard"] else " [PREFERENCE]"
    if f.get("unstated"): s += f"  (guessed: {', '.join(f['unstated'])})"
    return s
