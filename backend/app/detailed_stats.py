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
    """Compute a hash of the raw data used for detailed stats."""
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
    hash_input = "|".join([
        str(year),
        today.isoformat(),
        fingerprint,
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

    if not rows:
        # Return an empty but valid-shaped response
        days_in_period = _days_in_year_period(year, today)
        return {
            "year": year,
            "top_days": [],
            "top_weeks": [],
            "top_months": [],
            "best_day_of_week": None,
            "day_of_week_breakdown": _compute_day_of_week_breakdown([]),
            "peak_month": None,
            "longest_streak": None,
            "current_year_longest_streak": None,
            "consistency": {
                "days_tracked": 0,
                "days_in_period": days_in_period,
                "percentage": 0.0,
            },
            "steps_distribution": _compute_steps_distribution([]),
            "monthly_totals": [],
            "cumulative_data": [],
            "year_summary": {
                "year": year,
                "total_steps": 0,
                "total_miles": 0.0,
                "avg_daily_steps": 0,
                "best_single_day_steps": 0,
                "best_single_day_date": None,
                "goal_met_days": 0,
                "goal_met_percentage": 0.0,
            },
        }

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
