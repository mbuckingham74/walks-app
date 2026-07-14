from unittest.mock import AsyncMock, MagicMock
from datetime import date

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestRouteEndpoint:
    def test_route_returns_waypoints(self, client):
        resp = client.get("/api/route")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_distance"] == 2850
        assert len(data["waypoints"]) == 34
        assert data["waypoints"][0]["city"] == "Seattle, WA"
        assert data["waypoints"][-1]["city"] == "Boston, MA"


class TestConfigEndpoint:
    def test_config_returns_constants(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "steps_per_mile" in data
        assert "daily_goal" in data
        assert data["steps_per_mile"] == 1850
        assert data["daily_goal"] == 15000


class TestGoalPaceProjection:
    def test_counts_start_date_as_first_walking_day_and_rounds_up(self):
        from app.main import _compute_goal_pace_projection

        days, finish_date = _compute_goal_pace_projection(
            date(2026, 1, 1), daily_goal=15000, steps_per_mile=1850
        )

        assert days == 352
        assert finish_date == "2026-12-18"

    def test_returns_none_without_a_start_date(self):
        from app.main import _compute_goal_pace_projection

        assert _compute_goal_pace_projection(None, 15000, 1850) == (None, None)


class TestActivitiesEndpoint:
    def test_activities_without_api_key_returns_401(self, client):
        resp = client.get("/api/activities")
        assert resp.status_code == 401

    def test_activities_with_wrong_key_returns_401(self, client):
        resp = client.get("/api/activities", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401

    def test_activities_with_correct_key_returns_200(self, client):
        from app.main import app, get_db

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        async def override():
            yield mock_session

        app.dependency_overrides[get_db] = override
        try:
            resp = client.get("/api/activities", headers={"X-API-Key": "test-api-key"})
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            app.dependency_overrides.clear()
            async def restore():
                yield AsyncMock()
            app.dependency_overrides[get_db] = restore


class TestPostStepsEndpoint:
    def test_post_steps_without_secret_returns_401(self, client):
        resp = client.post("/api/steps", json={"date": "2026-01-01", "steps": 10000})
        assert resp.status_code == 401

    def test_post_steps_with_wrong_secret_returns_401(self, client):
        resp = client.post(
            "/api/steps",
            json={"date": "2026-01-01", "steps": 10000},
            headers={"X-Shortcut-Secret": "wrong"},
        )
        assert resp.status_code == 401

    def test_post_steps_invalid_date_returns_422(self, client):
        resp = client.post(
            "/api/steps",
            json={"date": "1990-01-01", "steps": 10000},
            headers={"X-Shortcut-Secret": "test-shortcut-secret"},
        )
        assert resp.status_code == 422

    def test_post_steps_with_valid_data_returns_200(self, client):
        resp = client.post(
            "/api/steps",
            json={"date": "2026-01-01", "steps": 17000},
            headers={"X-Shortcut-Secret": "test-shortcut-secret"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["date"] == "2026-01-01"
        assert data["steps"] == 17000


class TestLogStepsGetEndpoint:
    def test_log_steps_get_without_secret_returns_401(self, client):
        resp = client.get("/api/log-steps?date=2026-01-01&steps=17000")
        assert resp.status_code == 401

    def test_log_steps_get_with_wrong_secret_returns_401(self, client):
        resp = client.get("/api/log-steps?date=2026-01-01&steps=17000&secret=wrong")
        assert resp.status_code == 401

    def test_log_steps_get_with_valid_data_returns_200(self, client):
        resp = client.get(
            "/api/log-steps?date=2026-01-01&steps=17000&secret=test-shortcut-secret"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["date"] == "2026-01-01"
        assert data["steps"] == 17000

    def test_log_steps_get_invalid_date_returns_422(self, client):
        resp = client.get(
            "/api/log-steps?date=not-a-date&steps=17000&secret=test-shortcut-secret"
        )
        assert resp.status_code == 422

    def test_log_steps_get_steps_out_of_bounds_returns_422(self, client):
        resp = client.get(
            "/api/log-steps?date=2026-01-01&steps=999999&secret=test-shortcut-secret"
        )
        assert resp.status_code == 422
