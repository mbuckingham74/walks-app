"""Detailed statistics computations for the Stats page.

This module exposes a single endpoint handler `get_detailed_stats` plus
helper functions to compute leaderboard-style metrics from daily steps.
"""

import hashlib
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from app.config import get_settings, Settings
from app.database import get_db, retry_on_connection_error
from app.models import DetailedStatsCache
from app.route import ROUTE_WAYPOINTS, TOTAL_ROUTE_DISTANCE

logger = logging.getLogger(__name__)

EST = ZoneInfo("America/New_York")

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

DISTRIBUTION_BUCKETS = [
    {"label": "0–5k", "min": 0, "max": 5000, "color": "#9ca3af"},
    {"label": "5–10k", "min": 5000, "max": 10000, "color": "#60a5fa"},
    {"label": "10–15k", "min": 10000, "max": 15000, "color": "#34d399"},
    {"label": "15–20k", "min": 15000, "max": 20000, "color": "#22c55e"},
    {"label": "20–25k", "min": 20000, "max": 25000, "color": "#f59e0b"},
    {"label": "25k+", "min": 25000, "max": None, "color": "#ef4444"},
]


class TopDaySchema(BaseModel):
    rank: int
    date: date
    day_of_week: str
    steps: int
    miles: float


class TopWeekSchema(BaseModel):
    rank: int
    year: int
    week: int
    start_date: date
    end_date: date
    total_steps: int
    avg_steps: int


class TopMonthSchema(BaseModel):
    rank: int
    year: int
    month: int
    month_name: str
    total_steps: int
    avg_steps: int
    days_tracked: int


class DayOfWeekSchema(BaseModel):
    day: str
    day_index: int
    total_steps: int
    count: int
    avg_steps: int


class StreakSchema(BaseModel):
    length: int
    start_date: date
    end_date: date


class DistributionBucketSchema(BaseModel):
    label: str
    count: int
    percentage: float
    color: str


class MonthlyTotalSchema(BaseModel):
    year: int
    month: int
    month_name: str
    total_steps: int
    avg_steps: int
    days_tracked: int
    goal_met_days: int


class CumulativePointSchema(BaseModel):
    date: date
    steps: int
    cumulative_steps: int
    cumulative_miles: float


class ConsistencySchema(BaseModel):
    days_tracked: int
    days_in_period: int
    percentage: float


class YearSummarySchema(BaseModel):
    year: int
    total_steps: int
    total_miles: float
    avg_daily_steps: int
    best_single_day_steps: int
    best_single_day_date: Optional[date]
    goal_met_days: int
    goal_met_percentage: float


class ActivityCalendarDaySchema(BaseModel):
    date: date
    steps: int
    goal_met: bool
    intensity: int


class ActivityCalendarSchema(BaseModel):
    days: list[ActivityCalendarDaySchema]


class YearRacePointSchema(BaseModel):
    day_of_year: int
    cumulative_steps: int


class YearRaceSchema(BaseModel):
    current_year: int
    previous_year: int
    goal_daily: int
    current: list[YearRacePointSchema]
    previous: list[YearRacePointSchema]


class MomentumPointSchema(BaseModel):
    date: date
    steps: int
    avg_7: Optional[int]
    avg_28: Optional[int]


class RecordChaseSchema(BaseModel):
    today_steps: int
    today_date: Optional[date]
    top_10_threshold: int
    steps_to_top_10: int
    in_top_10: bool


class WeeklyFinishLineSchema(BaseModel):
    week_start: date
    week_end: date
    current_steps: int
    weekly_goal: int
    days_elapsed: int
    days_remaining: int
    required_daily_avg: int


class GoalSurplusPointSchema(BaseModel):
    date: date
    surplus: int


class RollingRecordSchema(BaseModel):
    total_steps: int
    avg_steps: int
    start_date: date
    end_date: date


class RollingRecordsSchema(BaseModel):
    best_7: Optional[RollingRecordSchema]
    best_14: Optional[RollingRecordSchema]
    best_30: Optional[RollingRecordSchema]


class DayPercentileSchema(BaseModel):
    steps: int
    date: Optional[date]
    percentile: float


class MilestoneSchema(BaseModel):
    city: str
    miles_from_start: int
    reached: bool
    date_reached: Optional[date]


class MilestoneTimelineSchema(BaseModel):
    crossings_completed: int
    milestones: list[MilestoneSchema]


