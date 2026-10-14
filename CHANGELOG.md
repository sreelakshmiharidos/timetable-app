# Changelog

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
