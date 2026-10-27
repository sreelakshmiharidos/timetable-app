# The data model: what a timetable grid actually contains

*KMBVM Pottore, 2026-27. 27 October 2026.*

The school's timetable is a grid of two layers: a subject label and a teacher label per cell.
The whole difficulty of the project turned out to be that **the same visual pattern in that grid
means four different things**, and a model that reads it one way cannot reproduce the school's
own timetable. Until these four were separated, the school's real timetable came out
**infeasible** in our model for every band. Once they were separated, all four bands reproduce,
and the system can also build the school from scratch.

## The test

Two questions, both answerable without asking anyone:

1. **Reproduction.** Pin every lesson to the slot the school actually used. Is that
   assignment feasible under our constraints? If not, our model asserts something false
   about the school.
2. **Cold start.** Given only the derived instance — curricula, staffing, rules — can the
   system build a timetable from nothing?

Reproduction is the honest test, because the school's timetable is known to work.

## The four things that look alike

### 1. An in-section split
One cell, several teacher codes, one section: the class divides and goes to several rooms at
once. `SCI LAB` under `UPR/REM/TSD` is physics, chemistry and biology running simultaneously
for thirds of one class. **Every named teacher is busy for every lesson of that pair.**

### 2. A regroup across sections
The same teacher code appears in two sections in the same period. A teacher cannot be in two
rooms, so those two groups are *one class*: the sections' students regroup.

- `DMD` (dance, music, drawing) under `V/A/S`: two sections at a time, three specialists —
  8A+8B Mon P2, 7A+7B Mon P3, 6A+6B Mon P6, 6C+6D Tue P2, 8C+8D Fri P4, 7C+7D Fri P6.
- `M/IP/P` across 11E, 11F, 11G, and again across 12A, 12D, 12E.
- Languages in 10A, 10B and 10C together under one teacher, six times a week.
- 11A's biology students sitting in 11E's biology lesson — *different labels*, same teacher.

**The teacher is occupied once, not once per section.** Detected empirically: shared teacher
plus overlapping subject name, where a laboratory and its subject count as the same subject
(`BIO LAB` ≡ `BIO`). That last equivalence is what catches the cross-label cases.

### 3. A shared load
One teacher per cell, but two teachers over the week. 12B English is ANR five times and BIN
once. This is *not* a split: one of them takes each lesson, and each teacher's weekly share is
fixed. Modelled with a per-teacher choice variable under each lesson.

Treating this as a split was the single most damaging error: booking every named teacher for
every lesson pushed ANR to 47 periods in a 45-period week, which alone made the school
unsolvable.

### 4. A double-period continuation
In grades 11-12 every laboratory is a double period, written as a label followed by a blank.
The blank is not free time — the class and its teachers are still there. **This has to be
filled in before anything else is measured**, because regroups, teacher loads and conflicts
are all counted from the expanded grid. The last two unexplained conflicts in 11-12 were
exactly this.

## What being taught by the same teacher does *not* mean

Two sections sharing a teacher are not automatically one block. ANR teaches 12B and 12E
English together five times a week and separately once. They share a teacher; they are not
locked to the same period. Sections are tied to a common slot **only where their own grid never
separates them.**

## Cells the model cannot explain

The same reasoning finds errors in the source. A single appearance by a teacher who takes that
subject nowhere else in the band is a cell written in the wrong row, not a teaching assignment.
Four were found this way, and the lesson is given to the teacher who takes the rest:

| Teacher | Appears in | Actually teaches |
|---|---|---|
| ANR | 11B physics | English |
| ADS | 10B English | maths |
| ANP | 6C Hindi | English |
| PMN | 6D English | computer science / maths |

PMN was confirmed as Priya Mahadevan, who teaches maths and computing — which is
what prompted the general test. One further cell is reported and unexplained: `ANP` in 6C Hindi
and 8C English in the same period, different grades, unrelated subjects.

## Slots that do not exist

Grades 1-5 open with a zero period on **Thursday only**: 46 slots in a week, not 45. The model
carries a set of closed slots, per school or per section, so an irregular day needs no special
case anywhere else. In a single whole-school solve the zero period is closed for every
secondary section and open for the primary ones.

## Results

**Reproduction** — their own timetable, every lesson pinned where they put it:

| Band | Sections | Lessons pinned | Result |
|---|---|---|---|
| 11-12 | 12 | 474 | feasible |
| 9-10 | 8 | 360 | feasible |
| 6-8 | 12 | 540 | feasible |
| 1-5 | 18 | 828 | feasible |

**Cold start** — built from the instance alone, bands in the committee's own order
(11-12, 9-10, 6-8, 1-5), each against the teacher time the earlier bands have spent, with the
school's stated rules:

| Band | Result | Time | Rules |
|---|---|---|---|
| 11-12 | optimal | 90 s | 51 |
| 9-10 | optimal | 17 s | 32 |
| 6-8 | optimal | 170 s | 24 |
| 1-5 | feasible, 6 preferences given up | 200 s | 26 |

Checked independently: **0** sections with the wrong lesson counts, **0** teachers in two
places at once anywhere in the school.

## Rules used in the cold start

As stated by Jyothy Tr, who does the timetabling, each as a typed form the translator turns into
constraints:

- every laboratory is a double period (hard);
- no laboratory in period 1 — that period belongs to the class teacher (hard);
- games never in period 1 (hard);
- games and yoga at most once a day (hard);
- no subject twice in a row, outside doubles (preference);
- no teacher more than four periods in a row (preference).

Preferences are reported when given up rather than silently dropped: grades 1-5 gave up six.

## Why band-by-band is the real product

The committee schedules 11-12 first, then 9-10, then 6-8, then 1-5, because 30 teacher codes
appear in both 6-8 and 9-10 and 11 appear in all three secondary bands. Each band fixed removes
availability from the next. A system that could only solve the school in one pass would not fit
how they work, so building one band against an already-fixed one is a requirement, not an
optimisation.

## One pass versus band by band

Solving all 50 sections in a single pass returns UNKNOWN after five and a half minutes: the
model is built and consistent, but the search does not close. Fixing the band-by-band answer
into that same one-pass model and asking whether it holds comes back **optimal**, so the
one-pass formulation is correct and merely hard to search — a result worth stating, because it
separates a modelling fault from a search cost.

Getting that answer also exposed a real fault. The first attempt laid the four bands on a common
grid by starting the shorter days later, which moved the lunch break relative to each band's own
periods, and a laboratory double that is legal in its own band then straddled the break. The
conflict explainer named the single offending rule — `BIO/CS LAB is a double period` — in 0.2
seconds, out of 100 rules. Each band now keeps its own period numbers and has the surplus slots
at the end of the day closed instead.
