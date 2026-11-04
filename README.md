# Chalk n Duster

Describe a school timetable in plain English; the system fills a typed constraint form,
asks where it is unsure, and hands the form to a CP-SAT solver. When no timetable exists
it reports the smallest set of rules that cannot hold together.

## Layout

    derive_all.py    timetable grid -> machine-readable school, all four bands
    derive.py        the same for one band (earlier, kept for reference)
    template.py      the input workbook: writing a blank or filled one, and reading one back
    rules.py         the typed constraint forms for each band
    run_all.py       solves the bands in order, each against the earlier ones' teacher commitments
    school.py        the data model
    model.py         Layer 2: the translator (constraint forms -> CP-SAT)
    solve.py         solving, conflict extraction, printing
    experiments.py   system-evaluation runs (timings)
    tests/           one test per constraint type
    data/            derived school instances
    reader.py        Layer 1: sentence -> validated constraint form (LLM or offline)
    app.py           Streamlit interface, running the current engine
    pipeline.py      v0.1 single-file prototype (kept for reference)

## Input format

A school fills one workbook with six tabs: Read me, School, Classes, Teaching, Fixed slots and
Rules (`template.py`). Only Teaching is long, and one row there can cover a whole grade. The blank
template is `data/template_blank.xlsx`, and both it and a filled example are downloadable from the
web application itself. That workbook is the production input. Reading a school's finished timetable
(`parse_xl.py`, `derive_all.py`) is how the example was produced and how a school with no template
can start.

## Bands

The school builds grades 11-12 first, then 9-10, then 6-8, then 1-5, because teachers are shared
between bands. `School.subset(sections, committed)` and `solve.commitments()` reproduce that: solve one
band, extract the teacher slots it used, pass them to the next band as fixed unavailability.

## Run

    pip install -r requirements.txt
    python3 derive.py ../data/g910.csv data/kmbvm_9_10.json
    python3 tests/test_rules.py
    python3 experiments.py

## Data

`data/` holds school instances derived from KMBVM Pottore's 2026-27 timetable. **Those files and
`data_raw/` are not in this repository.** They name real teachers and give their whole working week,
so they are kept out until the school agrees to their release. `data/sample_school.json` and
`data/template_blank.xlsx` are here, and they are enough to run everything. The grid
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
| `double_period` | subject, sections, across_break |
| `parallel_block` | subject, sections |
| `shared_resource` | subject, sections, max_at_once |
