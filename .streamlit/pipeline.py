"""
FYP v1: plain-English rules -> structured form -> CP-SAT timetable.

Layer 1  read_rule()      AI fills a fixed form (never writes solver code)
Layer 2  build_model()    my translator: form -> CP-SAT constraints
Layer 3  describe(), explain_conflict()   plain-English echo + conflict explanation
Research bit: sample the AI N times per rule; disagreement = ambiguity -> ask.
"""
import json, os, re, time, itertools
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from ortools.sat.python import cp_model

# ---------------------------------------------------------------- fake school
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
PERIODS = 6                      # periods 1..6
LUNCH_AFTER = 3                  # lunch between period 3 and 4
CLASSES = ["6A", "6B", "7A", "7B"]
TEACHERS = {                     # teacher -> subject (teaches it to every class)
    "Suma": "Maths", "Ravi": "English", "Anita": "Science",
    "Joseph": "Malayalam", "Priya": "Social", "Deepa": "PE",
}
LESSONS_PER_WEEK = {"Maths": 6, "English": 5, "Science": 5,
                    "Malayalam": 4, "Social": 4, "PE": 2}
SUBJECTS = list(LESSONS_PER_WEEK)
SUBJECT_TEACHER = {s: t for t, s in TEACHERS.items()}

# ---------------------------------------------------------------- the form (Layer 1 menu)
RULE_MENU = {
    "max_consecutive": {
        "fields": {"teacher": "teacher name or ALL", "max": "int",
                   "lunch_breaks_run": "true if the lunch break resets the count"},
        "example": "No teacher should teach more than 3 periods in a row"},
    "max_per_day": {
        "fields": {"teacher": "teacher name or ALL", "max": "int"},
        "example": "Ravi should teach at most 4 periods a day"},
    "teacher_unavailable": {
        "fields": {"teacher": "teacher name", "days": "list of Mon..Fri",
                   "periods": "list of ints 1..6"},
        "example": "Suma can't teach on Monday mornings"},
    "subject_not_in_periods": {
        "fields": {"subject": "subject name", "classes": "list of classes or ALL",
                   "periods": "list of ints 1..6"},
        "example": "No PE in the first period"},
    "max_subject_per_day": {
        "fields": {"subject": "subject name or ALL", "classes": "list of classes or ALL",
                   "max": "int"},
        "example": "A class shouldn't have the same subject twice in a day"},
}
COMMON_FIELDS = {"hard": "true = must hold, false = preference that can be broken",
                 "unstated": "list of field names the sentence did NOT say explicitly (you guessed them)"}


def _prompt(sentence):
    return f"""You convert a school timetabling rule into JSON. Do NOT write code.
School facts: days {DAYS}; periods 1-{PERIODS} (lunch after period {LUNCH_AFTER}; "morning" = periods 1-{LUNCH_AFTER}, "afternoon" = {LUNCH_AFTER+1}-{PERIODS});
classes {CLASSES}; teachers {TEACHERS} (teacher: subject); subjects {SUBJECTS}.

Pick exactly one rule type from this menu and fill its fields:
{json.dumps(RULE_MENU, indent=1)}
Every rule also has these fields: {json.dumps(COMMON_FIELDS)}

If the sentence does not state a field, make your best guess AND list that field in "unstated".
If the sentence fits no rule type, return {{"type": "unsupported"}}.
Return ONLY a JSON object like {{"type": "...", "hard": true, "unstated": [...], ...fields}}.

Rule: "{sentence}"
"""

# ---------------------------------------------------------------- AI readers
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-flash-latest"]   # tried in order


def _gemini(prompt, key, temperature=1.0):
    import requests
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        try:
            return _gemini_call(url, prompt, key, temperature)
        except FileNotFoundError:
            continue                                  # model retired, try the next one
    raise RuntimeError("No Gemini model found: edit GEMINI_MODELS")


