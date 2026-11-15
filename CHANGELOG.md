# Changelog

## v0.13 - 16 November 2026

The built-in reader tested against 35 sentences phrased the way a new user might type them.
Before: 26 read correctly, 5 declined, 4 misread. After: 33 correct, 2 declined, 0 misread.

- "Physics should be in the afternoon" was read as "no physics in period 1", and "PT should not be
  after lunch" the same way. Morning, afternoon, before lunch and after lunch now map to the
  school's own periods either side of the break, in the direction the sentence states.
- A sentence naming a subject but no time now declines instead of defaulting to period 1.
- "ANR can teach at most 2 periods back to back" was read as a same-subject rule; back to back
  about a teacher is now a run-length rule for that teacher.
- "Once" is understood as 1. "Maths", "social studies" and "physical education" map to MTS, SS and
  PT where those subjects exist.
- "Try not to", "where possible" and similar now make a rule a preference.
- "ANR should not teach in the last period" is read as that teacher being unavailable then.
- The two sentences still declined are ones the reader cannot settle: "labs" when the school has
  four kinds of lab, and a minimum number of lessons per day, which has no rule type yet.

## v0.12 - 16 November 2026

Fixes to the built-in rule reader, found while rehearsing the demonstration.

- "9A should have PT in the first period" was read as "No PT in period 1, every section": the
  built-in reader had no case for placing a subject, so any sentence naming a subject and a
  period fell through to forbidding it. Positive placement ("should have", "must be", "is in")
  now becomes a fixed slot, with the section and day taken from the sentence where stated. A
  sentence that forbids a subject now also respects a named section.
- Names were matched as raw substrings. "SS" matched inside "assembly" and "class", teacher codes
  such as "DAN" inside "dance", "CHE" inside "teaches", and the single-letter code "A" matched the
  English word "a". Subjects now match whole words, teacher codes match case-sensitively and only
  from two characters, and the "science lab" style fallback matches from the start of a word.
- Where a phrase matches several subjects equally well, the reader now declines rather than
  picking the first one.
- Tested on grades 9-10: the four demonstration rules solve in about 13 s; adding "9A should
  have PT in the first period on Monday" is reported as a conflict between those two rules.

## v0.11 - 4 November 2026

Fixes found by testing the deployment rather than the local machine.

- Solve limit raised from 150s to 300s a band. The deployment runs on slower hardware than the
  machine the report's timings were measured on, and grades 1-5 was exceeding the old limit.
- The timeout message said 60s while the solver had actually run for the full limit. It now
  reports the real limit and says plainly that a timeout is not a proof of infeasibility.
- The footer no longer names which rule reader is active; it was an internal detail.
- Gemini requests were timing out on the deployment. The request timeout is raised from 45s to
  90s and sentences are now read one at a time rather than four, so the burst is 3 concurrent
  requests instead of 12, which the free tier tolerates.
- A rule was dropped when the reader returned a reply with no JSON in it. Each sample now retries
  once, output tokens raised from 700 to 1200, and the failure is reported in plain English with
  the reason in brackets rather than as a raw Python exception.

## v0.10 - 4 November 2026

The template is now downloadable from the web application itself rather than from the
repository, after the comment that the code is not what a reader looks at.

- `app.py`: two download buttons on the upload step, a blank template and the filled KMBVM
  example, served from `data/`.
- `data/template_blank.xlsx`: the six tabs with their headings and the Read me, nothing filled in,
  built by `template.write_workbook({}, ...)`.

## v0.9 - 28 October 2026

The coordinator's answers, applied. Three questions answered, two rules reclassified, and the
regroup rule confirmed by arithmetic.

- **The regroup rule, confirmed.** SMT appears in 61 cells of the grades 11-12 grid and teaches
  33 periods. The coordinator's explanation is the rule in her own words: where her name appears
  across several classes in the same period, those classes are regrouped into one group she
  takes. Collapsing regroups as the model does gives exactly 33.
- **Two rules are preferences, not rules.** No laboratory in the first period (broken once in 37,
  because nothing else fit) and no laboratory double across lunch (broken six times; the class
  goes to lunch and comes back). Both are now preferences the system reports when it breaks them,
  and the cold start keeps both in all four bands, which the school's own timetable does not.
- **Seven fixed slots derived**, on the coordinator's statement that the activity periods cannot
  move because outside teachers come in. Found as a subject every section taking it takes at
  exactly the same slots: the activity block on Wednesday periods 8 and 9 and the Thursday zero
  period, PF on Friday period 1, R3 on Wednesday period 9, and AI/MM/YOGA on Wednesday period 4
  and Friday period 7. The template's Fixed slots tab carries them, and they round-trip.
