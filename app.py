import html, json, time
import streamlit as st
from school import School
import reader as R
from solve import solve

VERSION = "v0.7"
SOLVE_CAP = 60          # seconds; the free-period rules are expensive on the real school
UPLOAD = "Our school (upload the workbook)"
DEMOS = {"KMBVM Pottore, grades 9 and 10 (fastest real band)": "data/kmbvm_9_10.json",
         "KMBVM Pottore, grades 11 and 12": "data/kmbvm_11_12.json",
         "KMBVM Pottore, grades 6 to 8": "data/kmbvm_6_8.json",
         "KMBVM Pottore, grades 1 to 5": "data/kmbvm_1_5.json",
         "KMBVM Pottore (the whole school, slow)": "data/kmbvm_school.json",
         "Sample school (small and fast)": "data/sample_school.json"}
BAND_LABEL = {"11_12": "grades 11 and 12", "9_10": "grades 9 and 10",
              "6_8": "grades 6 to 8", "1_5": "grades 1 to 5", "all": "the whole school"}
CAP = 150          # seconds per band
EXAMPLES = {
 "data/kmbvm_school.json": "No teacher should teach more than 4 periods in a row\n"
                           "No subject more than twice a day\n"
                           "Only one class can be in the LIB at a time",
 "data/sample_school.json": "No teacher should teach more than 3 periods in a row\n"
                            "Suma is not available on Monday\n"
                            "No PE in the first period",
 "data/kmbvm_9_10.json": "No teacher should teach more than 4 periods in a row\n"
                          "No subject more than twice a day\n"
                          "PHY must be taught as a double period\n"
                          "No PT in the first period",
 "data/kmbvm_11_12.json": "11E, 11F and 11G take M/IP/P at the same time\n"
                           "No teacher should teach more than 4 periods in a row\n"
                           "Only one class can be in the LIB at a time",
 "data/kmbvm_6_8.json": "No teacher should teach more than 4 periods in a row\n"
                        "No subject more than twice a day",
 "data/kmbvm_1_5.json": "No PT in the first period\n"
                        "Only one class can be in the LIB at a time",
 "data/sample.json": "No teacher should teach more than 3 periods in a row\n"
                      "Suma is not available on Monday\n"
                      "No PE in the first period\n"
                      "No subject more than twice a day",
}

