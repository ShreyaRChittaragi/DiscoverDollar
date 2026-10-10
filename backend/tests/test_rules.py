import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rules import check_claim


def sh(id_, start, end, cert=None, who="x"):
    return {"id": id_, "start": start, "end": end, "required_certification": cert, "assigned_to": who}


C = {"id": "c", "name": "C", "role": "STAFF", "certifications": []}


def rules_of(vs):
    return sorted(v["rule"] for v in vs)


def test_own_shift_only_rule1():
    s = sh("s", "2026-03-02T08:00", "2026-03-02T16:00", "NURSE", "c")
    assert rules_of(check_claim(C, s, "c", [])) == [1]


def test_cert():
    s = sh("s", "2026-03-02T08:00", "2026-03-02T16:00", "NURSE")
    assert rules_of(check_claim(C, s, "p", [])) == [2]


def test_overlap_and_touching():
    s = sh("s", "2026-03-02T08:00", "2026-03-02T16:00")
    ov = sh("a", "2026-03-02T15:00", "2026-03-02T20:00", who="c")
    assert 3 in rules_of(check_claim(C, s, "p", [ov]))
    touching = sh("b", "2026-03-02T16:00", "2026-03-02T20:00", who="c")  # not overlap, but 0h rest
    assert rules_of(check_claim(C, s, "p", [touching])) == [4]


def test_rest_exactly_11h_ok():
    s = sh("s", "2026-03-03T07:00", "2026-03-03T15:00")
    prev = sh("a", "2026-03-02T12:00", "2026-03-02T20:00", who="c")
    assert check_claim(C, s, "p", [prev]) == []


def test_week_limit_inclusive_and_boundary():
    mine = [sh(f"m{i}", f"2026-03-0{2+i}T09:00", f"2026-03-0{2+i}T17:00", who="c") for i in range(4)]  # 32h
    ok = sh("s", "2026-03-06T09:00", "2026-03-06T17:00")  # 40h exactly
    assert check_claim(C, ok, "p", mine) == []
    over = sh("s", "2026-03-06T09:00", "2026-03-06T17:30")
    assert rules_of(check_claim(C, over, "p", mine)) == [5]
    sunday_night = sh("s", "2026-03-08T23:00", "2026-03-09T07:00")  # belongs to week of Mar 2
    assert 5 in rules_of(check_claim(C, sunday_night, "p", mine + [sh("z", "2026-03-06T09:00", "2026-03-06T17:00", who="c")]))
