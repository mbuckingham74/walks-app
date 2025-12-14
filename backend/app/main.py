import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.mysql import insert

from app.config import get_settings
from app.database import get_db, init_db
from app.models import Activity, DailySteps, SyncLog, RouteProgress, SyncType, SyncStatus
from app.schemas import (
    ActivitySchema, DailyStepsSchema, SyncStatusSchema,
    RouteSchema, WaypointSchema, StatsSchema, PositionSchema, SyncTriggerResponse,
    StepsInput, StepsResponse
)
from app.route import get_route_waypoints, calculate_position, TOTAL_ROUTE_DISTANCE
from app.garmin import get_garmin_client

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


# --- Sync Operations ---

async def perform_sync(
    sync_type: SyncType,
    db: AsyncSession,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """Background task to sync data from Garmin."""
    sync_log = SyncLog(sync_type=sync_type, status=SyncStatus.running)
    db.add(sync_log)
    await db.commit()
    await db.refresh(sync_log)

    records_fetched = 0

    try:
        garmin = get_garmin_client()
        await garmin.connect()

        if not start_date:
            start_date = date(2020, 1, 1)
        if not end_date:
            end_date = date.today()

        if sync_type in (SyncType.activities, SyncType.full):
            activities = garmin.get_activities(start_date, end_date)
            for act_data in activities:
                stmt = insert(Activity).values(**act_data)
                stmt = stmt.on_duplicate_key_update(
                    activity_name=act_data["activity_name"],
                    distance_miles=act_data["distance_miles"],
                    duration_seconds=act_data["duration_seconds"],
                    calories=act_data["calories"],
                )
                await db.execute(stmt)
            records_fetched += len(activities)

        if sync_type in (SyncType.steps, SyncType.full):
            steps = garmin.get_steps(start_date, end_date)
            for step_data in steps:
                stmt = insert(DailySteps).values(**step_data)
                stmt = stmt.on_duplicate_key_update(
                    steps=step_data["steps"],
                    goal=step_data["goal"],
                    distance_miles=step_data["distance_miles"],
                    floors_climbed=step_data["floors_climbed"],
                )
                await db.execute(stmt)
            records_fetched += len(steps)

        await db.commit()

        # Update route progress for current year
        await update_route_progress(db, date.today().year)

        sync_log.status = SyncStatus.success
        sync_log.records_fetched = records_fetched
        sync_log.completed_at = datetime.utcnow()

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sync_log.status = SyncStatus.failed
        sync_log.error_message = str(e)
        sync_log.completed_at = datetime.utcnow()

    await db.commit()


async def update_route_progress(db: AsyncSession, year: int):
    """Recalculate route progress for a given year based on daily steps."""
    result = await db.execute(
        select(
            func.sum(DailySteps.steps),
            func.count(DailySteps.id)
        ).where(extract("year", DailySteps.step_date) == year)
    )
    row = result.first()
    total_steps = int(row[0] or 0)
    total_days = row[1] or 0

    # Convert steps to miles (2000 steps = 1 mile)
    total_distance = total_steps / 2000

    position = calculate_position(total_distance)

    stmt = insert(RouteProgress).values(
        year=year,
        total_distance_miles=total_distance,
        total_walks=total_days,
        current_waypoint_index=position["current_waypoint"]["index"],
        current_lat=position["lat"],
        current_lon=position["lon"],
    )
    stmt = stmt.on_duplicate_key_update(
        total_distance_miles=total_distance,
        total_walks=total_days,
        current_waypoint_index=position["current_waypoint"]["index"],
        current_lat=position["lat"],
        current_lon=position["lon"],
    )
    await db.execute(stmt)
    await db.commit()


@app.post("/api/sync", response_model=SyncTriggerResponse)
async def trigger_full_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger a full sync of activities and steps from Garmin."""
    sync_log = SyncLog(sync_type=SyncType.full, status=SyncStatus.running)
    db.add(sync_log)
    await db.commit()
    await db.refresh(sync_log)

    background_tasks.add_task(perform_sync, SyncType.full, db)
    return SyncTriggerResponse(message="Full sync started", sync_id=sync_log.id)


@app.post("/api/sync/activities", response_model=SyncTriggerResponse)
async def trigger_activities_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger sync of activities only."""
    sync_log = SyncLog(sync_type=SyncType.activities, status=SyncStatus.running)
    db.add(sync_log)
    await db.commit()
    await db.refresh(sync_log)

    background_tasks.add_task(perform_sync, SyncType.activities, db)
    return SyncTriggerResponse(message="Activities sync started", sync_id=sync_log.id)


@app.post("/api/sync/steps", response_model=SyncTriggerResponse)
async def trigger_steps_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger sync of steps only."""
    sync_log = SyncLog(sync_type=SyncType.steps, status=SyncStatus.running)
    db.add(sync_log)
    await db.commit()
    await db.refresh(sync_log)

    background_tasks.add_task(perform_sync, SyncType.steps, db)
    return SyncTriggerResponse(message="Steps sync started", sync_id=sync_log.id)


@app.get("/api/sync/status", response_model=SyncStatusSchema)
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    """Get the status of the most recent sync operation."""
    result = await db.execute(
        select(SyncLog).order_by(SyncLog.id.desc()).limit(1)
    )
    sync_log = result.scalar_one_or_none()

    if not sync_log:
        raise HTTPException(status_code=404, detail="No sync operations found")

    return SyncStatusSchema(
        sync_type=sync_log.sync_type.value,
        started_at=sync_log.started_at,
        completed_at=sync_log.completed_at,
        status=sync_log.status.value,
        records_fetched=sync_log.records_fetched,
        error_message=sync_log.error_message,
    )


# --- Data Retrieval ---

STEPS_PER_MILE = 2000


@app.get("/api/stats")
async def get_stats(
    year: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics based on daily steps. Defaults to current year if not specified."""
    if year is None:
        year = date.today().year

    # Get total steps and days walked for the year
    result = await db.execute(
        select(
            func.sum(DailySteps.steps),
            func.count(DailySteps.id)
        ).where(extract("year", DailySteps.step_date) == year)
    )
    row = result.first()
    total_steps = int(row[0] or 0)
    total_days = row[1] or 0

    # Convert steps to miles (2000 steps = 1 mile)
    total_distance = total_steps / STEPS_PER_MILE

    position = calculate_position(total_distance)

    return {
        "year": year,
        "total_distance_miles": round(total_distance, 2),
        "total_steps": total_steps,
        "total_days": total_days,
        "crossings_completed": position["crossings_completed"],
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
