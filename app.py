import html, os
import streamlit as st

st.set_page_config(page_title="Timetable, described", page_icon="🗓️", layout="centered")

# secrets -> env so pipeline.get_reader() finds them
for k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
    try:
        if k in st.secrets: os.environ[k] = st.secrets[k]
    except Exception:
        pass
import pipeline as P

# ------------------------------------------------------------------ style
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea, .stTextArea textarea { font-family: 'Inter', sans-serif !important; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 860px; padding-top: 3rem; padding-bottom: 4rem; }
.eyebrow { font-size: .75rem; letter-spacing: .08em; text-transform: uppercase; color: #6B6B63; font-weight: 600; }
h1.hero { font-size: 2.3rem; line-height: 1.15; font-weight: 700; letter-spacing: -.02em; margin: .35rem 0 .6rem; color:#1C1C1A; }
p.sub { color: #55554E; font-size: 1.05rem; max-width: 620px; margin-bottom: 1.8rem; }
.step { display:flex; align-items:center; gap:.6rem; margin: 2.2rem 0 .7rem; }
.step .n { width:1.6rem; height:1.6rem; border-radius:50%; background:#2F5D50; color:#fff; font-size:.8rem;
           display:flex; align-items:center; justify-content:center; font-weight:600; }
.step .t { font-weight:600; font-size:1.1rem; }
.card { background:#fff; border:1px solid #E6E4DD; border-radius:12px; padding:1rem 1.1rem; margin-bottom:.4rem; }
.card.warn { border-left: 4px solid #C98A2B; }
.card.ok { border-left: 4px solid #2F5D50; }
.card.bad { border-left: 4px solid #B5483B; }
.quote { color:#6B6B63; font-size:.9rem; margin-bottom:.3rem; }
.meaning { font-size:1rem; color:#1C1C1A; }
.badge { display:inline-block; font-size:.7rem; font-weight:600; padding:.12rem .5rem; border-radius:999px; margin-left:.4rem; vertical-align:middle; }
.b-must { background:#E4EEEA; color:#2F5D50; } .b-pref { background:#F1F0EB; color:#6B6B63; }
.b-ask { background:#FBEFD9; color:#8A5A12; }
.muted { color:#6B6B63; font-size:.85rem; }
.chips span { display:inline-block; background:#fff; border:1px solid #E6E4DD; border-radius:999px; padding:.2rem .65rem; margin:.15rem .2rem .15rem 0; font-size:.85rem; }
table.tt, table.tt th, table.tt td, table.tt tr { border:none !important; }
table.tt { width:100%; border-collapse:separate; border-spacing:4px; table-layout:fixed; }
table.tt th { font-size:.75rem; color:#6B6B63; font-weight:600; text-align:left; padding:.2rem .3rem; }
table.tt td { border-radius:8px; padding:.45rem .5rem; font-size:.82rem; height:2.9rem; vertical-align:top; }
table.tt th:first-child { width:2.6rem; }
table.tt td.p { background:transparent; color:#6B6B63; font-weight:600; width:2.6rem; }
table.tt td .who { display:block; font-size:.7rem; color:#55554E; }
table.tt td.free { background:#F4F3EF; color:#A5A49C; }
table.tt tr.lunch td { height:auto; padding:.1rem; text-align:center; font-size:.68rem; letter-spacing:.08em; color:#A5A49C; background:transparent; }
.how { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin-top:.6rem; }
.how div { background:#fff; border:1px solid #E6E4DD; border-radius:12px; padding:.9rem; font-size:.88rem; color:#55554E; }
.how b { display:block; color:#1C1C1A; margin-bottom:.25rem; }
@media (max-width: 640px) { .how { grid-template-columns:1fr; } h1.hero { font-size:1.8rem; } table.tt td { font-size:.7rem; } }
</style>
""", unsafe_allow_html=True)

COLORS = {"Maths": "#E3ECF7", "English": "#F6E7D8", "Science": "#E2F0E6",
          "Malayalam": "#F3E3EC", "Social": "#ECE8F6", "PE": "#F7F1D6"}
EXAMPLE = """No teacher should teach more than 3 periods in a row
Suma is not available on Monday
No PE in the first period
No subject more than twice a day"""

# ------------------------------------------------------------------ password gate
def _secret(name):
    try: return st.secrets.get(name)
    except Exception: return None

pw = _secret("APP_PASSWORD")
if pw and not st.session_state.get("authed"):
    st.markdown('<div class="eyebrow">Private prototype</div><h1 class="hero">Timetable, described</h1>', unsafe_allow_html=True)
    entered = st.text_input("Access code", type="password")
    if entered:
        if entered == pw: st.session_state.authed = True; st.rerun()
        else: st.error("That code isn't right.")
    st.stop()

ss = st.session_state
ss.setdefault("parsed", {})      # sentence -> (options, reason) or error string
ss.setdefault("result", None)
ss.setdefault("read_for", None)

AI_NAME, READER = P.get_reader()

# ------------------------------------------------------------------ hero
st.markdown(f"""
<div class="eyebrow">Prototype v1</div>
<h1 class="hero">Describe the timetable.<br>We'll build it.</h1>
<p class="sub">Type your school's rules the way you'd say them to a colleague. The system shows what it understood,
asks when it's unsure, and builds a timetable. If none is possible, it tells you which rules clash.</p>
""", unsafe_allow_html=True)

def step(n, title):
    st.markdown(f'<div class="step"><div class="n">{n}</div><div class="t">{title}</div></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ 1. school
step(1, "The school")
st.markdown(
    f'<div class="muted">A sample school: {len(P.CLASSES)} classes, {len(P.DAYS)} days, '
    f'{P.PERIODS} periods a day, lunch after period {P.LUNCH_AFTER}.</div>'
    '<div class="chips" style="margin-top:.5rem">' +
    "".join(f"<span><b>{t}</b> · {s} · {P.LESSONS_PER_WEEK[s]}/week</span>" for t, s in P.TEACHERS.items()) +
    "</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------ 2. rules
step(2, "Your rules")
text = st.text_area("One rule per line", EXAMPLE, height=130, label_visibility="collapsed")
st.markdown('<div class="muted">Understands: periods in a row, periods per day, when a teacher is unavailable, '
            'subjects kept out of certain periods, and how often a subject repeats in a day. '
            'Words like <i>ideally</i> or <i>if possible</i> make a rule a preference.</div>'
            '<div style="height:.6rem"></div>', unsafe_allow_html=True)
sentences = [l.strip() for l in text.splitlines() if l.strip()]

if st.button("Read my rules", type="primary"):
    with st.spinner("Reading each rule a few times…"):
        for s in sentences:
            if s not in ss.parsed:
                try: ss.parsed[s] = P.interpretations(s, READER)
                except Exception as e: ss.parsed[s] = str(e)
    ss.read_for = sentences; ss.result = None

# ------------------------------------------------------------------ 3. check
if ss.read_for and ss.read_for == sentences:
    step(3, "Check what I understood")
    rules = []
    for i, s in enumerate(sentences, 1):
        got = ss.parsed.get(s)
        q = f'<div class="quote">Rule {i} · “{html.escape(s)}”</div>'
        if isinstance(got, str) or got is None:
            st.markdown(f'<div class="card bad">{q}<div class="meaning">I couldn\'t turn this into a rule I know. '
                        f'It will be skipped.</div><div class="muted">{html.escape(got or "")}</div></div>',
                        unsafe_allow_html=True)
            continue
        opts, why = got
        key = f"r{i}_{abs(hash(s))}"
        if why is None:
            f = opts[0][0]
            st.markdown(f'<div class="card ok">{q}<div class="meaning">{html.escape(P.describe(f, notes=False))}</div></div>',
                        unsafe_allow_html=True)
        else:
            total = sum(n for _, n in opts)
            st.markdown(f'<div class="card warn">{q}<div class="meaning">I\'m not sure what you meant here'
                        f'<span class="badge b-ask">Needs your input</span></div>'
                        f'<div class="muted">Why I\'m asking: {why}.</div></div>', unsafe_allow_html=True)
            labels = [P.describe(f, notes=False) + (f"  ·  {n} of {total} readings" if n and total > 1 else "") for f, n in opts]
            pick = st.radio("Which did you mean?", range(len(opts)), format_func=lambda j: labels[j], key=key + "_pick")
            f = opts[pick][0]
        hard = st.toggle("Must hold (off = preference)", value=f["hard"], key=key + "_hard")
        rules.append((f"Rule {i}", {**f, "hard": hard}))

    step(4, "Timetable")
    if st.button("Build timetable", type="primary", disabled=not rules):
        with st.spinner("Solving…"):
            ss.result = (P.solve(rules), rules, dict(zip([l for l, _ in rules], sentences)))

    if ss.result:
        res, used, _ = ss.result
        texts = {f"Rule {i}": s for i, s in enumerate(sentences, 1)}
        if res["ok"]:
            msg = "All rules satisfied." if not res["broken"] else "Built, but some preferences couldn't be met."
            st.markdown(f'<div class="card ok"><div class="meaning">{msg}</div>' +
                        "".join(f'<div class="muted">{l}: {html.escape(texts[l])}</div>' for l in res["broken"]) +
                        "</div>", unsafe_allow_html=True)
            tabs = st.tabs([f"Class {c}" for c in P.CLASSES])
            for tab, c in zip(tabs, P.CLASSES):
                g = res["grids"][c]
                rows = "<tr><th></th>" + "".join(f"<th>{d}</th>" for d in P.DAYS) + "</tr>"
                for p, row in enumerate(g):
                    if p == P.LUNCH_AFTER:
                        rows += f'<tr class="lunch"><td></td><td colspan="{len(P.DAYS)}">LUNCH</td></tr>'
                    cells = "".join(
                        f'<td style="background:{COLORS[s]}">{s}<span class="who">{P.SUBJECT_TEACHER[s]}</span></td>'
                        if s else '<td class="free">free</td>' for s in row)
                    rows += f'<tr><td class="p">P{p+1}</td>{cells}</tr>'
                tab.markdown(f'<table class="tt">{rows}</table>', unsafe_allow_html=True)
        else:
            core = res.get("conflict")
            if core:
                head = ("This rule can't fit the lesson counts on its own." if len(core) == 1 else
                        "No timetable can satisfy these rules together. Relax or remove any one of them.")
                body = "".join(f'<div style="margin-top:.5rem"><b>{l}</b> · “{html.escape(texts[l])}”'
                               f'<div class="muted">{html.escape(P.describe(dict(used)[l], notes=False))}</div></div>'
                               for l in core)
                st.markdown(f'<div class="card bad"><div class="meaning">{head}</div>{body}'
                            f'<div class="muted" style="margin-top:.7rem">Tip: your answers in step 3 can change this. '
                            f'Try the other reading of a rule, or make one a preference.</div></div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="card bad"><div class="meaning">No timetable found.</div>'
                            f'<div class="muted">{res.get("note", "The lesson counts themselves do not fit.")}</div></div>',
                            unsafe_allow_html=True)

# ------------------------------------------------------------------ how it works
st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
st.markdown("""
<div class="eyebrow">How it works</div>
<div class="how">
  <div><b>1 · Read</b>An AI turns each sentence into a fixed, checkable form. It never writes solver code.</div>
  <div><b>2 · Ask</b>Each rule is read several times. Where readings disagree, or a detail was never said, it asks you.</div>
  <div><b>3 · Solve & explain</b>A constraint solver builds the timetable, or finds the smallest set of rules that clash.</div>
</div>
""", unsafe_allow_html=True)
st.markdown(f'<div class="muted" style="margin-top:1.2rem">Rule reader: {AI_NAME}</div>', unsafe_allow_html=True)
