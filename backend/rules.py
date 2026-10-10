"""Pure claim-rule logic. No I/O, no wall-clock: the real current time never affects a rule."""
from datetime import datetime, timedelta

MIN_REST = timedelta(hours=11)
MAX_WEEK = timedelta(hours=40)


def parse(s: str) -> datetime:
    return datetime.fromisoformat(s)


def duration(shift) -> timedelta:
    return parse(shift["end"]) - parse(shift["start"])


def overlaps(a, b) -> bool:
    return parse(a["start"]) < parse(b["end"]) and parse(b["start"]) < parse(a["end"])


def week_start(shift) -> datetime:
    """Monday 00:00 of the week in which the shift STARTS."""
    d = parse(shift["start"])
    return (d - timedelta(days=d.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _h(td: timedelta) -> str:
    return f"{td.total_seconds() / 3600:.2f}".rstrip("0").rstrip(".") + "h"


def _desc(x) -> str:
    return f"{x['id']} ({x['start'].replace('T', ' ')} to {x['end'].replace('T', ' ')})"


def _v(rule, message, conflicting=None):
    return {"rule": rule, "message": f"Rule {rule}: {message}", "conflicting_shift": conflicting}


def check_claim(claimer, shift, owner_id, claimer_shifts, rules=(1, 2, 3, 4, 5)):
    """Return a list of violations (empty = OK).

    claimer_shifts: shifts currently assigned to the claimer.
    rules: which rules to evaluate (approval re-check uses 2..5).
    """
    if 1 in rules and claimer["id"] == owner_id:
        return [_v(1, "you cannot claim your own shift")]

    out = []
    cert = shift.get("required_certification")
    if 2 in rules and cert and cert not in claimer.get("certifications", []):
        out.append(_v(2, f"this shift requires the '{cert}' certification, which {claimer['name']} does not have"))

    mine = sorted((x for x in claimer_shifts if x["id"] != shift["id"]), key=lambda x: x["start"])
    s_start, s_end = parse(shift["start"]), parse(shift["end"])

    for x in mine:
        xs, xe = parse(x["start"]), parse(x["end"])
        if xs < s_end and s_start < xe:
            if 3 in rules:
                out.append(_v(3, f"overlaps with assigned shift {_desc(x)}", x["id"]))
        elif 4 in rules:
            gap = (s_start - xe) if xe <= s_start else (xs - s_end)
            if gap < MIN_REST:
                out.append(_v(4, f"only {_h(gap)} rest between this shift and {_desc(x)}; at least 11h required", x["id"]))

    if 5 in rules:
        wk = week_start(shift)
        total = duration(shift) + sum((duration(x) for x in mine if week_start(x) == wk), timedelta())
        if total > MAX_WEEK:
            out.append(_v(5, f"total would be {_h(total)} in the week starting {wk.date()} (maximum 40h)"))

    return out
