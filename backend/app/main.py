import hashlib
import json
import logging
import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select, extract, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from app.config import get_settings, Settings
from app.database import get_db, init_db, dispose_engine, init_engine, retry_on_connection_error
from app.models import Activity, DailySteps, StatsCache
from app.schemas import (
    ActivitySchema, DailyStepsSchema,
    RouteSchema, WaypointSchema,
    StepsInput, StepsResponse
)
from app.route import get_route_waypoints, calculate_position, TOTAL_ROUTE_DISTANCE
from app.detailed_stats import get_detailed_stats as detailed_stats_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Security scheme for OpenAPI docs (shows "Authorize" button)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
shortcut_secret_header = APIKeyHeader(name="X-Shortcut-Secret", auto_error=False)


async def verify_api_key(
    x_api_key: Optional[str] = Depends(api_key_header),
    settings: Settings = Depends(get_settings),
):
    """Dependency to verify API key for private endpoints."""
    configured_key = settings.api_key.get_secret_value().strip()
    if not configured_key:
        raise HTTPException(
            status_code=404,
            detail="Not found"
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


async def verify_shortcut_secret(
    x_shortcut_secret: Optional[str] = Depends(shortcut_secret_header),
    settings: Settings = Depends(get_settings),
):
    configured_secret = settings.shortcut_secret.get_secret_value().strip()
    if not configured_secret:
        raise HTTPException(
            status_code=503,
            detail="Shortcut secret not configured"
        )
    if not x_shortcut_secret:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Shortcut-Secret header"
        )
    if not secrets.compare_digest(x_shortcut_secret.strip(), configured_secret):
        raise HTTPException(
            status_code=401,
            detail="Invalid shortcut secret"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    await init_db()
    yield
    await dispose_engine()


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
    allow_headers=["Content-Type", "X-API-Key", "X-Shortcut-Secret"],
)


# --- Data Retrieval ---

EST = ZoneInfo("America/New_York")


async def _fetch_aggregates(db: AsyncSession, year: int, today: date, settings: Settings) -> dict:
    """Fetch all aggregate data needed for hash computation and stats.

    Consolidates queries that were previously duplicated between
    _compute_data_hash() and _compute_stats().
    """
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)
    streak_window_start = today - timedelta(days=30)

    year_result = await db.execute(
        text("""
            SELECT
                MAX(step_date),
                COALESCE(SUM(steps), 0),
                COUNT(*),
                COALESCE(AVG(steps), 0),
                COALESCE(MAX(steps), 0),
                COALESCE(SUM(CASE WHEN steps >= :daily_goal THEN 1 ELSE 0 END), 0),
                (
                    SELECT step_date
                    FROM daily_steps
                    WHERE YEAR(step_date) = :year
                    ORDER BY steps DESC, step_date ASC
                    LIMIT 1
                ) as best_day_date
            FROM daily_steps
            WHERE YEAR(step_date) = :year
        """),
        {"year": year, "daily_goal": settings.daily_goal}
    )
    year_row = year_result.first()

    daily_result = await db.execute(
        text("""
            SELECT GROUP_CONCAT(CONCAT(step_date, ':', steps) ORDER BY step_date SEPARATOR ',')
            FROM daily_steps
            WHERE step_date >= :start_date
        """),
        {"start_date": streak_window_start}
    )
    daily_fingerprint = daily_result.scalar() or ""

    all_time_result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(steps), 0),
                COUNT(*),
                COALESCE(AVG(steps), 0),
                COALESCE(MAX(steps), 0),
                COALESCE(SUM(CASE WHEN steps >= :daily_goal THEN 1 ELSE 0 END), 0),
                (
                    SELECT step_date
                    FROM daily_steps
                    ORDER BY steps DESC, step_date ASC
                    LIMIT 1
                ) as best_day_date
            FROM daily_steps
        """),
        {"daily_goal": settings.daily_goal}
    )
    all_time_row = all_time_result.first()

    week_result = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(CASE WHEN step_date >= :week_start AND step_date <= :today
                             THEN steps ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN step_date >= :last_week_start AND step_date < :week_start
                             THEN steps ELSE 0 END), 0)
            FROM daily_steps
            WHERE step_date >= :last_week_start AND step_date <= :today
        """),
        {"week_start": week_start, "last_week_start": last_week_start, "today": today}
    )
    week_row = week_result.first()

    return {
        "year_max_date": year_row[0],
        "year_sum": int(year_row[1]),
        "year_count": int(year_row[2]),
        "year_avg": int(year_row[3]),
        "year_max": int(year_row[4]),
        "year_goal_met": int(year_row[5]),
        "year_best_day_date": year_row[6],
        "daily_fingerprint": daily_fingerprint,
        "all_time_sum": int(all_time_row[0]),
        "all_time_count": int(all_time_row[1]),
        "all_time_avg": int(all_time_row[2]),
        "all_time_max": int(all_time_row[3]),
        "all_time_goal_met": int(all_time_row[4]),
        "all_time_best_day_date": all_time_row[5],
        "this_week_steps": int(week_row[0]),
        "last_week_steps": int(week_row[1]),
    }