def _gemini_call(url, prompt, key, temperature):
    import requests
    cfg = {"temperature": temperature, "responseMimeType": "application/json",
           "maxOutputTokens": 600}
    if "2.5" in url: cfg["thinkingConfig"] = {"thinkingBudget": 0}   # speed: no thinking step
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": cfg}
    for attempt in range(3):
        r = requests.post(url, headers={"x-goog-api-key": key}, json=body, timeout=45)
        if r.status_code in (429, 503):          # free-tier rate limit: wait and retry
            if attempt == 2: raise RuntimeError("Gemini is rate limiting us. Wait a minute and try again.")
            time.sleep(5 * (attempt + 1)); continue
        if r.status_code == 404: raise FileNotFoundError
        if not r.ok: raise RuntimeError(f"Gemini error {r.status_code}: {r.text[:300]}")
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError("Gemini rate limit: wait a minute and rerun")


def _claude(prompt, key, model=None, temperature=1.0):
    import requests
    model = model or os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=60,
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                      json={"model": model, "max_tokens": 400, "temperature": temperature,
                            "messages": [{"role": "user", "content": prompt}]})
    if not r.ok: raise RuntimeError(f"Claude error {r.status_code}: {r.text[:300]}")
    return r.json()["content"][0]["text"]


def _offline(sentence):
    """No-API fallback: understands fixed phrasings only."""
    s = sentence.lower()
    nums = [int(n) for n in re.findall(r"\b(\d+)\b", s)]
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "once": 1, "twice": 2}
    nums += [v for w, v in words.items() if re.search(rf"\b{w}\b", s)]
    teacher = next((t for t in TEACHERS if t.lower() in s), "ALL")
    subject = next((x for x in SUBJECTS if x.lower() in s), None)
    days = [d for d in DAYS if d.lower() in s] or (DAYS if "any day" in s else [])
    if "morning" in s: periods = list(range(1, LUNCH_AFTER + 1))
    elif "afternoon" in s: periods = list(range(LUNCH_AFTER + 1, PERIODS + 1))
    elif "first period" in s: periods = [1]
    elif "last period" in s: periods = [PERIODS]
    else: periods = list(range(1, PERIODS + 1))
    hard = not any(w in s for w in ["prefer", "ideally", "try", "if possible"])
    unst = [] if any(w in s for w in ["must", "never", "prefer", "ideally", "if possible"]) else ["hard"]
    if "in a row" in s or "consecutive" in s:
        lb = "lunch" in s
        return {"type": "max_consecutive", "teacher": teacher, "max": nums[0], "lunch_breaks_run": lb,
                "hard": hard, "unstated": unst + ([] if lb else ["lunch_breaks_run"])}
    if ("subject" in s or (subject and teacher == "ALL")) and "day" in s:
        more = re.search(r"more than (\w+)", s)
        mx = (int(more.group(1)) if more.group(1).isdigit() else words.get(more.group(1), 1)) if more else 1
        return {"type": "max_subject_per_day", "subject": subject or "ALL", "classes": "ALL",
                "max": mx, "hard": hard, "unstated": unst}
    if "a day" in s or "per day" in s:
        return {"type": "max_per_day", "teacher": teacher, "max": nums[0], "hard": hard, "unstated": unst}
    if teacher != "ALL" and ("not available" in s or "can't" in s or "cannot" in s or "unavailable" in s or "off" in s):
        return {"type": "teacher_unavailable", "teacher": teacher, "days": days or DAYS,
                "periods": periods, "hard": hard, "unstated": unst}
    if subject and ("no " in s or "not" in s):
        return {"type": "subject_not_in_periods", "subject": subject, "classes": "ALL",
                "periods": periods, "hard": hard, "unstated": unst}
    return {"type": "unsupported"}


def get_reader():
    """Pick Gemini if a key exists, else Claude, else offline."""
    def key(name):
        try:
            from google.colab import userdata      # Colab Secrets
            return userdata.get(name)
        except Exception:
            return os.environ.get(name)
    if key("GEMINI_API_KEY"):
        k = key("GEMINI_API_KEY"); return "Gemini", lambda p: _gemini(p, k)
    if key("ANTHROPIC_API_KEY"):
        k = key("ANTHROPIC_API_KEY"); return "Claude", lambda p: _claude(p, k)
    return "offline", None

