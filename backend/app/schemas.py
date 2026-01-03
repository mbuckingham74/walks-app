from datetime import date
from decimal import Decimal
from pydantic import BaseModel, field_validator
from typing import Optional


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


class PositionSchema(BaseModel):
    lat: float
    lon: float
    miles_traveled: float
    current_waypoint: WaypointSchema
    next_waypoint: Optional[WaypointSchema]
    miles_to_next: float
    percent_complete: float


class StatsSchema(BaseModel):
    year: int
    total_distance_miles: float
    total_walks: int
    crossings_completed: int
    current_position: PositionSchema


class StepsInput(BaseModel):
    date: date
    steps: int

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
