# Changelog

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