class PerfectPeriodsSchema(BaseModel):
    perfect_weeks: int
    best_goal_met_month: Optional[MonthlyTotalSchema]
    longest_5_of_7_run: int


class ComebackScoreSchema(BaseModel):
    attempts: int
    successes: int
    score: Optional[float]


class DetailedStatsSchema(BaseModel):
    year: int
    top_days: list[TopDaySchema]
    top_weeks: list[TopWeekSchema]
    top_months: list[TopMonthSchema]
    best_day_of_week: Optional[DayOfWeekSchema]
    day_of_week_breakdown: list[DayOfWeekSchema]
    peak_month: Optional[TopMonthSchema]
    longest_streak: Optional[StreakSchema]
    current_year_longest_streak: Optional[StreakSchema]
    consistency: ConsistencySchema
    steps_distribution: list[DistributionBucketSchema]
    monthly_totals: list[MonthlyTotalSchema]
    cumulative_data: list[CumulativePointSchema]
    year_summary: YearSummarySchema
    activity_calendar: ActivityCalendarSchema
    year_race: YearRaceSchema
    momentum: list[MomentumPointSchema]
    record_chase: RecordChaseSchema
    weekly_finish_line: WeeklyFinishLineSchema
    goal_surplus: list[GoalSurplusPointSchema]
    rolling_records: RollingRecordsSchema
    day_percentile: Optional[DayPercentileSchema]
    milestone_timeline: MilestoneTimelineSchema
    perfect_periods: PerfectPeriodsSchema
    comeback_score: ComebackScoreSchema


def _bucket_label(steps: int) -> str:
    for bucket in DISTRIBUTION_BUCKETS:
        if bucket["max"] is None or steps < bucket["max"]:
            return bucket["label"]
    return DISTRIBUTION_BUCKETS[-1]["label"]


def _bucket_color(label: str) -> str:
    for bucket in DISTRIBUTION_BUCKETS:
        if bucket["label"] == label:
            return bucket["color"]
    return "#9ca3af"


def _iso_year_week(d: date) -> tuple[int, int]:
    """Return ISO year and ISO week for a date."""
    return d.isocalendar()[:2]


