from datetime import date, datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, field_validator
from typing import Optional
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo("America/New_York")
MAX_BACKFILL_DAYS = 730
MAX_FUTURE_DAYS = 1


class ActivitySchema(BaseModel):
    id: int
    external_activity_id: int
    activity_date: date
    activity_name: Optional[str]
    distance_miles: Decimal
    duration_seconds: int
    start_lat: Optional[Decimal]
    start_lon: Optional[Decimal]
    end_lat: Optional[Decimal]
    end_lon: Optional[Decimal]
    average_speed_mph: Optional[Decimal]
    calories: Optional[int]

    class Config:
        from_attributes = True


class DailyStepsSchema(BaseModel):
    id: int
    step_date: date
    steps: int
    goal: int
    distance_miles: Optional[Decimal]
    floors_climbed: Optional[int]

    class Config:
        from_attributes = True


class WaypointSchema(BaseModel):
    index: int
    city: str
    miles_from_start: int
    lat: float
    lon: float


class RouteSchema(BaseModel):
    total_distance: int
    waypoints: list[WaypointSchema]


class StepsInput(BaseModel):
    date: date
    steps: int

    @field_validator("date")
    @classmethod
    def validate_date_bounds(cls, value: date) -> date:
        """Allow normal daily sync plus occasional historical backfills."""
        today = datetime.now(APP_TIMEZONE).date()
        earliest_allowed = today - timedelta(days=MAX_BACKFILL_DAYS)
        latest_allowed = today + timedelta(days=MAX_FUTURE_DAYS)

        if value < earliest_allowed:
            raise ValueError(
                f"date is too old; only the last {MAX_BACKFILL_DAYS} days are accepted"
            )
        if value > latest_allowed:
            raise ValueError(
                f"date cannot be more than {MAX_FUTURE_DAYS} day in the future"
            )
        return value

    @field_validator("steps")
    @classmethod
    def validate_steps_bounds(cls, v: int) -> int:
        """Validate steps is within reasonable bounds."""
        if v < 0:
            raise ValueError("steps cannot be negative")
        if v > 500_000:
            raise ValueError("steps exceeds maximum allowed value (500,000)")
        return v


class StepsResponse(BaseModel):
    status: str
    date: date
    steps: int
