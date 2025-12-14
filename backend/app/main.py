import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from app.config import get_settings
from app.database import get_db, init_db
from app.models import Activity, DailySteps, RouteProgress
from app.schemas import (
    ActivitySchema, DailyStepsSchema,
    RouteSchema, WaypointSchema, StatsSchema, PositionSchema,
    StepsInput, StepsResponse
)
from app.route import get_route_waypoints, calculate_position, TOTAL_ROUTE_DISTANCE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Data Retrieval ---

STEPS_PER_MILE = 2000
EST = ZoneInfo("America/New_York")


@app.get("/api/stats")
async def get_stats(
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics based on daily steps. Defaults to current year if not specified."""
    if year is None:
        year = datetime.now(EST).date().year

    # Get total steps, days walked, avg, max for the year
    result = await db.execute(
        select(
            func.sum(DailySteps.steps),
            func.count(DailySteps.id),
            func.avg(DailySteps.steps),
            func.max(DailySteps.steps)
        ).where(extract("year", DailySteps.step_date) == year)
    )
    row = result.first()
    total_steps = int(row[0] or 0)
    total_days = row[1] or 0
    avg_steps = int(row[2] or 0)
    max_steps = int(row[3] or 0)

    # Get best day date
    best_day_result = await db.execute(
        select(DailySteps.step_date)
        .where(extract("year", DailySteps.step_date) == year)
        .where(DailySteps.steps == max_steps)
        .limit(1)
    )
    best_day_row = best_day_result.first()
    best_day_date = best_day_row[0].isoformat() if best_day_row else None

    # Get days goal met (goal >= 10000)
    goal_met_result = await db.execute(
        select(func.count(DailySteps.id))
        .where(extract("year", DailySteps.step_date) == year)
        .where(DailySteps.steps >= 10000)
    )
    days_goal_met = goal_met_result.scalar() or 0

    # Calculate current streak (consecutive days meeting goal, ending today or yesterday)
    all_steps_result = await db.execute(
        select(DailySteps.step_date, DailySteps.steps)
        .where(extract("year", DailySteps.step_date) == year)
        .order_by(DailySteps.step_date.desc())
    )
    all_steps = all_steps_result.all()

    current_streak = 0
    # Use EST timezone for "today" since Health data uses phone's local time
    today = datetime.now(EST).date()
    expected_date = today

    for step_date, steps in all_steps:
        # Allow streak to start from today or yesterday
        if current_streak == 0 and step_date < today - timedelta(days=1):
            break
        if current_streak == 0 and step_date <= today:
            expected_date = step_date

        if step_date == expected_date and steps >= 10000:
            current_streak += 1
            expected_date = step_date - timedelta(days=1)
        elif step_date == expected_date:
            break  # Goal not met, streak ends
        # Skip if date doesn't match (gap in data)

    # This week vs last week comparison (using EST)
    today = datetime.now(EST).date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    last_week_start = week_start - timedelta(days=7)

    this_week_result = await db.execute(
        select(func.sum(DailySteps.steps))
        .where(DailySteps.step_date >= week_start)
        .where(DailySteps.step_date <= today)
    )
    this_week_steps = int(this_week_result.scalar() or 0)

    last_week_result = await db.execute(
        select(func.sum(DailySteps.steps))
        .where(DailySteps.step_date >= last_week_start)
        .where(DailySteps.step_date < week_start)
    )
    last_week_steps = int(last_week_result.scalar() or 0)

    week_comparison = None
    if last_week_steps > 0:
        week_comparison = round(((this_week_steps - last_week_steps) / last_week_steps) * 100, 1)

    # Convert steps to miles (2000 steps = 1 mile)
    total_distance = total_steps / STEPS_PER_MILE
    avg_daily_miles = avg_steps / STEPS_PER_MILE

    position = calculate_position(total_distance)

    # Calculate ETA to Boston (using EST)
    miles_remaining = TOTAL_ROUTE_DISTANCE - position["effective_miles"]
    days_to_boston = None
    eta_date = None
    if avg_daily_miles > 0 and miles_remaining > 0:
        days_to_boston = int(miles_remaining / avg_daily_miles)
        eta_date = (datetime.now(EST).date() + timedelta(days=days_to_boston)).isoformat()

    return {
        "year": year,
        "total_distance_miles": round(total_distance, 2),
        "total_steps": total_steps,
        "total_days": total_days,
        "crossings_completed": position["crossings_completed"],
        # New stats
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
            "lat": position["lat"],
            "lon": position["lon"],
            "miles_traveled": position["miles_traveled"],
            "effective_miles": position["effective_miles"],
            "current_waypoint": position["current_waypoint"],
            "next_waypoint": position["next_waypoint"],
            "miles_to_next": round(position["miles_to_next"], 1),
            "percent_complete": round(position["percent_complete"], 1),
        }
    }


@app.get("/api/steps", response_model=list[DailyStepsSchema])
async def get_steps(
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
):
    """
    Upsert daily steps from iOS Shortcut.
    Insert if date doesn't exist, update if it does.
    """
    stmt = insert(DailySteps).values(
        step_date=data.date,
        steps=data.steps,
        goal=10000,
    )
    stmt = stmt.on_duplicate_key_update(
        steps=data.steps,
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
    db: AsyncSession = Depends(get_db)
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


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