def _week_start_end(iso_year: int, iso_week: int) -> tuple[date, date]:
    """Return Monday and Sunday for a given ISO year/week."""
    # January 4 is always in week 1
    jan4 = date(iso_year, 1, 4)
    monday = jan4 + timedelta(weeks=iso_week - 1, days=-jan4.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


async def _fetch_daily_steps_for_year(
    db: AsyncSession, year: int, today: date
) -> list[dict]:
    """Fetch all daily steps for the requested year up to today."""
    result = await db.execute(
        text("""
            SELECT step_date, steps
            FROM daily_steps
            WHERE YEAR(step_date) = :year
              AND step_date <= :today
            ORDER BY step_date ASC
        """),
        {"year": year, "today": today},
    )
    rows = result.all()
    return [{"date": row[0], "steps": int(row[1])} for row in rows]


async def _fetch_all_daily_steps(db: AsyncSession) -> list[dict]:
    """Fetch every recorded daily step, ordered by date (for milestone timeline)."""
    result = await db.execute(
        text("""
            SELECT step_date, steps
            FROM daily_steps
            ORDER BY step_date ASC
        """)
    )
    rows = result.all()
    return [{"date": row[0], "steps": int(row[1])} for row in rows]


async def _fetch_year_fingerprint(db: AsyncSession, year: int) -> str:
    """Compact fingerprint for a year's data (sum/count/max)."""
    result = await db.execute(
        text("""
            SELECT COALESCE(SUM(steps), 0), COUNT(*), COALESCE(MAX(steps), 0)
            FROM daily_steps
            WHERE YEAR(step_date) = :year
        """),
        {"year": year},
    )
    row = result.first()
    return f"{int(row[0])}|{int(row[1])}|{int(row[2])}"


async def _fetch_all_time_fingerprint(db: AsyncSession) -> str:
    """Compact fingerprint for all-time data (sum/count/max)."""
    result = await db.execute(
        text("""
            SELECT COALESCE(SUM(steps), 0), COUNT(*), COALESCE(MAX(steps), 0)
            FROM daily_steps
        """)
    )
    row = result.first()
    return f"{int(row[0])}|{int(row[1])}|{int(row[2])}"


async def _fetch_top_days(
    db: AsyncSession, year: int, today: date, limit: int = 10
) -> list[dict]:
    result = await db.execute(
        text("""
            SELECT step_date, steps
            FROM daily_steps
            WHERE YEAR(step_date) = :year
              AND step_date <= :today
            ORDER BY steps DESC, step_date ASC
            LIMIT :limit
        """),
        {"year": year, "today": today, "limit": limit},
    )
    return [{"date": row[0], "steps": int(row[1])} for row in result.all()]


async def _fetch_top_weeks(
    db: AsyncSession, year: int, today: date, limit: int = 5
) -> list[dict]:
    result = await db.execute(
        text("""
            SELECT
                iso_year,
                iso_week,
                SUM(steps) as total_steps,
                COUNT(*) as days_tracked
            FROM (
                SELECT
                    steps,
                    YEARWEEK(step_date, 3) DIV 100 as iso_year,
                    YEARWEEK(step_date, 3) % 100 as iso_week
                FROM daily_steps
                WHERE YEAR(step_date) = :year
                  AND step_date <= :today
            ) as weeks
            GROUP BY iso_year, iso_week
            ORDER BY total_steps DESC, iso_year ASC, iso_week ASC
            LIMIT :limit
        """),
        {"year": year, "today": today, "limit": limit},
    )
    return [
        {
            "iso_year": int(row[0]),
            "iso_week": int(row[1]),
            "total_steps": int(row[2]),
            "days_tracked": int(row[3]),
        }
        for row in result.all()
    ]


async def _fetch_top_months(
    db: AsyncSession, year: int, today: date, limit: int = 5
) -> list[dict]:
    result = await db.execute(
        text("""
            SELECT
                YEAR(step_date) as year,
                MONTH(step_date) as month,
                SUM(steps) as total_steps,
                COUNT(*) as days_tracked
            FROM daily_steps
            WHERE YEAR(step_date) = :year
              AND step_date <= :today
            GROUP BY YEAR(step_date), MONTH(step_date)
            ORDER BY total_steps DESC, year ASC, month ASC
            LIMIT :limit
        """),
        {"year": year, "today": today, "limit": limit},
    )
    return [
        {
            "year": int(row[0]),
            "month": int(row[1]),
            "total_steps": int(row[2]),
            "days_tracked": int(row[3]),
        }
        for row in result.all()
    ]


async def _fetch_year_aggregates(
    db: AsyncSession, year: int, today: date, settings: Settings
) -> dict:
    result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(steps), 0),
                COUNT(*),
                COALESCE(AVG(steps), 0),
                COALESCE(MAX(steps), 0),
                (
                    SELECT step_date
                    FROM daily_steps
                    WHERE YEAR(step_date) = :year
                      AND step_date <= :today
                    ORDER BY steps DESC, step_date ASC
                    LIMIT 1
                ) as best_day_date,
                COALESCE(SUM(CASE WHEN steps >= :daily_goal THEN 1 ELSE 0 END), 0)
            FROM daily_steps
            WHERE YEAR(step_date) = :year
              AND step_date <= :today
        """),
        {"year": year, "today": today, "daily_goal": settings.daily_goal},
    )
    row = result.first()
    return {
        "total_steps": int(row[0]),
        "days_tracked": int(row[1]),
        "avg_steps": int(row[2]),
        "max_steps": int(row[3]),
        "best_day_date": row[4],
        "goal_met_days": int(row[5]),
    }


async def _fetch_data_hash(
    db: AsyncSession, year: int, today: date, settings: Settings
) -> str:
    """Compute a hash of the raw data used for detailed stats.

    Includes the current year's per-day fingerprint plus compact fingerprints
    for the previous year and all-time data, since the response now embeds
    cross-year metrics (year race, milestone timeline).
    """
    result = await db.execute(
        text("""
            SELECT GROUP_CONCAT(CONCAT(step_date, ':', steps) ORDER BY step_date SEPARATOR '|')
            FROM daily_steps
            WHERE YEAR(step_date) = :year
              AND step_date <= :today
        """),
        {"year": year, "today": today},
    )
    fingerprint = result.scalar() or ""
    previous_fingerprint = await _fetch_year_fingerprint(db, year - 1)
    all_time_fingerprint = await _fetch_all_time_fingerprint(db)
    hash_input = "|".join([
        str(year),
        today.isoformat(),
        fingerprint,
        previous_fingerprint,
        all_time_fingerprint,
        str(settings.steps_per_mile),
        str(settings.daily_goal),
    ])
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


def _compute_day_of_week_breakdown(rows: list[dict]) -> list[DayOfWeekSchema]:
    totals = defaultdict(lambda: {"total_steps": 0, "count": 0})
    for row in rows:
        idx = row["date"].weekday()
        totals[idx]["total_steps"] += row["steps"]
        totals[idx]["count"] += 1

    breakdown = []
    for idx, name in enumerate(DAY_NAMES):
        info = totals.get(idx, {"total_steps": 0, "count": 0})
        count = info["count"]
        breakdown.append(DayOfWeekSchema(
            day=name,
            day_index=idx,
            total_steps=info["total_steps"],
            count=count,
            avg_steps=round(info["total_steps"] / count) if count > 0 else 0,
        ))
    return breakdown


def _compute_best_day_of_week(
    breakdown: list[DayOfWeekSchema],
) -> Optional[DayOfWeekSchema]:
    eligible = [d for d in breakdown if d.count > 0]
    if not eligible:
        return None
    return max(eligible, key=lambda d: d.avg_steps)


def _compute_longest_streak(rows: list[dict], daily_goal: int) -> Optional[StreakSchema]:
    goal_met_rows = [r for r in rows if r["steps"] >= daily_goal]
    if not goal_met_rows:
        return None

    longest = {"length": 0, "start": None, "end": None}
    current = {"length": 0, "start": None, "end": None}

    for row in goal_met_rows:
        d = row["date"]
        if current["end"] is not None and (d - current["end"]).days == 1:
            current["length"] += 1
            current["end"] = d
        else:
            current = {"length": 1, "start": d, "end": d}

        if current["length"] > longest["length"]:
            longest = current.copy()

    if longest["length"] == 0:
        return None

    return StreakSchema(
        length=longest["length"],
        start_date=longest["start"],
        end_date=longest["end"],
    )


def _compute_steps_distribution(rows: list[dict]) -> list[DistributionBucketSchema]:
    counts = defaultdict(int)
    for row in rows:
        counts[_bucket_label(row["steps"])] += 1

    total = len(rows)
    distribution = []
    for bucket in DISTRIBUTION_BUCKETS:
        count = counts.get(bucket["label"], 0)
        distribution.append(DistributionBucketSchema(
            label=bucket["label"],
            count=count,
            percentage=round((count / total) * 100, 1) if total > 0 else 0,
            color=bucket["color"],
        ))
    return distribution


def _compute_monthly_totals(
    rows: list[dict], year: int, daily_goal: int
) -> list[MonthlyTotalSchema]:
    monthly = defaultdict(lambda: {"total_steps": 0, "count": 0, "goal_met": 0})
    for row in rows:
        key = (row["date"].year, row["date"].month)
        monthly[key]["total_steps"] += row["steps"]
        monthly[key]["count"] += 1
        if row["steps"] >= daily_goal:
            monthly[key]["goal_met"] += 1

    totals = []
    for (y, m), info in sorted(monthly.items()):
        count = info["count"]
        totals.append(MonthlyTotalSchema(
            year=y,
            month=m,
            month_name=MONTH_NAMES[m - 1],
            total_steps=info["total_steps"],
            avg_steps=round(info["total_steps"] / count) if count > 0 else 0,
            days_tracked=count,
            goal_met_days=info["goal_met"],
        ))
    return totals


def _compute_cumulative_data(
    rows: list[dict], steps_per_mile: int
) -> list[CumulativePointSchema]:
    cumulative = []
    total = 0
    for row in rows:
        total += row["steps"]
        cumulative.append(CumulativePointSchema(
            date=row["date"],
            steps=row["steps"],
            cumulative_steps=total,
            cumulative_miles=round(total / steps_per_mile, 2),
        ))
    return cumulative


def _calendar_day_range(year: int, today: date) -> list[date]:
    start = date(year, 1, 1)
    end = min(today, date(year, 12, 31))
    if end < start:
        return []
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _compute_activity_calendar(
    rows: list[dict], year: int, today: date, daily_goal: int
) -> ActivityCalendarSchema:
    steps_map = {r["date"]: r["steps"] for r in rows}
    days = []
    for d in _calendar_day_range(year, today):
        steps = steps_map.get(d, 0)
        goal_met = steps >= daily_goal
        if d not in steps_map:
            intensity = 0
        else:
            pct = steps / daily_goal if daily_goal > 0 else 0
            if pct < 0.5:
                intensity = 1
            elif pct < 1.0:
                intensity = 2
            elif pct < 1.5:
                intensity = 3
            else:
                intensity = 4
        days.append(ActivityCalendarDaySchema(
            date=d, steps=steps, goal_met=goal_met, intensity=intensity,
        ))
    return ActivityCalendarSchema(days=days)


def _cumulative_by_day_of_year(rows: list[dict]) -> list[YearRacePointSchema]:
    series = []
    total = 0
    for r in rows:
        total += r["steps"]
        series.append(YearRacePointSchema(
            day_of_year=r["date"].timetuple().tm_yday,
            cumulative_steps=total,
        ))
    return series


def _compute_year_race(
    current_rows: list[dict],
    previous_rows: list[dict],
    year: int,
    daily_goal: int,
) -> YearRaceSchema:
    return YearRaceSchema(
        current_year=year,
        previous_year=year - 1,
        goal_daily=daily_goal,
        current=_cumulative_by_day_of_year(current_rows),
        previous=_cumulative_by_day_of_year(previous_rows),
    )


def _compute_momentum(
    rows: list[dict], year: int, today: date
) -> list[MomentumPointSchema]:
    steps_map = {r["date"]: r["steps"] for r in rows}
    result = []
    for d in _calendar_day_range(year, today):
        steps = steps_map.get(d, 0)
        avg_7 = round(sum(
            steps_map.get(d - timedelta(days=i), 0) for i in range(7)
        ) / 7) if d >= date(year, 1, 1) + timedelta(days=6) else None
        avg_28 = round(sum(
            steps_map.get(d - timedelta(days=i), 0) for i in range(28)
        ) / 28) if d >= date(year, 1, 1) + timedelta(days=27) else None
        result.append(MomentumPointSchema(
            date=d, steps=steps, avg_7=avg_7, avg_28=avg_28,
        ))
    return result


def _compute_record_chase(
    rows: list[dict], today: date
) -> RecordChaseSchema:
    today_row = next((r for r in rows if r["date"] == today), None)
    today_steps = today_row["steps"] if today_row else 0
    today_date = today_row["date"] if today_row else None

    sorted_steps = sorted((r["steps"] for r in rows), reverse=True)
    if len(sorted_steps) >= 10:
        threshold = sorted_steps[9]
    elif sorted_steps:
        threshold = sorted_steps[-1]
    else:
        threshold = 0

    in_top_10 = bool(sorted_steps and len(sorted_steps) >= 10 and today_steps >= threshold)
    if len(sorted_steps) < 10 and today_steps > 0:
        in_top_10 = True
    steps_to_top_10 = max(0, threshold - today_steps) if threshold > 0 else 0
    return RecordChaseSchema(
        today_steps=today_steps,
        today_date=today_date,
        top_10_threshold=threshold,
        steps_to_top_10=steps_to_top_10,
        in_top_10=in_top_10,
    )


def _compute_weekly_finish_line(
    rows: list[dict], today: date, daily_goal: int
) -> WeeklyFinishLineSchema:
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    weekly_goal = daily_goal * 7
    current_steps = sum(
        r["steps"] for r in rows
        if week_start <= r["date"] <= min(week_end, today)
    )
    days_elapsed = (today - week_start).days + 1
    days_remaining = max(0, 7 - days_elapsed)
    deficit = max(0, weekly_goal - current_steps)
    required_daily_avg = (
        -(-deficit // days_remaining) if days_remaining > 0 else deficit
    )
    return WeeklyFinishLineSchema(
        week_start=week_start,
        week_end=week_end,
        current_steps=current_steps,
        weekly_goal=weekly_goal,
        days_elapsed=days_elapsed,
        days_remaining=days_remaining,
        required_daily_avg=required_daily_avg,
    )


def _compute_goal_surplus(
    rows: list[dict], daily_goal: int
) -> list[GoalSurplusPointSchema]:
    return [
        GoalSurplusPointSchema(date=r["date"], surplus=r["steps"] - daily_goal)
        for r in rows
    ]


def _compute_rolling_records(
    rows: list[dict], year: int, today: date
) -> RollingRecordsSchema:
    steps_map = {r["date"]: r["steps"] for r in rows}
    calendar_days = _calendar_day_range(year, today)
    steps_list = [steps_map.get(d, 0) for d in calendar_days]

    def best_window(n: int) -> Optional[RollingRecordSchema]:
        if len(steps_list) < n:
            return None
        window_sum = sum(steps_list[:n])
        best_sum = window_sum
        best_start = 0
        for i in range(1, len(steps_list) - n + 1):
            window_sum += steps_list[i + n - 1] - steps_list[i - 1]
            if window_sum > best_sum:
                best_sum = window_sum
                best_start = i
        return RollingRecordSchema(
            total_steps=best_sum,
            avg_steps=round(best_sum / n),
            start_date=calendar_days[best_start],
            end_date=calendar_days[best_start + n - 1],
        )

    return RollingRecordsSchema(
        best_7=best_window(7),
        best_14=best_window(14),
        best_30=best_window(30),
    )


def _compute_day_percentile(
    rows: list[dict], today: date
) -> Optional[DayPercentileSchema]:
    if not rows:
        return None
    today_row = next((r for r in rows if r["date"] == today), None)
    if today_row:
        target = today_row["steps"]
        target_date = today_row["date"]
    else:
        target = rows[-1]["steps"]
        target_date = rows[-1]["date"]
    all_steps = sorted(r["steps"] for r in rows)
    below = sum(1 for s in all_steps if s < target)
    percentile = round((below / len(all_steps)) * 100, 1)
    return DayPercentileSchema(
        steps=target, date=target_date, percentile=percentile,
    )


def _compute_milestone_timeline(
    all_rows: list[dict], steps_per_mile: int
) -> MilestoneTimelineSchema:
    total_steps = sum(r["steps"] for r in all_rows)
    total_miles = total_steps / steps_per_mile
    crossings = int(total_miles // TOTAL_ROUTE_DISTANCE)

    milestones = []
    for wp in ROUTE_WAYPOINTS:
        threshold = crossings * TOTAL_ROUTE_DISTANCE + wp.miles_from_start
        reached = total_miles >= threshold
        date_reached = None
        if reached:
            cumulative_miles = 0.0
            for r in all_rows:
                cumulative_miles += r["steps"] / steps_per_mile
                if cumulative_miles >= threshold:
                    date_reached = r["date"]
                    break
        milestones.append(MilestoneSchema(
            city=wp.city,
            miles_from_start=wp.miles_from_start,
            reached=reached,
            date_reached=date_reached,
        ))
    return MilestoneTimelineSchema(
        crossings_completed=crossings, milestones=milestones,
    )


def _compute_perfect_periods(
    rows: list[dict],
    year: int,
    today: date,
    daily_goal: int,
    monthly_totals: list[MonthlyTotalSchema],
) -> PerfectPeriodsSchema:
    steps_map = {r["date"]: r["steps"] for r in rows}
    weeks: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for r in rows:
        iso_year, iso_week, _ = r["date"].isocalendar()
        weeks[(iso_year, iso_week)].append(r)

    perfect_weeks = 0
    week_5_of_7_flags: list[bool] = []
    for (iy, iw) in sorted(weeks.keys()):
        monday, sunday = _week_start_end(iy, iw)
        if sunday >= today:
            continue
        met_days = sum(
            1 for i in range(7)
            if steps_map.get(monday + timedelta(days=i), 0) >= daily_goal
        )
        if met_days == 7:
            perfect_weeks += 1
        week_5_of_7_flags.append(met_days >= 5)

    longest_5_of_7_run = 0
    current_run = 0
    for flag in week_5_of_7_flags:
        if flag:
            current_run += 1
            longest_5_of_7_run = max(longest_5_of_7_run, current_run)
        else:
            current_run = 0

    best_goal_met_month = max(
        (m for m in monthly_totals if m.days_tracked > 0),
        key=lambda m: (m.goal_met_days, m.goal_met_days / m.days_tracked),
        default=None,
    )

    return PerfectPeriodsSchema(
        perfect_weeks=perfect_weeks,
        best_goal_met_month=best_goal_met_month,
        longest_5_of_7_run=longest_5_of_7_run,
    )


def _compute_comeback_score(
    rows: list[dict], daily_goal: int
) -> ComebackScoreSchema:
    sorted_rows = sorted(rows, key=lambda r: r["date"])
    attempts = 0
    successes = 0
    for i in range(1, len(sorted_rows)):
        prev = sorted_rows[i - 1]
        curr = sorted_rows[i]
        if (curr["date"] - prev["date"]).days == 1 and prev["steps"] < daily_goal:
            attempts += 1
            if curr["steps"] >= daily_goal:
                successes += 1
    score = round((successes / attempts) * 100, 1) if attempts > 0 else None
    return ComebackScoreSchema(attempts=attempts, successes=successes, score=score)


def _days_in_year_period(year: int, today: date) -> int:
    """Number of days from Jan 1 of the year through today (inclusive)."""
    start = date(year, 1, 1)
    end = min(today, date(year, 12, 31))
    if end < start:
        return 0
    return (end - start).days + 1


async def _compute_detailed_stats(
    db: AsyncSession,
    year: int,
    today: date,
    settings: Settings,
) -> dict:
    """Compute the full detailed-stats payload."""
    rows = await _fetch_daily_steps_for_year(db, year, today)
    previous_rows = await _fetch_daily_steps_for_year(db, year - 1, today)
    all_rows = await _fetch_all_daily_steps(db)

    year_race = _compute_year_race(rows, previous_rows, year, settings.daily_goal)
    milestone_timeline = _compute_milestone_timeline(all_rows, settings.steps_per_mile)

    if not rows:
        days_in_period = _days_in_year_period(year, today)
        return DetailedStatsSchema(
            year=year,
            top_days=[],
            top_weeks=[],
            top_months=[],
            best_day_of_week=None,
            day_of_week_breakdown=_compute_day_of_week_breakdown([]),
            peak_month=None,
            longest_streak=None,
            current_year_longest_streak=None,
            consistency=ConsistencySchema(
                days_tracked=0,
                days_in_period=days_in_period,
                percentage=0.0,
            ),
            steps_distribution=_compute_steps_distribution([]),
            monthly_totals=[],
            cumulative_data=[],
            year_summary=YearSummarySchema(
                year=year,
                total_steps=0,
                total_miles=0.0,
                avg_daily_steps=0,
                best_single_day_steps=0,
                best_single_day_date=None,
                goal_met_days=0,
                goal_met_percentage=0.0,
            ),
            activity_calendar=_compute_activity_calendar([], year, today, settings.daily_goal),
            year_race=year_race,
            momentum=_compute_momentum([], year, today),
            record_chase=_compute_record_chase([], today),
            weekly_finish_line=_compute_weekly_finish_line([], today, settings.daily_goal),
            goal_surplus=[],
            rolling_records=RollingRecordsSchema(best_7=None, best_14=None, best_30=None),
            day_percentile=None,
            milestone_timeline=milestone_timeline,
            perfect_periods=_compute_perfect_periods([], year, today, settings.daily_goal, []),
            comeback_score=_compute_comeback_score([], settings.daily_goal),
        ).model_dump(mode="json")

    aggregates = await _fetch_year_aggregates(db, year, today, settings)

    top_days_rows = await _fetch_top_days(db, year, today, limit=10)
    top_weeks_rows = await _fetch_top_weeks(db, year, today, limit=5)
    top_months_rows = await _fetch_top_months(db, year, today, limit=5)

    top_days = []
    for rank, row in enumerate(top_days_rows, start=1):
        top_days.append(TopDaySchema(
            rank=rank,
            date=row["date"],
            day_of_week=DAY_NAMES[row["date"].weekday()],
            steps=row["steps"],
            miles=round(row["steps"] / settings.steps_per_mile, 2),
        ))

    top_weeks = []
    for rank, row in enumerate(top_weeks_rows, start=1):
        start_date, end_date = _week_start_end(row["iso_year"], row["iso_week"])
        top_weeks.append(TopWeekSchema(
            rank=rank,
            year=row["iso_year"],
            week=row["iso_week"],
            start_date=start_date,
            end_date=end_date,
            total_steps=row["total_steps"],
            avg_steps=round(row["total_steps"] / row["days_tracked"]),
        ))

    top_months = []
    for rank, row in enumerate(top_months_rows, start=1):
        top_months.append(TopMonthSchema(
            rank=rank,
            year=row["year"],
            month=row["month"],
            month_name=MONTH_NAMES[row["month"] - 1],
            total_steps=row["total_steps"],
            avg_steps=round(row["total_steps"] / row["days_tracked"]),
            days_tracked=row["days_tracked"],
        ))

    day_of_week_breakdown = _compute_day_of_week_breakdown(rows)
    best_day_of_week = _compute_best_day_of_week(day_of_week_breakdown)
    peak_month = max(top_months, key=lambda m: m.total_steps) if top_months else None

    longest_streak = _compute_longest_streak(rows, settings.daily_goal)
    current_year_longest_streak = longest_streak  # Same data set; named for clarity

    days_in_period = _days_in_year_period(year, today)
    consistency = ConsistencySchema(
        days_tracked=aggregates["days_tracked"],
        days_in_period=days_in_period,
        percentage=round(
            (aggregates["days_tracked"] / days_in_period) * 100, 1
        ) if days_in_period > 0 else 0.0,
    )

    steps_distribution = _compute_steps_distribution(rows)
    monthly_totals = _compute_monthly_totals(rows, year, settings.daily_goal)
    cumulative_data = _compute_cumulative_data(rows, settings.steps_per_mile)

    activity_calendar = _compute_activity_calendar(rows, year, today, settings.daily_goal)
    momentum = _compute_momentum(rows, year, today)
    record_chase = _compute_record_chase(rows, today)
    weekly_finish_line = _compute_weekly_finish_line(rows, today, settings.daily_goal)
    goal_surplus = _compute_goal_surplus(rows, settings.daily_goal)
    rolling_records = _compute_rolling_records(rows, year, today)
    day_percentile = _compute_day_percentile(rows, today)
    perfect_periods = _compute_perfect_periods(
        rows, year, today, settings.daily_goal, monthly_totals
    )
    comeback_score = _compute_comeback_score(rows, settings.daily_goal)

    year_summary = YearSummarySchema(
        year=year,
        total_steps=aggregates["total_steps"],
        total_miles=round(aggregates["total_steps"] / settings.steps_per_mile, 2),
        avg_daily_steps=aggregates["avg_steps"],
        best_single_day_steps=aggregates["max_steps"],
        best_single_day_date=aggregates["best_day_date"],
        goal_met_days=aggregates["goal_met_days"],
        goal_met_percentage=round(
            (aggregates["goal_met_days"] / aggregates["days_tracked"]) * 100, 1
        ) if aggregates["days_tracked"] > 0 else 0.0,
    )

    return DetailedStatsSchema(
        year=year,
        top_days=top_days,
        top_weeks=top_weeks,
        top_months=top_months,
        best_day_of_week=best_day_of_week,
        day_of_week_breakdown=day_of_week_breakdown,
        peak_month=peak_month,
        longest_streak=longest_streak,
        current_year_longest_streak=current_year_longest_streak,
        consistency=consistency,
        steps_distribution=steps_distribution,
        monthly_totals=monthly_totals,
        cumulative_data=cumulative_data,
        year_summary=year_summary,
        activity_calendar=activity_calendar,
        year_race=year_race,
        momentum=momentum,
        record_chase=record_chase,
        weekly_finish_line=weekly_finish_line,
        goal_surplus=goal_surplus,
        rolling_records=rolling_records,
        day_percentile=day_percentile,
        milestone_timeline=milestone_timeline,
        perfect_periods=perfect_periods,
        comeback_score=comeback_score,
    ).model_dump(mode="json")


async def _get_cached_detailed_stats(
    db: AsyncSession, year: int, data_hash: str
) -> Optional[dict]:
    result = await db.execute(
        text("""
            SELECT stats_json
            FROM detailed_stats_cache
            WHERE year = :year AND data_hash = :data_hash
        """),
        {"year": year, "data_hash": data_hash},
    )
    row = result.scalar_one_or_none()
    if row:
        return json.loads(row)
    return None


async def _set_cached_detailed_stats(
    db: AsyncSession, year: int, data_hash: str, payload: dict
) -> None:
    stats_json = json.dumps(payload)
    stmt = insert(DetailedStatsCache).values(
        year=year,
        stats_json=stats_json,
        data_hash=data_hash,
    )
    stmt = stmt.on_duplicate_key_update(
        stats_json=stats_json,
        data_hash=data_hash,
    )
    await db.execute(stmt)
    await db.commit()


async def get_detailed_stats(
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get detailed leaderboard statistics for the Stats page.

    Defaults to the current year. Results are cached and invalidated when
    the underlying daily_steps data changes.
    """
    settings = get_settings()
    today = datetime.now(EST).date()

    if year is None:
        year = today.year

    if year < 1900 or year > 2100:
        raise HTTPException(status_code=400, detail="Invalid year")

    try:
        data_hash = await _fetch_data_hash(db, year, today, settings)
        cached = await _get_cached_detailed_stats(db, year, data_hash)
        if cached:
            logger.debug(f"Detailed stats cache hit for year {year}")
            return cached

        logger.info(f"Detailed stats cache miss for year {year}, recomputing...")
        payload = await _compute_detailed_stats(db, year, today, settings)
        await _set_cached_detailed_stats(db, year, data_hash, payload)
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to compute detailed stats for year {year}")
        raise HTTPException(
            status_code=500,
            detail="Unable to compute detailed statistics. Please try again later.",
        ) from exc