st.set_page_config(page_title="Chalk n Duster", page_icon="🗓️", layout="centered")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea, .stTextArea textarea { font-family:'Inter',sans-serif !important; }
header[data-testid="stHeader"]{background:transparent;} #MainMenu, footer{visibility:hidden;}
.block-container{max-width:900px;padding-top:3rem;padding-bottom:4rem;}
.eyebrow{font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:#6B6B63;font-weight:600;}
h1.hero{font-size:2.2rem;line-height:1.15;font-weight:700;letter-spacing:-.02em;margin:.35rem 0 .6rem;}
p.sub{color:#55554E;font-size:1.03rem;max-width:640px;margin-bottom:1.6rem;}
.step{display:flex;align-items:center;gap:.6rem;margin:2rem 0 .7rem;}
.step .n{width:1.6rem;height:1.6rem;border-radius:50%;background:#2F5D50;color:#fff;font-size:.8rem;display:flex;align-items:center;justify-content:center;font-weight:600;}
.step .t{font-weight:600;font-size:1.08rem;}
.card{background:#fff;border:1px solid #E6E4DD;border-radius:12px;padding:.9rem 1rem;margin-bottom:.4rem;}
.card.ok{border-left:4px solid #2F5D50;} .card.warn{border-left:4px solid #C98A2B;} .card.bad{border-left:4px solid #B5483B;}
.quote{color:#6B6B63;font-size:.88rem;margin-bottom:.25rem;} .meaning{font-size:1rem;}
.muted{color:#6B6B63;font-size:.85rem;}
.chips span{display:inline-block;background:#fff;border:1px solid #E6E4DD;border-radius:999px;padding:.15rem .6rem;margin:.12rem .18rem .12rem 0;font-size:.82rem;}
table.tt{width:100%;border-collapse:separate;border-spacing:4px;table-layout:fixed;}
table.tt,table.tt th,table.tt td,table.tt tr{border:none !important;}
table.tt th{font-size:.72rem;color:#6B6B63;font-weight:600;text-align:left;padding:.15rem .25rem;}
table.tt th:first-child{width:2.4rem;}
table.tt td{border-radius:8px;padding:.35rem .4rem;font-size:.74rem;height:2.4rem;vertical-align:top;background:#EDEFF3;}
table.tt td.p{background:transparent;color:#6B6B63;font-weight:600;}
table.tt td.free{background:#F4F3EF;color:#A5A49C;}
table.tt td .who{display:block;font-size:.64rem;color:#55554E;}
</style>""", unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("parsed", {}); ss.setdefault("result", None); ss.setdefault("read_for", None)

pw = None
try: pw = st.secrets.get("APP_PASSWORD")
except Exception: pass
if pw and not ss.get("authed"):
    st.markdown('<div class="eyebrow">Private prototype</div><h1 class="hero">Chalk n Duster</h1>', unsafe_allow_html=True)
    e = st.text_input("Access code", type="password")
    if e:
        if e == pw: ss.authed = True; st.rerun()
        else: st.error("That code isn't right.")
    st.stop()

st.markdown(f"""<div class="eyebrow">Chalk n Duster · {VERSION}</div>
<h1 class="hero">Describe the timetable.<br>We'll build it.</h1>
<p class="sub">Type the rules the way you'd say them to a colleague. The system shows what it understood,
asks when it's unsure, and builds a timetable. If none is possible, it names the rules that clash.</p>""",
unsafe_allow_html=True)

def step(n, t): st.markdown(f'<div class="step"><div class="n">{n}</div><div class="t">{t}</div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- 1. school
step(1, "The school")
pick = st.radio("School", [UPLOAD] + list(DEMOS), label_visibility="collapsed")
sheet_rules = []
bands = {}
if pick == UPLOAD:
    st.markdown('<div class="muted">One workbook, six tabs: Structure, Sections, Curriculum, '
                'Allocation, Groups and Rules. Download the filled KMBVM example from the repo '
                'to see the shape.</div>', unsafe_allow_html=True)
    up = st.file_uploader("School workbook (.xlsx)", type=["xlsx"], label_visibility="collapsed")
    if not up: st.stop()
    import template
    raw, sheet_rules = template.read_workbook(up)
    if not raw: st.error("No bands found. Check the Structure and Sections tabs."); st.stop()
    bands = {k: School(v) for k, v in raw.items()}
    path = "upload"
else:
    path = DEMOS[pick]
    try:
        spec = json.load(open(path))
        if "bands" in spec:                     # a whole school: several bands, built in order
            bands = {k: School.load(v) for k, v in spec["bands"].items()}
            bands = {k: bands[k] for k in spec["order"] if k in bands}
        else:                                   # one band on its own
            bands = {spec.get("band", "all"): School(spec)}
    except FileNotFoundError as e:
        st.error(f"A data file is missing from the deployment: {e}. Upload the data/ folder.")
        st.stop()
    except Exception as e:
        st.error(f"Could not read {path}: {e}"); st.stop()
school = list(bands.values())[0]        # the first band defines days, periods and the break
if ss.get("school_path") != path:
    ss.school_path, ss.parsed, ss.result, ss.read_for = path, {}, None, None
all_secs = [s for b in bands.values() for s in b.sections]
all_teach = sorted({t for b in bands.values() for t in b.teachers})
st.markdown(f'<div class="muted">{len(all_secs)} sections in {len(bands)} bands · {len(school.days)} days · '
            f'{school.periods} periods a day · break after period {school.lunch_after} · '
            f'{len(all_teach)} teachers</div>'
            '<div class="chips" style="margin-top:.45rem">'
            + "".join(f"<span>{BAND_LABEL.get(k, k)}: {len(b.sections)} sections</span>"
                      for k, b in bands.items()) + "</div>"
            '<div class="muted" style="margin-top:.4rem">Bands are built in this order, because teachers '
            'are shared: each band fixes its teachers\' time before the next one is built.</div>',
            unsafe_allow_html=True)
if school.unstaffed:
    st.markdown(f'<div class="muted" style="margin-top:.4rem">{len(school.unstaffed)} (section, subject) '
                'pairs in the real data name a group of teachers rather than one, so they are scheduled '
                'without a teacher constraint for now.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- 2. rules
step(2, "Your rules")
default = ("\n".join(r[1] for r in sheet_rules) if sheet_rules
           else EXAMPLES.get(path, "No teacher should teach more than 4 periods in a row"))
if sheet_rules:
    st.markdown(f'<div class="muted">{len(sheet_rules)} rules came from the workbook\'s Rules tab. '
                'Edit them here if you want.</div>', unsafe_allow_html=True)
text = st.text_area("One rule per line", default, height=130, label_visibility="collapsed")
st.markdown('<div class="muted">Understands: periods in a row, periods per day, teacher availability, '
            'subjects kept out of periods, repeats per day, no same subject back to back, free-period '
            'limits, a required mid-day break, fixed slots, and double periods. Words like <i>ideally</i> '
            'make a rule a preference.</div><div style="height:.6rem"></div>', unsafe_allow_html=True)
sentences = [l.strip() for l in text.splitlines() if l.strip()]
name, READER = R.get_reader()

if st.button("Read my rules", type="primary"):
    todo = [s for s in sentences if s not in ss.parsed]
    bar = st.progress(0.0, text="Reading your rules…")
    from concurrent.futures import ThreadPoolExecutor
    def one(s):
        try: return s, R.interpretations(school, s, READER)
        except Exception as e: return s, str(e)
    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for s, got in pool.map(one, todo):
            ss.parsed[s] = got; done += 1
            bar.progress(done / max(len(todo), 1), text=f"Read {done} of {len(todo)}…")
    bar.empty(); ss.read_for, ss.result = sentences, None

# ---------------------------------------------------------------- 3. check
if ss.read_for == sentences and sentences:
    step(3, "Check what I understood")
    rules = []
    for i, s in enumerate(sentences, 1):
        got = ss.parsed.get(s)
        q = f'<div class="quote">Rule {i} · “{html.escape(s)}”</div>'
        if isinstance(got, str) or got is None:
            st.markdown(f'<div class="card bad">{q}<div class="meaning">Skipped: {html.escape(got or "")}</div></div>',
                        unsafe_allow_html=True); continue
        opts, why = got
        key = f"r{i}_{abs(hash(s))}"
        if why is None:
            f = opts[0][0]
            st.markdown(f'<div class="card ok">{q}<div class="meaning">{html.escape(R.describe(school, f, False))}</div></div>',
                        unsafe_allow_html=True)
        else:
            total = sum(n for _, n in opts)
            st.markdown(f'<div class="card warn">{q}<div class="meaning">I\'m not sure what you meant here.</div>'
                        f'<div class="muted">Why: {why}.</div></div>', unsafe_allow_html=True)
            labels = [R.describe(school, of, False) + (f"  ·  {n} of {total} readings"
                                                       if n and total > 1 else "")
                      for of, n in opts]
            chosen = st.radio("Which did you mean?", labels, key=key + "_p")
            f = opts[labels.index(chosen)][0]
        hard = st.toggle("Must hold (off = preference)", value=f["hard"], key=key + "_h")
        rules.append((f"Rule {i}", {**f, "hard": hard}))

    step(4, "Timetable")
    if st.button("Build the timetable", type="primary", disabled=not rules):
        out, com, bar = {}, {}, st.progress(0.0, text="Building…")
        t0 = time.time()
        for i, (key, band) in enumerate(bands.items()):
            label = BAND_LABEL.get(key, key)
            bar.progress(i / len(bands), text=f"Building {label}…")
            keep = [(l, f) for l, f in rules
                    if f.get("teacher") in (None, "ALL") or f["teacher"] in band.teachers]
            mine = {t: v for t, v in com.items() if t in band.teachers}
            r = solve(band.subset(band.sections, mine), keep, seconds=CAP)
            out[key] = (r, band)
            if not r.get("ok"): break
            # the teacher time this band has used, read from the solved model: a regrouped
            # lesson counts once and a shared load counts for whoever took it
            for t, slots in r["busy"].items():
                com.setdefault(t, set()).update(slots)
        bar.empty()
        ss.result = (out, rules, {f"Rule {i}": s for i, s in enumerate(sentences, 1)},
                     round(time.time() - t0, 1))

    if ss.result:
        out, used, texts, took = ss.result
        done = sum(1 for r, _ in out.values() if r.get("ok"))
        st.markdown(f'<div class="muted">{done} of {len(out)} bands built in {took}s</div>',
                    unsafe_allow_html=True)
        for key, (res, band) in out.items():
            school = band
            st.markdown(f'<div class="step" style="margin-top:1.2rem"><div class="n">'
                        f'{list(out).index(key)+1}</div><div class="t">'
                        f'{BAND_LABEL.get(key, key)}</div></div>', unsafe_allow_html=True)
            if res.get("ok"):
                msg = "All rules satisfied." if not res["broken"] else "Built, but some preferences could not be met."
                st.markdown(f'<div class="card ok"><div class="meaning">{msg}</div>'
                            f'<div class="muted">solved in {took}s</div>'
                            + "".join(f'<div class="muted">{l}: {html.escape(texts[l])}</div>' for l in res["broken"])
                            + "</div>", unsafe_allow_html=True)
                tabs = st.tabs(school.sections)
                for tab, c in zip(tabs, school.sections):
                    g = res["grids"][c]
                    rows = "<tr><th></th>" + "".join(f"<th>{d}</th>" for d in school.days) + "</tr>"
                    for p, row in enumerate(g):
                        if school.lunch_after and p == school.lunch_after:
                            rows += f'<tr><td class="p"></td><td class="free" colspan="{len(school.days)}" style="height:1rem">lunch</td></tr>'
                        cells = "".join(
                            f'<td>{x}<span class="who">{school.teacher_of(c, x) or ""}</span></td>' if x
                            else '<td class="free">free</td>' for x in row)
                        rows += f'<tr><td class="p">P{p+1}</td>{cells}</tr>'
                    tab.markdown(f'<table class="tt">{rows}</table>', unsafe_allow_html=True)
            else:
                core = res.get("conflict")
                if core:
                    head = ("This rule cannot be satisfied on its own." if len(core) == 1 else
                            "No timetable can satisfy these rules together. Relax or remove any one of them.")
                    body = "".join(f'<div style="margin-top:.45rem"><b>{l}</b> · “{html.escape(texts[l])}”'
                                   f'<div class="muted">{html.escape(R.describe(school, dict(used)[l], False))}</div></div>'
                                   for l in core)
                    st.markdown(f'<div class="card bad"><div class="meaning">{head}</div>{body}'
                                '<div class="muted" style="margin-top:.6rem">Your answers in step 3 can change this: '
                                'try the other reading of a rule, or make one a preference.</div></div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="card bad"><div class="meaning">No timetable found in {SOLVE_CAP}s.</div>'
                                '<div class="muted">Rules about teachers\' free periods are the expensive ones. '
                                'Try removing one, or run it from the command line with a longer limit.</div></div>',
                                unsafe_allow_html=True)

st.markdown("<div style='height:2rem'></div><div class='eyebrow'>How it works</div>"
            "<div class='muted' style='margin-top:.4rem'>An AI turns each sentence into a fixed, checkable "
            "form and never writes solver code. Each rule is read three times: where the readings disagree, "
            "or a detail was never stated, the system asks. A constraint solver then builds the timetable, "
            "or finds the smallest set of rules that clash.</div>", unsafe_allow_html=True)
st.markdown(f'<div class="muted" style="margin-top:1rem">{VERSION} · 12 rule types · rule reader: {name}</div>',
            unsafe_allow_html=True)
