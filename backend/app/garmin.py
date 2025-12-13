import logging
import os
from datetime import date, timedelta
from pathlib import Path

import garth
from garminconnect import Garmin
from app.config import get_settings

logger = logging.getLogger(__name__)

METERS_TO_MILES = 0.000621371
TOKENS_PATH = Path("/app/garth_tokens")


class GarminClient:
    def __init__(self):
        self.settings = get_settings()
        self.client = None

    async def connect(self):
        """Authenticate with Garmin Connect using saved tokens."""
        try:
            # Try to load saved tokens first
            if TOKENS_PATH.exists():
                logger.info("Loading saved Garmin tokens...")
                garth.resume(str(TOKENS_PATH))

                # Create Garmin client with the authenticated garth session
                self.client = Garmin()
                self.client.garth = garth.client
                logger.info("Successfully connected to Garmin Connect using saved tokens")
            else:
                # Fall back to password login (will fail if MFA required)
                logger.info("No saved tokens, attempting password login...")
                self.client = Garmin(
                    self.settings.garmin_email,
                    self.settings.garmin_password
                )
                self.client.login()
                logger.info("Successfully connected to Garmin Connect")
        except Exception as e:
            logger.error(f"Failed to connect to Garmin: {e}")
            raise

    def get_activities(
        self,
        start_date: date,
        end_date: date,
        activity_type: str = "walking"
    ) -> list[dict]:
        """
        Fetch walking activities from Garmin Connect.
        Returns list of activity data dicts.
        """
        if not self.client:
            raise RuntimeError("Not connected to Garmin. Call connect() first.")

        activities = []
        try:
            # Get activities (Garmin returns most recent first)
            raw_activities = self.client.get_activities_by_date(
                start_date.isoformat(),
                end_date.isoformat(),
                activity_type
            )

            for act in raw_activities:
                # Convert distance from meters to miles
                distance_meters = act.get("distance", 0) or 0
                distance_miles = distance_meters * METERS_TO_MILES

                # Extract speed (convert m/s to mph if available)
                avg_speed = act.get("averageSpeed")
                if avg_speed:
                    avg_speed_mph = avg_speed * 2.23694  # m/s to mph
                else:
                    avg_speed_mph = None

                activities.append({
                    "garmin_activity_id": act["activityId"],
                    "activity_date": date.fromisoformat(act["startTimeLocal"][:10]),
                    "activity_name": act.get("activityName", "Walking"),
                    "distance_miles": round(distance_miles, 2),
                    "duration_seconds": int(act.get("duration", 0)),
                    "start_lat": act.get("startLatitude"),
                    "start_lon": act.get("startLongitude"),
                    "end_lat": act.get("endLatitude"),
                    "end_lon": act.get("endLongitude"),
                    "average_speed_mph": round(avg_speed_mph, 2) if avg_speed_mph else None,
                    "calories": act.get("calories"),
                })

        except Exception as e:
            logger.error(f"Error fetching activities: {e}")
            raise

        return activities

    def get_steps(self, start_date: date, end_date: date) -> list[dict]:
        """
        Fetch daily step data from Garmin Connect.
        Returns list of daily step data dicts.
        """
        if not self.client:
            raise RuntimeError("Not connected to Garmin. Call connect() first.")

        steps_data = []
        current_date = start_date

        while current_date <= end_date:
            try:
                daily_stats = self.client.get_stats(current_date.isoformat())

                if daily_stats:
                    total_steps = daily_stats.get("totalSteps", 0) or 0
                    step_goal = daily_stats.get("dailyStepGoal", 10000) or 10000
                    distance = daily_stats.get("totalDistanceMeters", 0) or 0
                    floors = daily_stats.get("floorsAscended", 0) or 0

                    steps_data.append({
                        "step_date": current_date,
                        "steps": total_steps,
                        "goal": step_goal,
                        "distance_miles": round(distance * METERS_TO_MILES, 2),
                        "floors_climbed": floors,
                    })

            except Exception as e:
                logger.warning(f"Error fetching steps for {current_date}: {e}")

            current_date += timedelta(days=1)

        return steps_data


def get_garmin_client() -> GarminClient:
    return GarminClient()
