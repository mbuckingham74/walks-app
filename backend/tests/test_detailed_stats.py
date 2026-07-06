from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.detailed_stats import (
    _compute_best_day_of_week,
    _compute_day_of_week_breakdown,
    _compute_longest_streak,
    _compute_monthly_totals,
    _compute_steps_distribution,
    _week_start_end,
)


class TestWeekStartEnd:
    def test_week_1_returns_correct_range(self):
        start, end = _week_start_end(2026, 1)
        assert start == date(2025, 12, 29)
        assert end == date(2026, 1, 4)
        assert start.weekday() == 0
        assert end.weekday() == 6

    def test_week_20_returns_correct_range(self):
        start, end = _week_start_end(2026, 20)
        assert start == date(2026, 5, 11)
        assert end == date(2026, 5, 17)


class TestDayOfWeekBreakdown:
    def test_empty_rows_returns_zeroed_breakdown(self):
        result = _compute_day_of_week_breakdown([])
        assert len(result) == 7
        assert all(r.count == 0 for r in result)
        assert result[0].day == "Monday"
        assert result[6].day == "Sunday"

    def test_computes_averages(self):
        rows = [
            {"date": date(2026, 1, 5), "steps": 10000},  # Monday
            {"date": date(2026, 1, 12), "steps": 20000},  # Monday
            {"date": date(2026, 1, 6), "steps": 15000},  # Tuesday
        ]
        result = _compute_day_of_week_breakdown(rows)
        monday = result[0]
        tuesday = result[1]
        assert monday.total_steps == 30000
        assert monday.count == 2
        assert monday.avg_steps == 15000
        assert tuesday.avg_steps == 15000


class TestBestDayOfWeek:
    def test_returns_day_with_highest_average(self):
        rows = [
            {"date": date(2026, 1, 5), "steps": 10000},  # Monday
            {"date": date(2026, 1, 12), "steps": 20000},  # Monday
            {"date": date(2026, 1, 6), "steps": 5000},  # Tuesday
        ]
        breakdown = _compute_day_of_week_breakdown(rows)
        best = _compute_best_day_of_week(breakdown)
        assert best.day == "Monday"
        assert best.avg_steps == 15000

    def test_no_data_returns_none(self):
        assert _compute_best_day_of_week([]) is None


class TestLongestStreak:
    def test_no_goal_met_days_returns_none(self):
        rows = [
            {"date": date(2026, 1, 1), "steps": 1000},
        ]
        assert _compute_longest_streak(rows, daily_goal=15000) is None

    def test_single_streak(self):
        rows = [
            {"date": date(2026, 1, 1), "steps": 15000},
            {"date": date(2026, 1, 2), "steps": 16000},
            {"date": date(2026, 1, 4), "steps": 17000},
        ]
        streak = _compute_longest_streak(rows, daily_goal=15000)
        assert streak.length == 2
        assert streak.start_date == date(2026, 1, 1)
        assert streak.end_date == date(2026, 1, 2)

    def test_gaps_break_streak(self):
        rows = [
            {"date": date(2026, 1, 1), "steps": 15000},
            {"date": date(2026, 1, 3), "steps": 16000},
            {"date": date(2026, 1, 4), "steps": 17000},
        ]
        streak = _compute_longest_streak(rows, daily_goal=15000)
        assert streak.length == 2
        assert streak.start_date == date(2026, 1, 3)


class TestStepsDistribution:
    def test_empty_data(self):
        result = _compute_steps_distribution([])
        assert len(result) == 6
        assert all(b.count == 0 for b in result)

    def test_buckets_counted_correctly(self):
        rows = [
            {"date": date(2026, 1, 1), "steps": 3000},
            {"date": date(2026, 1, 2), "steps": 8000},
            {"date": date(2026, 1, 3), "steps": 12000},
            {"date": date(2026, 1, 4), "steps": 17000},
            {"date": date(2026, 1, 5), "steps": 22000},
            {"date": date(2026, 1, 6), "steps": 26000},
        ]
        result = _compute_steps_distribution(rows)
        labels = [b.label for b in result]
        assert labels == ["0–5k", "5–10k", "10–15k", "15–20k", "20–25k", "25k+"]
        assert [b.count for b in result] == [1, 1, 1, 1, 1, 1]
        assert all(b.percentage == pytest.approx(16.7, 0.1) for b in result)


class TestMonthlyTotals:
    def test_computes_monthly_totals(self):
        rows = [
            {"date": date(2026, 1, 1), "steps": 10000},
            {"date": date(2026, 1, 2), "steps": 20000},
            {"date": date(2026, 2, 1), "steps": 15000},
        ]
        result = _compute_monthly_totals(rows, 2026, daily_goal=15000)
        assert len(result) == 2
        jan = result[0]
        assert jan.month_name == "January"
        assert jan.total_steps == 30000
        assert jan.avg_steps == 15000
        assert jan.goal_met_days == 1


class TestDetailedStatsEndpoint:
    @pytest.fixture
    def detailed_client(self, client):
        """Return a client with mocked DB responses for detailed stats."""
        from app.main import app, get_db

        # Build sequential results for the queries made by get_detailed_stats.
        mock_results = []

        def add_scalar(value):
            m = MagicMock()
            m.scalar_one_or_none.return_value = None
            m.scalar.return_value = value
            m.first.return_value = None
            mock_results.append(m)

        def add_first(row_tuple):
            m = MagicMock()
            m.scalar_one_or_none.return_value = None
            m.scalar.return_value = None
            m.first.return_value = row_tuple
            mock_results.append(m)

        def add_all(rows):
            m = MagicMock()
            m.scalar_one_or_none.return_value = None
            m.scalar.return_value = None
            m.first.return_value = None
            m.all.return_value = rows
            mock_results.append(m)

        # 1. data hash fingerprint
        add_scalar("2026-01-01:10000|2026-01-02:20000")
        # 2. cache lookup miss
        add_scalar(None)
        # 3. daily steps
        add_all([
            (date(2026, 1, 1), 10000),
            (date(2026, 1, 2), 20000),
        ])
        # 4. year aggregates
        add_first((30000, 2, 15000, 20000, date(2026, 1, 2), 1))
        # 5. top days
        add_all([
            (date(2026, 1, 2), 20000),
            (date(2026, 1, 1), 10000),
        ])
        # 6. top weeks
        add_all([
            (2026, 1, 30000, 2),
        ])
        # 7. top months
        add_all([
            (2026, 1, 30000, 2),
        ])
        # 8. cache insert
        add_scalar(1)

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_results

        async def override():
            yield mock_session

        app.dependency_overrides[get_db] = override
        try:
            yield client
        finally:
            app.dependency_overrides.clear()

    def test_detailed_stats_returns_expected_shape(self, detailed_client):
        resp = detailed_client.get("/api/detailed-stats?year=2026")
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2026
        assert len(data["top_days"]) == 2
        assert data["top_days"][0]["steps"] == 20000
        assert len(data["top_weeks"]) == 1
        assert len(data["top_months"]) == 1
        assert data["year_summary"]["total_steps"] == 30000
        assert "consistency" in data
        assert "steps_distribution" in data
        assert "cumulative_data" in data

    def test_detailed_stats_invalid_year_returns_400(self, detailed_client):
        resp = detailed_client.get("/api/detailed-stats?year=1800")
        assert resp.status_code == 400

    def test_detailed_stats_defaults_to_current_year(self, detailed_client):
        from datetime import datetime
        current_year = datetime.now().year
        resp = detailed_client.get("/api/detailed-stats")
        assert resp.status_code == 200
        assert resp.json()["year"] == current_year
