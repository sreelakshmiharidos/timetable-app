# How the rules were found: a record of the back and forth

*KMBVM Pottore, 2026-27. Kept current from August 2026. Last updated 27 October 2026.*

This is the audit trail behind the constraint set. Nobody at the school had a written list of
timetabling rules, so every rule here came from one of three places, and this document records
which, what we believed first, and what changed when the evidence disagreed.

**Sources**

- **G** — measured from the school's own 2026-27 timetable workbook. Four tabs, about 50
  sections, roughly 2,200 filled cells.
- **J** — stated by **Jyothy Tr**, who does the timetabling at the school, and who is the
  author's mother. That relationship is the reason this school's complete workbook and this
  depth of questioning were available at all, and it is also a limitation: a coordinator who is
  a relative may agree more readily than a stranger. It is declared here and carried into the
  evaluation protocol.
- **S** — stated by **Suma Tr**, the timetable coordinator, in the earlier scoping
  conversations.
- **C** — inferred from how the committee works, then confirmed.

A rule is only treated as hard if someone stated it *and* the grid does not contradict it. Where
those two disagree, the disagreement is recorded rather than resolved quietly. That is the whole
point of the document.

---

## 1. What we asked, and what came back

The first pass measured the grid and produced eight questions. Jyothy Tr's answers, and what
each one settled:

| Asked | Answer | Effect |
|---|---|---|
| When a class splits for labs, does it split within itself or regroup with other classes? | One class splits into three groups and goes to three labs: chemistry, physics, biology. | Established the **in-section split**: all three teachers busy at once for one section. |
| And for `M/IP/P`? | Students from all three classes regroup into maths, informatics or psychology. | Established the **regroup across sections**, a different thing entirely. |
| When does the break fall? | After six periods, confirmed twice. | Set the break position. Independently corroborated: 11A and 11B stop at exactly that point (§3). Six lab doubles still cross it (§3). |
| Why do 11 and 12 get more lab time than 9 and 10? | "It's just how it is." | Not a rule to model; a curriculum fact already in the per-section requirements. |
| What are `R3`, `KV`, `CC/GK`, `D/M/D`, `yoga/kaushal baug`? | R3 is the third language. KV and KV LAB are Kaushal Vikas. CC and GK are subjects that alternate. D/M/D is dance, music, drawing and the class splits. Yoga and Kaushal Baug, the class splits. | Decoded the labels. **The D/M/D answer was contradicted by the grid — see §3.** |
| Are outside instructors on the timetable? | Outside people teach some things, but a monitoring teacher is allotted, activity-wise not class-wise. | Explains why support codes appear in cells. They are real people and must be counted. |
| Is the curriculum fixed? | Board-fixed, with the school adjusting a little. | Requirements are taken from the grid as given, not recomputed. |
| Do you have the rules written down? | No. "Can't you figure it out from the timetable?" | **This is why the project needs the grid as a source at all.** |

Her answer to the last question is the reason this document exists. The rules are not written
anywhere; they live in a working timetable and in the head of the person who builds it.

## 2. The rules, with provenance

| Rule | Source | Strength | Status |
|---|---|---|---|
| A subject may appear twice in a day but not back to back | J, G | preference | Stated by J. Grid agrees: 50 same-day repeats against 2 genuine doubles in 9-10. |
| Games and yoga at most once a day | J | hard | Stated by J as an exception to the rule above. |
| No teacher more than four periods in a row | J, G | preference | J said "try, not hard", so it is modelled as a preference and reported when given up. Grid agrees: longest run is 4 in 6-8 and 9-10. |
| Games never in the first period | J, G | hard | J's reason: the class teacher takes period 1. **Grid confirms exactly: 0 violations in all three secondary bands.** |
| No laboratory in the first period | J, G | preference | Same reason. 1 violation in 37 (11A, Monday P1). Jyothy Tr: they could not avoid it and did not want it, so it is a preference the system reports when it has to break it. |
| A laboratory double should not run across lunch | J, G | preference | Jyothy Tr: it is allowed, the class goes to lunch and comes back, but it is not wanted. Six of 37 doubles do it. Modelled as a required double plus a preference against crossing. |
| Activity periods, R3 and PF are at fixed times | J, G | hard | Jyothy Tr: outside teachers come in for the activity periods, so those times cannot move. PF is a performance for grades 1-5 together in the main auditorium. R3 is common across grade 9. Seven fixed slots found in the grid, each a subject every section taking it takes at exactly the same slots. |
| Every laboratory in 11-12 is a double period | G, S | hard | 37 lab cells, 37 followed by a blank continuation. No exceptions. |
| Elective blocks run at the same time across their sections | G, J | hard | `M/IP/P` across 11E-11G and again across 12A, 12D, 12E; `AI/MM/YOGA` across all five of 11C-11G at once. |
| One specialist per subject in grades 1-5 | G | hard | Dance, music, drawing, craft, library, robotics and computing never appear in two sections in the same period. |
| Bands are built 11-12, then 9-10, then 6-8, then 1-5 | C, S | structural | 30 teacher codes appear in both 6-8 and 9-10, 11 in all three secondary bands. Each band fixed removes availability from the next. |
| Grades 1-5 have a zero period on Thursday only | G | structural | 46 slots in their week, not 45. |

## 3. Where a stated rule and the grid disagreed

These are the entries that matter most, because each one changed the model.

**D/M/D is not a class splitting.** Jyothy Tr described dance, music and drawing as the class
splitting within itself. The grid says otherwise: `DMD` appears in exactly **two sections at the
same time**, always with the same three specialists `V/A/S` — 8A+8B Monday P2, 7A+7B Monday P3,
6A+6B Monday P6, 6C+6D Tuesday P2, 8C+8D Friday P4, 7C+7D Friday P6. Two sections regroup into
three activity groups. Modelled as a regroup, on the grid's evidence. **Still to confirm with
her.** Modelling it as a split was producing a phantom teacher clash between 6A and 6B.

