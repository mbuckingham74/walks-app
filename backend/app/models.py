from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Date, DateTime,
    DECIMAL, func
)
from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_activity_id = Column(BigInteger, unique=True, nullable=False)
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
    goal = Column(Integer, default=15000)
    distance_miles = Column(DECIMAL(10, 2))
    floors_climbed = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class StatsCache(Base):
    """Cache for computed statistics to avoid recalculating on every request."""
    __tablename__ = "stats_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, unique=True, nullable=False)
    stats_json = Column(Text, nullable=False)  # JSON blob of full stats response
    data_hash = Column(String(64), nullable=False)  # Hash of underlying data for invalidation
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
