import hashlib
import json
import logging
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy import select, func, extract, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from app.config import get_settings, Settings
from app.database import get_db, init_db
from app.models import Activity, DailySteps, RouteProgress, StatsCache
from app.schemas import (
    ActivitySchema, DailyStepsSchema,
    RouteSchema, WaypointSchema, StatsSchema, PositionSchema,
    StepsInput, StepsResponse
)
from app.route import get_route_waypoints, calculate_position, TOTAL_ROUTE_DISTANCE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Security scheme for OpenAPI docs (shows "Authorize" button)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    x_api_key: Optional[str] = Depends(api_key_header),
    settings: Settings = Depends(get_settings),
):
    """Dependency to verify API key for mutating endpoints."""
    configured_key = settings.api_key.get_secret_value().strip()
    if not configured_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server"
        )
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header"
        )
    if not secrets.compare_digest(x_api_key.strip(), configured_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Walks Tracker API",
    description="Track walking progress across I-90 from Seattle to Boston",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# --- Data Retrieval ---

EST = ZoneInfo("America/New_York")


async def _compute_data_hash(db: AsyncSession, year: int, today: date) -> str:
    """Compute a hash of the underlying data to detect changes.

    Includes factors that affect stats:
    - Year-specific: max date, sum, count, individual daily values (for streaks)
    - Cross-year: recent data for week comparisons, all-time totals for position
    - Time-relative: today's date (streak/week calculations are date-relative)
    """
    # Year-specific aggregates
    year_result = await db.execute(
        select(
            func.max(DailySteps.step_date),
            func.sum(DailySteps.steps),
            func.count(DailySteps.id)
        ).where(extract("year", DailySteps.step_date) == year)
    )
    year_row = year_result.first()

    # Get checksum of recent daily values (affects streaks - last 30 days)
    # Using GROUP_CONCAT to create a fingerprint of per-day data
    streak_window_start = today - timedelta(days=30)
    daily_result = await db.execute(
        text("""
            SELECT GROUP_CONCAT(CONCAT(step_date, ':', steps) ORDER BY step_date SEPARATOR ',')
            FROM daily_steps
            WHERE step_date >= :start_date
        """),
        {"start_date": streak_window_start}
    )
    daily_fingerprint = daily_result.scalar() or ""

    # All-time totals (for position calculation across years)
    all_time_result = await db.execute(
        select(func.sum(DailySteps.steps), func.count(DailySteps.id))
    )
    all_time_row = all_time_result.first()

    # Week comparison needs data from past 2 weeks (cross-year)
    week_start = today - timedelta(days=today.weekday())
    two_weeks_ago = week_start - timedelta(days=7)
    week_result = await db.execute(
        select(func.sum(DailySteps.steps)).where(
            DailySteps.step_date >= two_weeks_ago
        )
    )
    recent_weeks_sum = week_result.scalar() or 0

    hash_input = "|".join([
        str(year_row[0]),  # max date for year
        str(year_row[1]),  # sum for year
        str(year_row[2]),  # count for year
        daily_fingerprint,  # per-day values for streak calculation
        str(all_time_row[0]),  # all-time sum
        str(all_time_row[1]),  # all-time count
        str(recent_weeks_sum),  # recent weeks data
        today.isoformat(),  # today's date
    ])
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


async def _calculate_streak_sql(db: AsyncSession, year: int, today: date, daily_goal: int) -> int:
    """Calculate current streak using MySQL window functions.

    Uses LAG to detect gaps in consecutive goal-met days, then finds
    the streak that includes today or yesterday.
    """
    yesterday = today - timedelta(days=1)

    # This query:
    # 1. Filters to days where goal was met
    # 2. Uses LAG to get previous goal-met date
    # 3. Calculates if there's a gap (more than 1 day between consecutive goal-met days)
    # 4. Creates streak groups using a running sum of gap flags
    # 5. Finds the streak containing today or yesterday and counts its days
    streak_sql = text("""
        WITH goal_met_days AS (
            SELECT
                step_date,
                LAG(step_date) OVER (ORDER BY step_date) as prev_date
            FROM daily_steps
            WHERE YEAR(step_date) = :year
              AND steps >= :daily_goal
        ),
        with_gaps AS (
            SELECT
                step_date,
                CASE
                    WHEN prev_date IS NULL THEN 1
                    WHEN DATEDIFF(step_date, prev_date) > 1 THEN 1
                    ELSE 0
                END as is_new_streak
            FROM goal_met_days
        ),
        with_groups AS (
            SELECT
                step_date,
                SUM(is_new_streak) OVER (ORDER BY step_date) as streak_group
            FROM with_gaps
        ),
        current_streak AS (
            SELECT streak_group, COUNT(*) as streak_length, MAX(step_date) as max_date
            FROM with_groups
            GROUP BY streak_group
            HAVING MAX(step_date) >= :yesterday
        )
        SELECT COALESCE(MAX(streak_length), 0) as current_streak
        FROM current_streak
        WHERE max_date >= :yesterday
    """)

    result = await db.execute(
        streak_sql,
        {"year": year, "daily_goal": daily_goal, "yesterday": yesterday}
    )
    return result.scalar() or 0


async def _get_all_time_steps(db: AsyncSession) -> int:
    """Get total steps across all years."""
    result = await db.execute(
        select(func.coalesce(func.sum(DailySteps.steps), 0))
    )
    return int(result.scalar())


async def _compute_stats(db: AsyncSession, year: int, settings: Settings) -> dict:
    """Compute all statistics in optimized queries."""
    today = datetime.now(EST).date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    last_week_start = week_start - timedelta(days=7)

    # Single query for year-specific aggregates
    combined_sql = text("""
        SELECT
            COALESCE(SUM(steps), 0) as total_steps,
            COUNT(*) as total_days,
            COALESCE(AVG(steps), 0) as avg_steps,
            COALESCE(MAX(steps), 0) as max_steps,
            (SELECT step_date FROM daily_steps
             WHERE YEAR(step_date) = :year
             ORDER BY steps DESC, step_date ASC LIMIT 1) as best_day_date,
            SUM(CASE WHEN steps >= :daily_goal THEN 1 ELSE 0 END) as days_goal_met
        FROM daily_steps
        WHERE YEAR(step_date) = :year
    """)

    # Separate query for week comparison (spans across years)
    week_sql = text("""
        SELECT
            COALESCE(SUM(CASE WHEN step_date >= :week_start AND step_date <= :today
                         THEN steps ELSE 0 END), 0) as this_week_steps,
            COALESCE(SUM(CASE WHEN step_date >= :last_week_start AND step_date < :week_start
                         THEN steps ELSE 0 END), 0) as last_week_steps
        FROM daily_steps
        WHERE step_date >= :last_week_start AND step_date <= :today
    """)

    result = await db.execute(
        combined_sql,
        {
            "year": year,
            "daily_goal": settings.daily_goal,
        }
    )
    row = result.first()

    total_steps = int(row[0])
    total_days = int(row[1])
    avg_steps = int(row[2])
    max_steps = int(row[3])
    best_day_date = row[4].isoformat() if row[4] else None
    days_goal_met = int(row[5])

    # Get week comparison (across years)
    week_result = await db.execute(
        week_sql,
        {
            "week_start": week_start,
            "last_week_start": last_week_start,
            "today": today
        }
    )
    week_row = week_result.first()
    this_week_steps = int(week_row[0])
    last_week_steps = int(week_row[1])

    # Calculate streak using window function query
    current_streak = await _calculate_streak_sql(db, year, today, settings.daily_goal)

    # Week comparison
    week_comparison = None
    if last_week_steps > 0:
        week_comparison = round(((this_week_steps - last_week_steps) / last_week_steps) * 100, 1)

    # Convert steps to miles
    total_distance = total_steps / settings.steps_per_mile
    avg_daily_miles = avg_steps / settings.steps_per_mile

    position = calculate_position(total_distance)

    # Calculate all-time position for the map (across all years)
    all_time_steps = await _get_all_time_steps(db)
    all_time_distance = all_time_steps / settings.steps_per_mile
    all_time_position = calculate_position(all_time_distance)

    # Calculate ETA to Boston (based on all-time progress)
    miles_remaining = TOTAL_ROUTE_DISTANCE - all_time_position["effective_miles"]
    days_to_boston = None
    eta_date = None
    if avg_daily_miles > 0 and miles_remaining > 0:
        days_to_boston = int(miles_remaining / avg_daily_miles)
        eta_date = (today + timedelta(days=days_to_boston)).isoformat()

    return {
        "year": year,
        "total_distance_miles": round(total_distance, 2),
        "total_steps": total_steps,
        "total_days": total_days,
        "crossings_completed": all_time_position["crossings_completed"],
        "avg_daily_steps": avg_steps,
        "best_day_steps": max_steps,
        "best_day_date": best_day_date,
        "days_goal_met": days_goal_met,
        "goal_met_percentage": round((days_goal_met / total_days * 100), 1) if total_days > 0 else 0,
        "current_streak": current_streak,
        "this_week_steps": this_week_steps,
        "last_week_steps": last_week_steps,
        "week_comparison": week_comparison,
        "miles_remaining": round(miles_remaining, 1),
        "days_to_boston": days_to_boston,
        "eta_date": eta_date,
        "current_position": {
            "lat": all_time_position["lat"],
            "lon": all_time_position["lon"],
            "miles_traveled": all_time_position["miles_traveled"],
            "effective_miles": all_time_position["effective_miles"],
            "current_waypoint": all_time_position["current_waypoint"],
            "next_waypoint": all_time_position["next_waypoint"],
            "miles_to_next": round(all_time_position["miles_to_next"], 1),
            "percent_complete": round(all_time_position["percent_complete"], 1),
        },
        "all_time_steps": all_time_steps,
        "all_time_distance_miles": round(all_time_distance, 2),
    }


@app.get("/api/stats")
async def get_stats(
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get dashboard statistics based on daily steps.

    Uses caching - stats are recomputed only when underlying data changes.
    Defaults to current year if not specified.
    """
    if year is None:
        year = datetime.now(EST).date().year

    today = datetime.now(EST).date()

    # Check cache
    current_hash = await _compute_data_hash(db, year, today)

    cache_result = await db.execute(
        select(StatsCache).where(StatsCache.year == year)
    )
    cached = cache_result.scalar_one_or_none()

    if cached and cached.data_hash == current_hash:
        logger.debug(f"Stats cache hit for year {year}")
        return json.loads(cached.stats_json)

    # Cache miss or stale - recompute
    logger.info(f"Stats cache miss for year {year}, recomputing...")
    stats = await _compute_stats(db, year, settings)

    # Update cache
    stats_json = json.dumps(stats)
    stmt = insert(StatsCache).values(
        year=year,
        stats_json=stats_json,
        data_hash=current_hash
    )
    stmt = stmt.on_duplicate_key_update(
        stats_json=stats_json,
        data_hash=current_hash
    )
    await db.execute(stmt)
    await db.commit()

    return stats


@app.get("/api/steps", response_model=list[DailyStepsSchema])
async def get_steps(
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get daily steps data within a date range."""
    if not start:
        start = date.today() - timedelta(days=30)
    if not end:
        end = date.today()

    result = await db.execute(
        select(DailySteps)
        .where(DailySteps.step_date >= start)
        .where(DailySteps.step_date <= end)
        .order_by(DailySteps.step_date)
    )
    return result.scalars().all()


@app.post("/api/steps", response_model=StepsResponse)
async def upsert_steps(
    data: StepsInput,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """
    Upsert daily steps from iOS Shortcut.
    Insert if date doesn't exist, update only if new value is higher.
    """
    stmt = insert(DailySteps).values(
        step_date=data.date,
        steps=data.steps,
        goal=settings.daily_goal,
    )
    # Only update if new value is higher than existing
    stmt = stmt.on_duplicate_key_update(
        steps=func.greatest(DailySteps.steps, stmt.inserted.steps),
    )
    await db.execute(stmt)
    await db.commit()

    logger.info(f"Upserted steps: {data.date} -> {data.steps}")

    return StepsResponse(
        status="ok",
        date=data.date,
        steps=data.steps
    )


@app.get("/api/activities", response_model=list[ActivitySchema])
async def get_activities(
    year: Optional[int] = Query(default=None),
    limit: int = Query(default=50, le=500),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get walking activities list."""
    query = select(Activity)

    if year:
        query = query.where(extract("year", Activity.activity_date) == year)

    query = query.order_by(Activity.activity_date.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@app.get("/api/route", response_model=RouteSchema)
async def get_route():
    """Get I-90 route waypoints for map rendering."""
    waypoints = get_route_waypoints()
    return RouteSchema(
        total_distance=TOTAL_ROUTE_DISTANCE,
        waypoints=[
            WaypointSchema(
                index=wp.index,
                city=wp.city,
                miles_from_start=wp.miles_from_start,
                lat=wp.lat,
                lon=wp.lon
            )
            for wp in waypoints
        ]
    )


@app.get("/api/config")
async def get_config():
    """Get public configuration values for frontend."""
    return {
        "steps_per_mile": settings.steps_per_mile,
        "daily_goal": settings.daily_goal,
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
