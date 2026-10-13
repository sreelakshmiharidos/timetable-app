# Chalk n Duster

Describe a school timetable in plain English; the system fills a typed constraint form,
asks where it is unsure, and hands the form to a CP-SAT solver. When no timetable exists
it reports the smallest set of rules that cannot hold together.

## Layout

    derive.py        timetable grid -> machine-readable school (sections, requirements, teachers)
    school.py        the data model
    model.py         Layer 2: the translator (constraint forms -> CP-SAT)
    solve.py         solving, conflict extraction, printing
    experiments.py   system-evaluation runs (timings)
    tests/           one test per constraint type
    data/            derived school instances
    app.py           Streamlit interface (v0.1, being ported to the new model)
    pipeline.py      v0.1 single-file prototype (kept for reference)

## Run

    pip install -r requirements.txt
    python3 derive.py ../data/g910.csv data/kmbvm_9_10.json
    python3 tests/test_rules.py
    python3 experiments.py

## Data

`data/` holds school instances derived from KMBVM Pottore's 2026-27 timetable. The grid
the school produced is the *output* of their manual process; what the solver needs is the
*input* behind it, which `derive.py` extracts: how many lessons each section takes of each
subject, and which teacher takes which (section, subject) pair.

## Constraint types

| type | fields |
|---|---|
| `max_consecutive` | teacher, max, lunch_breaks_run |
| `max_per_day` | teacher, max |
| `teacher_unavailable` | teacher, days, periods |
| `subject_not_in_periods` | subject, sections, periods |
| `max_subject_per_day` | subject, sections, max |
| `no_consecutive_same_subject` | subject, sections |
| `max_gaps_per_day` | teacher, max |
| `require_midday_gap` | teacher, periods, min_lessons |
| `fixed_slot` | subject, sections, days, periods |
