"""Weekly availability overlap in UTC minutes.

Rules live in each profile's local timezone; we project them onto a fixed
reference week so the comparison is deterministic (DST shifts within a demo
horizon are irrelevant). Missing availability yields 0 minutes but never
disqualifies a candidate (§5.5).
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

WEEK_MINUTES = 7 * 24 * 60
# Fixed reference Monday (UTC) — determinism beats calendar accuracy here.
_REFERENCE_MONDAY = datetime(2026, 8, 17, tzinfo=ZoneInfo("UTC"))


def _to_intervals(rules: list[tuple[int, time, time, str]]) -> list[tuple[int, int]]:
    intervals: list[tuple[int, int]] = []
    for weekday, local_start, local_end, timezone_name in rules:
        try:
            zone = ZoneInfo(timezone_name)
        except KeyError:
            continue
        local_day = (_REFERENCE_MONDAY + timedelta(days=weekday)).date()
        start_utc = datetime.combine(local_day, local_start, tzinfo=zone).astimezone(
            ZoneInfo("UTC")
        )
        end_utc = datetime.combine(local_day, local_end, tzinfo=zone).astimezone(ZoneInfo("UTC"))
        start_minute = int((start_utc - _REFERENCE_MONDAY).total_seconds() // 60) % WEEK_MINUTES
        length = max(0, int((end_utc - start_utc).total_seconds() // 60))
        if length == 0:
            continue
        end_minute = start_minute + length
        if end_minute <= WEEK_MINUTES:
            intervals.append((start_minute, end_minute))
        else:  # wraps past Sunday midnight UTC
            intervals.append((start_minute, WEEK_MINUTES))
            intervals.append((0, end_minute - WEEK_MINUTES))
    return sorted(intervals)


def weekly_overlap_minutes(
    rules_a: list[tuple[int, time, time, str]],
    rules_b: list[tuple[int, time, time, str]],
) -> int:
    intervals_a = _to_intervals(rules_a)
    intervals_b = _to_intervals(rules_b)
    total = 0
    for a_start, a_end in intervals_a:
        for b_start, b_end in intervals_b:
            total += max(0, min(a_end, b_end) - max(a_start, b_start))
    return total
