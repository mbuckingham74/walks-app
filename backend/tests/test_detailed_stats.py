from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.detailed_stats import (
    _compute_best_day_of_week,
    _compute_day_of_week_breakdown,
    _compute_longest_streak,
    _compute_monthly_totals,
    _compute_steps_distribution,
    _compute_activity_calendar,
    _compute_year_race,
    _compute_momentum,
    _compute_record_chase,
    _compute_weekly_finish_line,
    _compute_goal_surplus,
    _compute_rolling_records,
    _compute_day_percentile,
    _compute_milestone_timeline,
    _compute_perfect_periods,
    _compute_comeback_score,
    _previous_year_cutoff,
    _set_cached_detailed_stats,
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


class TestActivityCalendar:
    def test_fills_all_days_with_intensity(self):
        rows = [{"date": date(2026, 1, 1), "steps": 22500}]
        cal = _compute_activity_calendar(rows, 2026, date(2026, 1, 3), 15000)
        assert len(cal.days) == 3
        assert cal.days[0].intensity == 4
        assert cal.days[0].goal_met is True
        assert cal.days[1].intensity == 0
        assert cal.days[1].steps == 0

    def test_intensity_buckets(self):
        rows = [
            {"date": date(2026, 1, 1), "steps": 3000},   # <50% -> 1
            {"date": date(2026, 1, 2), "steps": 10000},  # 50-99% -> 2
            {"date": date(2026, 1, 3), "steps": 15000},  # 100-149% -> 3
            {"date": date(2026, 1, 4), "steps": 25000},  # >=150% -> 4
        ]
        cal = _compute_activity_calendar(rows, 2026, date(2026, 1, 4), 15000)
        assert [d.intensity for d in cal.days] == [1, 2, 3, 4]


class TestYearRace:
    def test_cumulative_aligned_by_day_of_year(self):
        current = [{"date": date(2026, 1, 1), "steps": 10000},
                   {"date": date(2026, 1, 2), "steps": 20000}]
        previous = [{"date": date(2025, 1, 1), "steps": 5000}]
        race = _compute_year_race(current, previous, 2026, 15000)
        assert race.current_year == 2026
        assert race.previous_year == 2025
        assert race.current[-1].cumulative_steps == 30000
        assert race.current[-1].day_of_year == 2
        assert race.previous[-1].cumulative_steps == 5000

    def test_previous_year_cutoff_matches_elapsed_day(self):
        assert _previous_year_cutoff(2026, date(2026, 7, 13)) == date(2025, 7, 13)

    def test_previous_year_cutoff_handles_leap_year_length(self):
        assert _previous_year_cutoff(2024, date(2025, 1, 1)) == date(2023, 12, 31)

    def test_empty_years(self):
        race = _compute_year_race([], [], 2026, 15000)
        assert race.current == []
        assert race.previous == []


class TestMomentum:
    def test_rolling_averages_after_window(self):
        rows = [{"date": date(2026, 1, 1) + timedelta(days=i), "steps": 10000}
                for i in range(10)]
        momentum = _compute_momentum(rows, 2026, date(2026, 1, 10))
        first = momentum[0]
        assert first.avg_7 is None
        assert first.avg_28 is None
        seventh = momentum[6]
        assert seventh.avg_7 == 10000
        assert seventh.avg_28 is None


class TestRecordChase:
    def test_steps_needed_to_enter_top_10(self):
        rows = [{"date": date(2026, 1, d), "steps": 10000 + d * 100}
                for d in range(1, 11)]
        today = date(2026, 1, 11)
        chase = _compute_record_chase(rows + [{"date": today, "steps": 5000}], today)
        assert chase.in_top_10 is False
        assert chase.steps_to_top_10 == chase.top_10_threshold - 5000

    def test_already_in_top_10(self):
        rows = [{"date": date(2026, 1, d), "steps": 10000}
                for d in range(1, 11)]
        today = date(2026, 1, 11)
        chase = _compute_record_chase(rows + [{"date": today, "steps": 30000}], today)
        assert chase.in_top_10 is True
        assert chase.steps_to_top_10 == 0


class TestWeeklyFinishLine:
    def test_required_pace(self):
        today = date(2026, 1, 7)
        rows = [{"date": date(2026, 1, 5), "steps": 15000},
                {"date": date(2026, 1, 6), "steps": 15000},
                {"date": date(2026, 1, 7), "steps": 15000}]
        wfl = _compute_weekly_finish_line(rows, today, 15000)
        assert wfl.weekly_goal == 105000
        assert wfl.current_steps == 45000
        assert wfl.days_elapsed == 3
        assert wfl.days_remaining == 4
        assert wfl.required_daily_avg > 0


class TestGoalSurplus:
    def test_surplus_values(self):
        rows = [{"date": date(2026, 1, 1), "steps": 20000},
                {"date": date(2026, 1, 2), "steps": 10000}]
        surplus = _compute_goal_surplus(rows, 15000)
        assert surplus[0].surplus == 5000
        assert surplus[1].surplus == -5000


class TestRollingRecords:
    def test_best_window(self):
        rows = [{"date": date(2026, 1, 1) + timedelta(days=i),
                 "steps": 10000 if i < 7 else 20000}
                for i in range(14)]
        records = _compute_rolling_records(rows, 2026, date(2026, 1, 14))
        assert records.best_7 is not None
        assert records.best_7.total_steps == 7 * 20000
        assert records.best_7.start_date == date(2026, 1, 8)

    def test_insufficient_data_returns_none(self):
        rows = [{"date": date(2026, 1, 1), "steps": 10000}]
        records = _compute_rolling_records(rows, 2026, date(2026, 1, 1))
        assert records.best_7 is None
        assert records.best_30 is None


class TestDayPercentile:
    def test_percentile_of_today(self):
        rows = [{"date": date(2026, 1, d), "steps": d * 1000}
                for d in range(1, 11)]
        today = date(2026, 1, 10)
        pct = _compute_day_percentile(rows, today)
        assert pct.steps == 10000
        assert pct.percentile == 90.0

    def test_no_data_returns_none(self):
        assert _compute_day_percentile([], date(2026, 1, 1)) is None


class TestMilestoneTimeline:
    def test_seattle_reached_immediately(self):
        rows = [{"date": date(2026, 1, 1), "steps": 1850}]
        timeline = _compute_milestone_timeline(rows, 1850)
        assert timeline.crossings_completed == 0
        assert timeline.milestones[0].city == "Seattle, WA"
        assert timeline.milestones[0].reached is True
        assert timeline.milestones[1].reached is False

    def test_crossing_detected(self):
        rows = [{"date": date(2026, 1, 1), "steps": 2850 * 1850}]
        timeline = _compute_milestone_timeline(rows, 1850)
        assert timeline.crossings_completed == 1


class TestPerfectPeriods:
    def test_perfect_week_counted(self):
        rows = [{"date": date(2026, 1, 5) + timedelta(days=i), "steps": 16000}
                for i in range(7)]
        monthly = _compute_monthly_totals(rows, 2026, 15000)
        pp = _compute_perfect_periods(rows, 2026, date(2026, 1, 20), 15000, monthly)
        assert pp.perfect_weeks == 1
        assert pp.longest_5_of_7_run == 1

    def test_missing_week_breaks_5_of_7_streak(self):
        rows = []
        for monday in (date(2026, 1, 5), date(2026, 1, 19)):
            rows.extend(
                {"date": monday + timedelta(days=i), "steps": 16000}
                for i in range(5)
            )
        monthly = _compute_monthly_totals(rows, 2026, 15000)

        pp = _compute_perfect_periods(
            rows, 2026, date(2026, 1, 27), 15000, monthly
        )

        assert pp.longest_5_of_7_run == 1

    def test_no_data_returns_zeros(self):
        pp = _compute_perfect_periods([], 2026, date(2026, 1, 20), 15000, [])
        assert pp.perfect_weeks == 0
        assert pp.longest_5_of_7_run == 0
        assert pp.best_goal_met_month is None


class TestComebackScore:
    def test_bounce_back_after_miss(self):
        rows = [
            {"date": date(2026, 1, 1), "steps": 5000},   # miss
            {"date": date(2026, 1, 2), "steps": 16000},  # bounce back
            {"date": date(2026, 1, 3), "steps": 5000},   # miss
            {"date": date(2026, 1, 4), "steps": 5000},   # no bounce back
        ]
        score = _compute_comeback_score(rows, 15000)
        assert score.attempts == 2
        assert score.successes == 1
        assert score.score == 50.0

    def test_no_misses_returns_none_score(self):
        rows = [{"date": date(2026, 1, 1), "steps": 16000},
                {"date": date(2026, 1, 2), "steps": 16000}]
        score = _compute_comeback_score(rows, 15000)
        assert score.attempts == 0
        assert score.score is None


class TestDetailedStatsCache:
    @pytest.mark.asyncio
    async def test_write_and_rollback_failures_are_non_fatal(self):
        db = AsyncMock()
        db.execute.side_effect = RuntimeError("cache unavailable")
        db.rollback.side_effect = RuntimeError("connection unavailable")

        await _set_cached_detailed_stats(db, 2026, "hash", {"year": 2026})

        db.rollback.assert_awaited_once()


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

        # 1. data hash fingerprint (current year GROUP_CONCAT)
        add_scalar("2026-01-01:10000|2026-01-02:20000")
        # 2. previous year fingerprint
        add_first((0, 0, 0))
        # 3. all-time fingerprint
        add_first((30000, 2, 20000))
        # 4. cache lookup miss
        add_scalar(None)
        # 5. current year daily steps
        add_all([
            (date(2026, 1, 1), 10000),
            (date(2026, 1, 2), 20000),
        ])
        # 6. previous year daily steps
        add_all([])
        # 7. all daily steps (for milestone timeline)
        add_all([
            (date(2026, 1, 1), 10000),
            (date(2026, 1, 2), 20000),
        ])
        # 8. year aggregates
        add_first((30000, 2, 15000, 20000, date(2026, 1, 2), 1))
        # 9. top days
        add_all([
            (date(2026, 1, 2), 20000),
            (date(2026, 1, 1), 10000),
        ])
        # 10. top weeks
        add_all([
            (2026, 1, 30000, 2),
        ])
        # 11. top months
        add_all([
            (2026, 1, 30000, 2),
        ])
        # 12. cache insert
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
