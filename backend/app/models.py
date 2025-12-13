from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, BigInteger, String, Date, DateTime,
    DECIMAL, Text, Enum, func
)
from app.database import Base


class SyncType(PyEnum):
    activities = "activities"
    steps = "steps"
    full = "full"


class SyncStatus(PyEnum):
    running = "running"
    success = "success"
    failed = "failed"


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    garmin_activity_id = Column(BigInteger, unique=True, nullable=False)
    activity_date = Column(Date, nullable=False)
    activity_name = Column(String(255))
    distance_miles = Column(DECIMAL(10, 2), default=0)
    duration_seconds = Column(Integer, default=0)
    start_lat = Column(DECIMAL(10, 7))
    start_lon = Column(DECIMAL(10, 7))
    end_lat = Column(DECIMAL(10, 7))
    end_lon = Column(DECIMAL(10, 7))
    average_speed_mph = Column(DECIMAL(5, 2))
    calories = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DailySteps(Base):
    __tablename__ = "daily_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    step_date = Column(Date, unique=True, nullable=False)
    steps = Column(Integer, default=0)
    goal = Column(Integer, default=10000)
    distance_miles = Column(DECIMAL(10, 2))
    floors_climbed = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class SyncLog(Base):
    __tablename__ = "sync_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_type = Column(Enum(SyncType), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    status = Column(Enum(SyncStatus), default=SyncStatus.running)
    records_fetched = Column(Integer, default=0)
    error_message = Column(Text)


class RouteProgress(Base):
    __tablename__ = "route_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, unique=True, nullable=False)
    total_distance_miles = Column(DECIMAL(10, 2), default=0)
    total_walks = Column(Integer, default=0)
    current_waypoint_index = Column(Integer, default=0)
    current_lat = Column(DECIMAL(10, 7))
    current_lon = Column(DECIMAL(10, 7))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
