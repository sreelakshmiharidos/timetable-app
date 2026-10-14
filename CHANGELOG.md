# Changelog

## v0.6 - the real workbook, every secondary band, and a school-facing input format
Corrections first, all of them mistakes the earlier versions made:
- Codes such as PRC, VIS, SMC, ASK, REM are **teachers** (Praveen, Vismaya, Suma, Ashok...), not
  support markers. They were excluded from clash checking; they no longer are.
- A cell naming several teachers inside one section means the class **splits**: SCI LAB under
  UPR/REM/TSD is physics, chemistry and biology in three rooms. All named teachers are now booked.
- The same label in the same slot across sections means the sections **regroup**, and each teacher
  takes one group. Booking all of them gave SMT 73 lessons a week; one per section fixes it.
- The break falls after period 5, not 4.
- Section letters past E exist (11F, 11G) and were being dropped by the parser.
- Grades 11A and 11B use 30-31 of 45 slots because they leave for an integrated JEE programme,
  not because the record is incomplete.

New:
- `parse_xl.py` reads the school's own workbook directly instead of a hand transcription, finding
  the period columns rather than assuming them.
- `derive_all.py` builds one instance per band: 11-12 (12 sections, 37 teachers),
  9-10 (8 sections, 60 teachers), 6-8 (12 sections, 65 teachers).
- Whole secondary school solved in the committee's order: 11-12 in 184s, then 9-10 in 46s against
  those commitments, then 6-8 in 23s. 166 teacher codes scheduled, no cross-band clash.
- `template.py`: the school-facing input format, one workbook with Structure, Sections, Curriculum,
  Allocation, Groups and Rules tabs, written and read back. A filled example for KMBVM is in
  `data/kmbvm_input_template.xlsx`.
- The app can now take that workbook as an upload, pick a band, and read the rules straight from
  the Rules tab.

## v0.6 - grades 11 and 12, and the whole secondary school in sequence
- `derive1112.py` reads the senior grid, where a blank cell after a laboratory means the lesson
  continues into the next period. 12 sections, 33 subjects, 27 teachers.
- Sections are streams, so the curriculum is per section: 11A and 11B use 30-31 of the 45 slots
  while every other senior section uses all 45.
- Elective blocks are detected from the grid: M/IP/P across 11E, 11F and 11G and again across
  12A, 12D and 12E, seven periods a week each; AI/MM/YOGA across five sections.
- Whole secondary school solved the way the committee works: 11-12 with 19 structural rules in
  2.9s, then 9-10 against those teachers' commitments in 6.3s. 15 teachers are shared between the
  bands and none is double-booked.
- Assumptions, recorded in the instance under `assumed` rather than left silent: a blank after a
  laboratory is a continuation; the first teacher named in a cell is the one scheduled; where a
  block names fewer teachers than it has groups, one teacher per remaining group is invented.

## v0.5 - sequenced bands
- A school can now be split into bands and solved one after another, which is how the committee
  works: `School.subset(sections, committed)` builds a band, and `commitments()` reports the teacher
  slots a solved band has used.
- Teacher time committed by an earlier band becomes fixed unavailability in the next one, so no
  teacher is double-booked across bands.
- Demonstrated on the real data: grade 9 solves in 4.3s, grade 10 then solves against grade 9's fixed
  commitments in 0.2s, with zero cross-band clashes. Solving both bands in a single pass takes 2.4s,
  so sequencing costs time and freedom but reproduces the school's own process.
- Test added for cross-band clashes; 11 tests in total.

## v0.4 - parallel blocks and shared specialists
- `parallel_block`: named sections take a subject in the same periods as each other, so students can
  be re-grouped across sections. This is the elective and language block structure that the school
  uses throughout grades 9 to 12, and that existing tools make hardest to express.
- `shared_resource`: at most N sections (default 1) may take a subject in any one period, for a
  specialist or room serving the whole school. In the primary school, dance, music, drawing, craft,
  library, robotics and computing each behave this way.
- Sections can only run a subject in parallel if they have the same number of lessons of it, so the
  translator rejects a mismatch with the counts rather than leaving the solver to grind on it
  (9C has 4 LANG lessons, 10A has 6: the system says so instead of timing out).
- Both encode cheaply: the full set of four rules including a parallel block solves the real
  grade 9-10 instance in about 5 seconds.
- Tests for both; 10 tests in total.

## v0.3 - double periods, and the web app on real data
- New constraint type `double_period`: every lesson of a subject runs as a block of two
  consecutive periods, and a block may not straddle the lunch break unless `across_break` is set.
- A subject with an odd number of lessons per week correctly reports itself as the conflict.
- `double_period` and `no_consecutive_same_subject` contradict each other, as they should: a
  double period *is* the same subject twice in a row. The system names both rules.
- The Streamlit app now runs the v0.2/v0.3 engine, with a school picker (sample school or the real
  KMBVM grades 9 and 10), all 10 constraint types, a 60s solve cap, and a version line.
- Reader rebuilt for the enlarged schema (`reader.py`), with a no-AI fallback.

## v0.2 - real school data model
- School is now sections + per-section curriculum + teachers assigned to (section, subject)
  pairs, loaded from JSON, instead of a hard-coded sample school with one teacher per subject.
- `derive.py` extracts a school instance from the class-wise timetable grid.
- Loaded KMBVM grades 9 and 10: 8 sections, 21 subjects, 33 teachers, 45 slots per section.
- Four new constraint types: `no_consecutive_same_subject`, `max_gaps_per_day`,
  `require_midday_gap`, `fixed_slot`.
- `require_midday_gap` takes `min_lessons`, because "a free period in the middle of the day"
  is infeasible if applied to every working day and feasible from two lessons upward.
- Tests: one per constraint type.
- First system-evaluation timings on the real instance (`experiments.py`).

## v0.1 - first end-to-end pipeline
- Five constraint types, sample school.
- LLM fills a typed form; three independent parses flag ambiguity; translator to CP-SAT;
  minimal conflict set reported in plain English.
- Streamlit web interface, deployed.