async def _compute_data_hash(aggregates: dict, today: date, settings: Settings) -> str:
    """Compute a hash of the underlying data to detect changes.

    Includes factors that affect stats:
    - Year-specific: max date, sum, count, individual daily values (for streaks)
    - Cross-year: recent data for week comparisons, all-time totals for position
    - Time-relative: today's date (streak/week calculations are date-relative)
    """
    hash_input = "|".join([
        str(aggregates["year_max_date"]),
        str(aggregates["year_sum"]),
        str(aggregates["year_count"]),
        str(aggregates["year_max"]),
        str(aggregates["year_goal_met"]),
        str(aggregates["year_best_day_date"]),
        aggregates["daily_fingerprint"],
        str(aggregates["all_time_sum"]),
        str(aggregates["all_time_count"]),
        str(aggregates["all_time_max"]),
        str(aggregates["all_time_goal_met"]),
        str(aggregates["all_time_best_day_date"]),
        str(aggregates["this_week_steps"] + aggregates["last_week_steps"]),
        today.isoformat(),
        str(settings.steps_per_mile),
        str(settings.daily_goal),
    ])
    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


async def _calculate_streak_sql(
    db: AsyncSession,
    today: date,
    daily_goal: int,
    year: Optional[int] = None,
) -> int:
    """Calculate current streak using MySQL window functions.

    Uses LAG to detect gaps in consecutive goal-met days, then finds
    the streak that includes today or yesterday.
    """
    yesterday = today - timedelta(days=1)
    date_filter = ""
    params = {"daily_goal": daily_goal, "yesterday": yesterday}

    if year is not None:
        date_filter = "AND YEAR(step_date) = :year"
        params["year"] = year

    # This query:
    # 1. Filters to days where goal was met
    # 2. Uses LAG to get previous goal-met date
    # 3. Calculates if there's a gap (more than 1 day between consecutive goal-met days)
    # 4. Creates streak groups using a running sum of gap flags
    # 5. Finds the streak containing today or yesterday and counts its days
    streak_sql = text(f"""
        WITH goal_met_days AS (
            SELECT
                step_date,
                LAG(step_date) OVER (ORDER BY step_date) as prev_date
            FROM daily_steps
            WHERE steps >= :daily_goal
              {date_filter}
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

    result = await db.execute(streak_sql, params)
    return result.scalar() or 0


async def _compute_stats(db: AsyncSession, aggregates: dict, year: int, today: date, settings: Settings) -> dict:
    """Compute all statistics using pre-fetched aggregates plus streak queries."""
    total_steps = aggregates["year_sum"]
    total_days = aggregates["year_count"]
    avg_steps = aggregates["year_avg"]
    max_steps = aggregates["year_max"]
    best_day_date = aggregates["year_best_day_date"].isoformat() if aggregates["year_best_day_date"] else None
    days_goal_met = aggregates["year_goal_met"]

    all_time_steps = aggregates["all_time_sum"]
    all_time_total_days = aggregates["all_time_count"]
    all_time_avg_steps = aggregates["all_time_avg"]
    all_time_best_day_steps = aggregates["all_time_max"]
    all_time_best_day_date = aggregates["all_time_best_day_date"].isoformat() if aggregates["all_time_best_day_date"] else None
    all_time_days_goal_met = aggregates["all_time_goal_met"]

    this_week_steps = aggregates["this_week_steps"]
    last_week_steps = aggregates["last_week_steps"]

    current_streak = await _calculate_streak_sql(db, today, settings.daily_goal, year=year)
    all_time_current_streak = await _calculate_streak_sql(db, today, settings.daily_goal)

    # Week comparison
    week_comparison = None
    if last_week_steps > 0:
        week_comparison = round(((this_week_steps - last_week_steps) / last_week_steps) * 100, 1)

    # Convert steps to miles
    total_distance = total_steps / settings.steps_per_mile
    avg_daily_miles = avg_steps / settings.steps_per_mile

    # Calculate all-time position for the map (across all years)
    all_time_distance = all_time_steps / settings.steps_per_mile
    all_time_position = calculate_position(all_time_distance)

    # Calculate ETA to Boston (based on all-time progress)
    miles_remaining = TOTAL_ROUTE_DISTANCE - all_time_position["effective_miles"]
    steps_to_boston = int(miles_remaining * settings.steps_per_mile)
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
        "steps_to_boston": steps_to_boston,
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
        "all_time_total_days": all_time_total_days,
        "all_time_distance_miles": round(all_time_distance, 2),
        "all_time_avg_daily_steps": all_time_avg_steps,
        "all_time_best_day_steps": all_time_best_day_steps,
        "all_time_best_day_date": all_time_best_day_date,
        "all_time_days_goal_met": all_time_days_goal_met,
        "all_time_goal_met_percentage": round((all_time_days_goal_met / all_time_total_days * 100), 1) if all_time_total_days > 0 else 0,
        "all_time_current_streak": all_time_current_streak,
    }


@app.get("/api/stats")
@retry_on_connection_error(max_retries=1)
async def get_stats(
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics based on daily steps.

    Uses caching - stats are recomputed only when underlying data changes.
    Defaults to current year if not specified.
    """
    if year is None:
        year = datetime.now(EST).date().year

    today = datetime.now(EST).date()

    aggregates = await _fetch_aggregates(db, year, today, settings)
    current_hash = await _compute_data_hash(aggregates, today, settings)

    cache_result = await db.execute(
        select(StatsCache).where(StatsCache.year == year)
    )
    cached = cache_result.scalar_one_or_none()

    if cached and cached.data_hash == current_hash:
        logger.debug(f"Stats cache hit for year {year}")
        return json.loads(cached.stats_json)

    # Cache miss or stale - recompute
    logger.info(f"Stats cache miss for year {year}, recomputing...")
    stats = await _compute_stats(db, aggregates, year, today, settings)

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
    try:
        await db.execute(stmt)
        await db.commit()
    except Exception:
        logger.warning(f"Failed to cache stats for year {year}", exc_info=True)
        await db.rollback()

    return stats


@app.get("/api/detailed-stats")
@retry_on_connection_error(max_retries=1)
async def get_detailed_stats(
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed leaderboard statistics for the Stats page."""
    return await detailed_stats_handler(year=year, db=db)


@app.get("/api/steps", response_model=list[DailyStepsSchema])
@retry_on_connection_error(max_retries=1)
async def get_steps(
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get daily steps data within a date range."""
    today = datetime.now(EST).date()
    if not start:
        start = today - timedelta(days=30)
    if not end:
        end = today

    result = await db.execute(
        select(DailySteps)
        .where(DailySteps.step_date >= start)
        .where(DailySteps.step_date <= end)
        .order_by(DailySteps.step_date)
    )
    return result.scalars().all()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log request body on validation errors to help debug shortcut issues."""
    body = await request.body()
    safe_errors = []
    for err in exc.errors():
        safe_err = dict(err)
        if "ctx" in safe_err:
            safe_err["ctx"] = {k: str(v) for k, v in safe_err["ctx"].items()}
        safe_errors.append(safe_err)
    logger.warning(
        f"Validation error for {request.method} {request.url}: "
        f"{body.decode()!r} - {safe_errors}"
    )
    return JSONResponse(
        status_code=422,
        content={"detail": safe_errors},
    )


@app.post("/api/steps", response_model=StepsResponse)
@retry_on_connection_error(max_retries=1)
async def upsert_steps(
    data: StepsInput,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_shortcut_secret),
):
    """
    Public upsert endpoint for the iOS Shortcut.
    Inserts if the date doesn't exist, otherwise overwrites with the latest value.
    """
    stmt = insert(DailySteps).values(
        step_date=data.date,
        steps=data.steps,
        goal=settings.daily_goal,
    )
    # Always overwrite with the latest posted value so the daily shortcut sync wins.
    stmt = stmt.on_duplicate_key_update(
        steps=stmt.inserted.steps,
    )
    await db.execute(stmt)
    await db.commit()

    logger.info(f"Upserted steps: {data.date} -> {data.steps}")

    return StepsResponse(
        status="ok",
        date=data.date,
        steps=data.steps
    )


@app.get("/api/log-steps")
@retry_on_connection_error(max_retries=1)
async def log_steps_get(
    log_date: date = Query(..., alias="date"),
    steps: int = Query(..., ge=0, le=500_000),
    secret: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Simple GET endpoint for logging steps via URL query parameters.

    Useful for Shortcuts automations that struggle with JSON body variables.
    The secret is passed as a query param, which is acceptable for personal use
    with a low threat model.
    """
    settings = get_settings()
    configured_secret = settings.shortcut_secret.get_secret_value().strip()
    if not configured_secret or not secrets.compare_digest(secret.strip(), configured_secret):
        raise HTTPException(status_code=401, detail="Invalid shortcut secret")

    stmt = insert(DailySteps).values(
        step_date=log_date,
        steps=steps,
        goal=settings.daily_goal,
    )
    stmt = stmt.on_duplicate_key_update(
        steps=stmt.inserted.steps,
    )
    await db.execute(stmt)
    await db.commit()

    logger.info(f"Upserted steps via GET: {log_date} -> {steps}")

    return {"status": "ok", "date": log_date.isoformat(), "steps": steps}


@app.get("/api/activities", response_model=list[ActivitySchema])
@retry_on_connection_error(max_retries=1)
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
    return {"status": "healthy", "timestamp": datetime.now(EST).isoformat()}