**Lab doubles do cross the break, and that is tolerated rather than intended.** Six of the 37 lab
doubles in 11-12 start at period 6 and run across the break (11D on Monday, Tuesday and
Wednesday; 11A and 11E on Wednesday; 12C on Friday). Jyothy Tr confirmed it is allowed: the class
goes to lunch and comes back to the laboratory, though it is not what they want. The model
therefore requires the double and asks for no crossing as a preference. Given the freedom of a
cold start the system satisfies that preference in every band, which the school's own timetable
does not: a small case of the system finding something the committee could not by hand.

**11A and 11B are not short of lessons; their day is short.** The two sections are empty in
periods 7, 8 and 9 on every day of the week, which was first read as an incomplete record. It is
neither that nor merged groups: those students leave for outside coaching after the break, and the
run of empty periods begins exactly where the break falls. Their day is six periods and they take
30 lessons in 30 slots, which is completely full. Those slots are now closed for those two
sections, by the same mechanism as the Thursday zero period in grades 1-5, because a solver with
access to them will otherwise schedule lessons for students who are not on the premises. It also
removed a contradiction: the blank after 11A's Wednesday period 6 laboratory had been read as the
second half of a double, and is in fact the section going home, so that laboratory is a single
period.

**Support codes are teachers.** We initially excluded `PRC`, `VIS`, `SMC`, `ASK`, `REM` and
`LIB` from the teacher count, on the pattern-matching guess that they were room or supervision
markers. They are people. `PRC` is Praveen. `LIB` is the library. Excluding them understated
teacher load and hid real conflicts. The teacher-wise sheet would have settled it immediately
and we should have asked for it first.

**"First named teacher is scheduled" was never true.** We asserted for a while that in a
multi-teacher cell the first name is the one actually teaching. Checking the grid found **zero**
cells where that mattered. The claim was withdrawn.

**Every named teacher busy was the costly one.** For a while the model booked every teacher
named against a section-subject pair for every lesson of that pair. That is right for a split
cell and wrong everywhere else. It pushed ANR to **47 periods in a 45-period week** and made the
whole school unsolvable. The fix, and the distinction it forced, is in `kmbvm-data-model.md`.

## 4. Open questions for Jyothy Tr

1. **D/M/D.** The grid shows two sections doing dance, music and drawing together with three
   teachers, not one class splitting three ways. Which is it?
2. **The break.** Is it after period 5 or period 6? And either way, six lab doubles appear to
   run straight through it. Is that allowed, or are those six recorded wrongly?
3. **11A, Monday period 1.** A lab in the first period, the one exception to a rule stated
   without exceptions. Real, or a slip?
4. **Four cells where a teacher appears in a subject she teaches nowhere else:** ANR in 11B
   physics, ADS in 10B English, ANP in 6C Hindi, PMN in 6D English. We read all four as cells
   written in the wrong row. Correct?
5. **12B and 6D English.** Each has one period taught by someone other than its main English
   teacher: BIN for 12B, and PMN for 6D. Is the 5+1 division deliberate?
6. **ANP** appears in 6C Hindi and 8C English in the same period, different grades, unrelated
   subjects. The one cell the model cannot explain at all.
7. ~~**11A and 11B** are only two-thirds full. Merged groups, or an incomplete record?~~
   **Answered: neither.** Those students leave for outside coaching at Pala after the break, so
   those two sections have a six-period day. See §3.
8. ~~**SMT** covers 61 slots in 11-12 alone, far more than anyone else.~~ **Answered: one
   teacher, Shyamili, and the arithmetic confirms the data model.** Her name appears in 61 cells
   and she teaches 33 periods. Jyothy Tr's explanation is the regroup rule in her own words:
   where her name appears across several classes in the same period, those classes are regrouped
   into one group that she takes. Collapsing regroups as the model does gives exactly 33.

## 5. What changed, in order

| When | Change |
|---|---|
| August | Scope set with Suma Tr. Rules assumed to come from natural language alone. |
| Early October | Her mother's school sends the real 2026-27 workbook. Four tabs, 50 sections. |
| Mid October | Grid measured. Eight implicit patterns found that nobody had stated. Eight questions drafted. |
| 27 October | Jyothy Tr answers. Labels decoded, splits and regroups distinguished, break position stated. |
| 27 October | Model booking every named teacher found to be the cause of a school-wide infeasibility. Four-way distinction introduced. |
| 27 October | Support codes reinstated as teachers. Four wrong-row cells found automatically. |
| 27 October | D/M/D reclassified as a regroup against her description, on the grid's evidence. |
| 27 October | `across_break` removed as an assumption: their own doubles cross the break. |
| 27 October | All four bands reproduce their own timetable. Cold start builds the whole school. |
| 28 October | SMT confirmed as one teacher, and the 61-to-33 collapse confirmed the regroup rule in the coordinator's own words. Seven fixed slots derived. Laboratories in period 1 and doubles across lunch reclassified as preferences. |
| 28 October | Break position confirmed after period 6. 11A and 11B identified as six-period days, not incomplete records, and their afternoon slots closed. |

## 6. Why this record is part of the result

The project's claim is that a system should notice when it is guessing and ask, rather than
guess quietly. This document is the same claim applied to the project itself. Four of the entries
in §3 are cases where we guessed, the guess was wrong, and the evidence said so. Two of them,
the wrong-row cells and the regroup detection, are now found by the system automatically rather
than by hand. The rules a school actually follows are not written down anywhere, and getting
them out is not a one-shot interview: it is this back and forth, and it has to leave a trace.