# ---------------------------------------------------------------- validation
def _match(name, options):
    if name in (None, "ALL", "all", "All"): return "ALL"
    for o in options:
        if str(name).lower() == o.lower() or str(name).lower() in o.lower(): return o
    raise ValueError(f"'{name}' not recognised (options: {options})")


def clean(form):
    """Check the AI's form against the school data. Returns a normalised form or raises."""
    f = dict(form); t = f.get("type")
    if t not in RULE_MENU: raise ValueError("rule type not supported yet")
    f["hard"] = bool(f.get("hard", True))
    f["unstated"] = sorted(set(f.get("unstated") or []))
    if "teacher" in RULE_MENU[t]["fields"]:
        f["teacher"] = _match(f.get("teacher"), list(TEACHERS))
        if t == "teacher_unavailable" and f["teacher"] == "ALL": raise ValueError("needs one teacher")
    if "subject" in RULE_MENU[t]["fields"]:
        f["subject"] = _match(f.get("subject"), SUBJECTS)
    if "classes" in RULE_MENU[t]["fields"]:
        c = f.get("classes", "ALL")
        f["classes"] = "ALL" if c in ("ALL", None) or c == CLASSES else sorted(_match(x, CLASSES) for x in c)
    if "days" in f: f["days"] = [d for d in DAYS if d in {_match(x[:3], DAYS) for x in f["days"]}]
    if "periods" in f: f["periods"] = sorted({int(p) for p in f["periods"] if 1 <= int(p) <= PERIODS})
    if "max" in f: f["max"] = int(f["max"])
    if t == "max_consecutive": f["lunch_breaks_run"] = bool(f.get("lunch_breaks_run", False))
    return {k: f[k] for k in ["type", *RULE_MENU[t]["fields"], "hard", "unstated"]}


def _key(form):   # what counts as "the same interpretation" (ignore the unstated list)
    return json.dumps({k: v for k, v in form.items() if k != "unstated"}, sort_keys=True)


def read_rule(sentence, reader=None, samples=3):
    """Layer 1 + ambiguity check. Returns list of (form, votes), most common first."""
    if reader is None:
        forms = [clean(_offline(sentence))]
    else:
        def one(_):
            try:
                txt = reader(_prompt(sentence))
                txt = txt[txt.find("{"): txt.rfind("}") + 1]
                return clean(json.loads(txt))
            except Exception as e:
                return {"type": "error", "why": str(e)}
        with ThreadPoolExecutor(max_workers=samples) as pool:   # all readings at once
            forms = list(pool.map(one, range(samples)))
    good = [f for f in forms if f.get("type") != "error"]
    if not good: raise ValueError(forms[0]["why"])
    votes = Counter(_key(f) for f in good)
    by_key = {}
    for f in good:   # merge unstated lists across samples
        k = _key(f); by_key.setdefault(k, dict(f))
        by_key[k]["unstated"] = sorted(set(by_key[k]["unstated"]) | set(f["unstated"]))
    return [(by_key[k], n) for k, n in votes.most_common()]

def interpretations(sentence, reader=None, samples=3):
    """Returns (options, reason). options = [(form, votes)], most likely first.
    reason is None when we're confident, else why we need to ask."""
    opts = read_rule(sentence, reader, samples)
    top = opts[0][0]
    # also offer the other reading of any yes/no detail the sentence didn't state
    for fld in top["unstated"]:
        if fld != "hard" and isinstance(top.get(fld), bool):
            alt = {**top, fld: not top[fld]}
            if _key(alt) not in {_key(f) for f, _ in opts}: opts.append((alt, 0))
    if len(opts) == 1: return opts, None
    why = "the AI's readings disagreed" if sum(1 for _, n in opts if n) > 1 else "the sentence doesn't say"
    return opts, why


