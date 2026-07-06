from datetime import date, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from app.schemas import StepsInput, MAX_BACKFILL_DAYS, MAX_FUTURE_DAYS


APP_TIMEZONE = ZoneInfo("America/New_York")


class TestStepsInput:
    def test_valid_input(self):
        today = date.today()
        data = StepsInput(date=today.isoformat(), steps=10000)
        assert data.steps == 10000
        assert data.date == today

    def test_zero_steps_valid(self):
        today = date.today()
        data = StepsInput(date=today.isoformat(), steps=0)
        assert data.steps == 0

    def test_max_steps_valid(self):
        today = date.today()
        data = StepsInput(date=today.isoformat(), steps=500_000)
        assert data.steps == 500_000

    def test_negative_steps_rejected(self):
        today = date.today()
        with pytest.raises(ValidationError, match="cannot be negative"):
            StepsInput(date=today.isoformat(), steps=-1)

    def test_steps_over_max_rejected(self):
        today = date.today()
        with pytest.raises(ValidationError, match="exceeds maximum"):
            StepsInput(date=today.isoformat(), steps=500_001)

    def test_old_date_rejected(self):
        today = date.today()
        too_old = today - timedelta(days=MAX_BACKFILL_DAYS + 10)
        with pytest.raises(ValidationError, match="too old"):
            StepsInput(date=too_old.isoformat(), steps=10000)

    def test_far_future_date_rejected(self):
        today = date.today()
        too_far = today + timedelta(days=MAX_FUTURE_DAYS + 5)
        with pytest.raises(ValidationError, match="future"):
            StepsInput(date=too_far.isoformat(), steps=10000)

    def test_boundary_date_max_backfill_accepted(self):
        today = date.today()
        boundary = today - timedelta(days=MAX_BACKFILL_DAYS)
        data = StepsInput(date=boundary.isoformat(), steps=5000)
        assert data.date == boundary

    def test_boundary_date_one_day_future_accepted(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        data = StepsInput(date=tomorrow.isoformat(), steps=5000)
        assert data.date == tomorrow