- R3 noted as a regroup the shared-teacher criterion cannot find, since its four cells name four
  different teachers, one to each language group. The occupancy is right regardless; what the
  grid needed from it was the fixed time.
- ANP in 6C Hindi and 8C English confirmed as a mistake in the sheet.
- All four bands still reproduce. Cold start: grades 11-12, 9-10 and 6-8 optimal, grades 1-5
  feasible with 5 preferences given up. 0 wrong lesson counts, 0 teachers in two places.

## v0.8 - 28 October 2026

The school-facing template, rebuilt around the four structures of the data model, and the round
trip it exists for: hand over the template, get a timetable back.

- One row per subject a class takes, replacing separate Curriculum and Allocation tabs that made
  a coordinator type every pair twice. A row may name a whole grade (`9A-9D`, `grade 9`), so the
  school's 753 section-subject pairs fit in 467 rows.
- The four things a grid cannot show are now asked as questions: whether the teachers named are
  all busy at once or share the week, how the week divides between them, which classes join the
  lesson, and whether it runs as a double.
- `always at the same time?` added after the first version made grades 11-12 infeasible: joining
  a lesson had implied running at the same period, and 12B and 12E take English together five
  times a week and apart once. The grid can show that; a template that only records the join
  cannot, so the template asks.
- Their own timetable is feasible in a model built from the template alone, all four bands.
  Cold from the template: grades 11-12, 9-10 and 6-8 optimal; grades 1-5 needs a warm start,
  which is search cost rather than a modelling fault.
- 11A and 11B modelled as six-period days: those students leave for outside coaching after the
  break, so their afternoon slots are closed rather than free. Previously read as an incomplete
  record. Section day lengths are derived before laboratory doubles are expanded, since a blank
  in the last period attended means going home, not a continuation.
- Break position confirmed after period 6, and the six laboratory doubles that cross it recorded
  as an open question.
- A Read me tab with worked examples in the school's own labels, and dropdowns on the yes/no
  columns.

## v0.7 - 27 October 2026

The data model, rewritten. Four patterns in a school's grid that look identical and mean
different things are now told apart: an in-section split, a regroup across sections, a shared
load between two teachers, and a double-period continuation. Written up in
`kmbvm-data-model.md`; the provenance of every rule is in `rule-record.md`.

- **Reproduction.** The school's own 2026-27 timetable is now feasible in the model for all four
  bands (474, 360, 540 and 828 lessons pinned). Every band was infeasible before this release.
- **Cold start.** The whole school builds from the instance alone, in the committee's own band
  order, with 0 wrong lesson counts and 0 teachers in two places at once.
- Grades 1-5 added, including the Thursday zero period: the model carries closed slots, declared
  for the whole school or for one section.
- Teacher occupancy is read from the solved model rather than re-derived, so a regrouped lesson
  counts once and a shared load counts for whoever took it.
- Regroups are detected from the grid: shared teacher plus overlapping subject name, treating a
  laboratory and its subject as the same subject.
- Sections are aligned in time only where their own grid never separates them. Sharing a teacher
  is not enough.
- Cells the model cannot explain are reported: four teachers appearing in a subject they teach
  nowhere else (ANR, ADS, ANP, PMN), read as cells written in the wrong row.
- `across_break` for lab doubles dropped as an assumption: six of the school's own doubles cross
  the break.
- The app loads a single band on its own, picks workers to suit a one-core host, and no longer
  uses the old teacher-booking path.
- 14 tests, three of them covering the new data model.

## v0.6.1 - correctness fixes and an honest negative result
- `commitments()` recorded the joined string "DPK/TSD" as one teacher, so teachers with shared
  lessons were never blocked in the next band: 39 cross-band double-bookings. Fixed.
- The loader accepts both the single-teacher and multi-teacher instance formats and reports a
  readable error instead of a redacted TypeError.
- One school, not three: the app takes a workbook (or a demo school) and builds its bands in order,
  carrying each band's teacher commitments into the next.
- **Negative result, recorded rather than hidden.** With commitments correct, building 11-12 then
  9-10 makes 6-8 provably infeasible (216s to prove). Solving all 32 sections in one model does not
  finish in 7 minutes either. The likely cause is the data model, not the solver: when sections
  regroup, the same lesson is counted once per section, so a teacher taking one combined group
  appears to need two or three slots. Treating a regrouped lesson as one occupation shared by
  several sections is v0.7.

## v0.6 - the real workbook, every secondary band, and a school-facing input format
Corrections first, all of them mistakes the earlier versions made:
- Codes such as PRC, VIS, SMC, ASK, REM are **teachers** (PRC is Praveen), not
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