def confirm(sentence, reader=None, samples=3, ask=True):
    """Notebook version: print what we understood, ask only where we're unsure."""
    opts, why = interpretations(sentence, reader, samples)
    top = opts[0][0]
    print(f'\n"{sentence}"')
    if why is None:
        print(f"  Understood: {describe(top)}"); return top
    total = sum(n for _, n in opts)
    print(f"  I'm not sure what you meant ({why}). Options:")
    for i, (f, n) in enumerate(opts, 1):
        print(f"   {i}. {describe(f)}" + (f"   <- {n}/{total} readings" if n else ""))
    if not ask: return top
    pick = input("  Which one? [1] ").strip()
    return opts[int(pick) - 1][0] if pick.isdigit() and 1 <= int(pick) <= len(opts) else top


# ---------------------------------------------------------------- Layer 3a: echo back
def _days(ds): return "every day" if ds == DAYS else ", ".join(ds)
def _pers(ps): return "all periods" if ps == list(range(1, PERIODS + 1)) else "period" + ("s " if len(ps) > 1 else " ") + ", ".join(map(str, ps))
def _who(t): return "Every teacher" if t == "ALL" else t
def _cls(c): return "any class" if c == "ALL" else ", ".join(c)
def _times(n): return {1: "once", 2: "twice"}.get(n, f"{n} times")

def describe(f, notes=True):
    t = f["type"]
    if t == "max_consecutive":
        s = f"{_who(f['teacher'])} teaches at most {f['max']} periods in a row; " + \
            ("lunch resets the count" if f["lunch_breaks_run"] else "lunch does NOT reset the count")
    elif t == "max_per_day":
        s = f"{_who(f['teacher'])} teaches at most {f['max']} periods a day"
    elif t == "teacher_unavailable":
        s = f"{f['teacher']} is not available on {_days(f['days'])}, {_pers(f['periods'])}"
    elif t == "subject_not_in_periods":
        s = f"No {f['subject']} for {_cls(f['classes'])} in {_pers(f['periods'])}"
    elif t == "max_subject_per_day":
        subj = "any one subject" if f["subject"] == "ALL" else f["subject"]
        who = "Every class" if f["classes"] == "ALL" else _cls(f["classes"])
        s = f"{who} has {subj} at most {_times(f['max'])} a day"
    if not notes: return s
    s += " [MUST]" if f["hard"] else " [PREFERENCE]"
    if f.get("unstated"): s += f"  (guessed: {', '.join(f['unstated'])})"
    return s

# ---------------------------------------------------------------- Layer 2: translator
def build_model(rules):
    """rules: list of (label, form). Each rule gets one on/off switch literal."""
    m = cp_model.CpModel()
    D, P = range(len(DAYS)), range(PERIODS)
    x = {(c, d, p, s): m.NewBoolVar(f"{c}_{d}_{p}_{s}")
         for c in CLASSES for d in D for p in P for s in SUBJECTS}
    # base structure (always on)
    for c in CLASSES:
        for d in D:
            for p in P: m.Add(sum(x[c, d, p, s] for s in SUBJECTS) <= 1)
        for s in SUBJECTS: m.Add(sum(x[c, d, p, s] for d in D for p in P) == LESSONS_PER_WEEK[s])
    busy = {(t, d, p): sum(x[c, d, p, TEACHERS[t]] for c in CLASSES)
            for t in TEACHERS for d in D for p in P}
    for k, e in busy.items(): m.Add(e <= 1)              # a teacher is in one room at a time

    switches, soft = {}, []
    for label, f in rules:
        on = m.NewBoolVar(f"rule_{label}"); switches[label] = (on, f)
        (soft if not f["hard"] else []).append(on)
        teachers = list(TEACHERS) if f.get("teacher") == "ALL" else [f.get("teacher")]
        classes = CLASSES if f.get("classes") == "ALL" else f.get("classes")
        t = f["type"]
        if t == "max_consecutive":
            k = f["max"]
            for tt in teachers:
                for d in D:
                    for start in range(PERIODS - k):
                        win = range(start, start + k + 1)
                        if f["lunch_breaks_run"] and (start < LUNCH_AFTER < start + k + 1):
                            continue                    # window crosses lunch: not a real run
                        m.Add(sum(busy[tt, d, p] for p in win) <= k).OnlyEnforceIf(on)
        elif t == "max_per_day":
            for tt in teachers:
                for d in D: m.Add(sum(busy[tt, d, p] for p in P) <= f["max"]).OnlyEnforceIf(on)
        elif t == "teacher_unavailable":
            for dn in f["days"]:
                for p in f["periods"]:
                    m.Add(busy[f["teacher"], DAYS.index(dn), p - 1] == 0).OnlyEnforceIf(on)
        elif t == "subject_not_in_periods":
            for c in classes:
                for d in D:
                    for p in f["periods"]: m.Add(x[c, d, p - 1, f["subject"]] == 0).OnlyEnforceIf(on)
        elif t == "max_subject_per_day":
            subs = SUBJECTS if f["subject"] == "ALL" else [f["subject"]]
            for c in classes:
                for d in D:
                    for s in subs: m.Add(sum(x[c, d, p, s] for p in P) <= f["max"]).OnlyEnforceIf(on)
    if soft: m.Maximize(sum(soft))
    return m, x, switches


