"""One small test per constraint type. Run: python3 -m pytest tests -q (or python3 tests/test_rules.py)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from school import School
from solve import solve

TINY = {
    "name": "tiny", "days": ["Mon", "Tue"], "periods": 4, "lunch_after": 2,
    "sections": ["A", "B"], "subjects": ["MTS", "ENG"],
    "requirements": {"A": {"MTS": 4, "ENG": 4}, "B": {"MTS": 4, "ENG": 4}},
    "assignment": {"A": {"MTS": "t1", "ENG": "t2"}, "B": {"MTS": "t3", "ENG": "t4"}},
    "unstaffed": [],
}
S = School(TINY)


def holds(rules):
    return solve(S, rules, seconds=20)


def test_base_feasible():
    assert holds([])["ok"]


def test_max_consecutive():
    r = holds([("c", {"type": "max_consecutive", "teacher": "t1", "max": 1,
                      "lunch_breaks_run": False, "hard": True})])
    assert r["ok"]
    g = r["grids"]["A"]
    for d in range(2):
        col = [g[p][d] for p in range(4)]
        runs, cur = 0, 0
        for v in col:
            cur = cur + 1 if v == "MTS" else 0
            runs = max(runs, cur)
        assert runs <= 1


def test_no_consecutive_same_subject():
    r = holds([("n", {"type": "no_consecutive_same_subject", "subject": "ALL",
                      "sections": "ALL", "hard": True})])
    assert r["ok"]
    for sec, g in r["grids"].items():
        for d in range(2):
            col = [g[p][d] for p in range(4)]
            assert all(col[i] != col[i + 1] for i in range(3))


def test_subject_not_in_periods():
    r = holds([("s", {"type": "subject_not_in_periods", "subject": "MTS",
                      "sections": "ALL", "periods": [1], "hard": True})])
    assert r["ok"]
    for sec, g in r["grids"].items():
        assert "MTS" not in g[0]


def test_max_subject_per_day():
    r = holds([("m", {"type": "max_subject_per_day", "subject": "MTS",
                      "sections": "ALL", "max": 2, "hard": True})])
    assert r["ok"]
    for sec, g in r["grids"].items():
        for d in range(2):
            assert sum(1 for p in range(4) if g[p][d] == "MTS") <= 2


def test_teacher_unavailable():
    r = holds([("u", {"type": "teacher_unavailable", "teacher": "t1",
                      "days": ["Mon"], "periods": [1, 2, 3, 4], "hard": True})])
    assert r["ok"]
    assert "MTS" not in [r["grids"]["A"][p][0] for p in range(4)]


def test_infeasible_reports_conflict():
    r = holds([("a", {"type": "subject_not_in_periods", "subject": "MTS",
                      "sections": "ALL", "periods": [1, 2], "hard": True}),
               ("b", {"type": "subject_not_in_periods", "subject": "MTS",
                      "sections": "ALL", "periods": [3, 4], "hard": True})])
    assert not r["ok"] and r["conflict"]




def test_double_period():
    r = holds([("d", {"type": "double_period", "subject": "MTS", "sections": "ALL",
                      "across_break": False, "hard": True})])
    assert r["ok"]
    for sec, g in r["grids"].items():
        for d in range(2):
            col = [g[p][d] for p in range(4)]
            idx = [i for i, v in enumerate(col) if v == "MTS"]
            assert len(idx) % 2 == 0
            for a, b in zip(idx[::2], idx[1::2]):
                assert b == a + 1 and not (a < 2 <= b)      # consecutive, not across lunch




def test_parallel_block():
    r = holds([("p", {"type": "parallel_block", "subject": "MTS",
                      "sections": ["A", "B"], "hard": True})])
    assert r["ok"]
    a, b = r["grids"]["A"], r["grids"]["B"]
    assert [[c == "MTS" for c in row] for row in a] == [[c == "MTS" for c in row] for row in b]


def test_shared_resource():
    r = holds([("s", {"type": "shared_resource", "subject": "MTS",
                      "sections": "ALL", "max_at_once": 1, "hard": True})])
    assert r["ok"]
    a, b = r["grids"]["A"], r["grids"]["B"]
    for p in range(4):
        for d in range(2):
            assert not (a[p][d] == "MTS" and b[p][d] == "MTS")


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print("PASS", name)
            except AssertionError:
                fails += 1; print("FAIL", name)
    raise SystemExit(fails)