def _solve(rules, seconds=10, hard_labels=None):
    m, x, sw = build_model(rules)
    hard = [sw[l][0] for l in (hard_labels if hard_labels is not None else
                               [l for l, f in rules if f["hard"]])]
    m.AddAssumptions(hard)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_workers = 8
    st = solver.Solve(m)
    return st, solver, x, sw

# ---------------------------------------------------------------- Layer 3b: conflicts
def explain_conflict(rules, seconds=5):
    """Smallest set of MUST rules that can't all hold (deletion-based, fine for few rules)."""
    core = [l for l, f in rules if f["hard"]]
    st, solver, _, sw = _solve(rules, seconds, hard_labels=core)
    if st == cp_model.INFEASIBLE:
        idx = set(solver.SufficientAssumptionsForInfeasibility())
        core = [l for l in core if sw[l][0].Index() in idx] or core
    base_ok, _, _, _ = _solve(rules, seconds, hard_labels=[])
    if base_ok not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None                                          # the school data itself is impossible
    for l in list(core):
        trial = [c for c in core if c != l]
        st, *_ = _solve(rules, seconds, hard_labels=trial)
        if st == cp_model.INFEASIBLE: core = trial           # still impossible without l -> l not needed
    return core


def solve(rules, seconds=10):
    """Returns dict with status, timetable grids, broken preferences or conflict."""
    st, solver, x, sw = _solve(rules, seconds)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        grids = {}
        for c in CLASSES:
            grids[c] = [[next((s for s in SUBJECTS if solver.Value(x[c, d, p, s])), None)
                         for d in range(len(DAYS))] for p in range(PERIODS)]
        broken = [l for l, (on, f) in sw.items() if not f["hard"] and not solver.Value(on)]
        return {"ok": True, "grids": grids, "broken": broken}
    if st == cp_model.INFEASIBLE:
        return {"ok": False, "conflict": explain_conflict(rules)}
    return {"ok": False, "conflict": None, "note": "solver ran out of time"}


def print_result(res, rules):
    lookup = dict(rules)
    if res["ok"]:
        for c, g in res["grids"].items():
            print(f"\n=== Class {c} ===")
            print(f"{'':4}" + "".join(f"{d:<20}" for d in DAYS))
            for p, row in enumerate(g):
                if p == LUNCH_AFTER: print("     ---- lunch ----")
                print(f"P{p+1:<3}" + "".join(f"{(f'{s} ({SUBJECT_TEACHER[s]})' if s else 'free'):<20}" for s in row))
        if res["broken"]:
            print("\nPreferences that couldn't be met:")
            for l in res["broken"]: print(f"  {l}: {describe(lookup[l])}")
        else:
            print("\nAll rules satisfied.")
    else:
        print("No timetable is possible.")
        if res.get("conflict"):
            if len(res["conflict"]) == 1:
                print("This rule on its own can't fit the lesson counts:")
            else:
                print("These rules can't all be true together (drop or relax any one of them):")
            for l in res["conflict"]: print(f"  {l}: {describe(lookup[l])}")
        elif res.get("note"): print(res["note"])
        else: print("Even with no rules, the lesson counts don't fit. Check the school data.")
