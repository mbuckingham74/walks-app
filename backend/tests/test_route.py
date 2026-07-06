from app.route import (
    calculate_position,
    get_route_waypoints,
    TOTAL_ROUTE_DISTANCE,
    ROUTE_WAYPOINTS,
)


class TestGetRouteWaypoints:
    def test_returns_all_waypoints(self):
        waypoints = get_route_waypoints()
        assert len(waypoints) == 34

    def test_first_waypoint_is_seattle(self):
        waypoints = get_route_waypoints()
        assert waypoints[0].city == "Seattle, WA"
        assert waypoints[0].miles_from_start == 0

    def test_last_waypoint_is_boston(self):
        waypoints = get_route_waypoints()
        assert waypoints[-1].city == "Boston, MA"
        assert waypoints[-1].miles_from_start == 2850

    def test_total_distance_constant(self):
        assert TOTAL_ROUTE_DISTANCE == 2850


class TestCalculatePosition:
    def test_zero_miles_at_seattle(self):
        pos = calculate_position(0)
        assert pos["effective_miles"] == 0
        assert pos["crossings_completed"] == 0
        assert pos["current_waypoint"]["city"] == "Seattle, WA"
        assert pos["percent_complete"] == 0

    def test_at_first_intermediate_waypoint(self):
        pos = calculate_position(107)
        assert pos["current_waypoint"]["city"] == "Ellensburg, WA"
        assert pos["next_waypoint"]["city"] == "Spokane, WA"

    def test_mid_segment_interpolation(self):
        pos = calculate_position(50)
        assert pos["current_waypoint"]["city"] == "Seattle, WA"
        assert pos["next_waypoint"]["city"] == "Ellensburg, WA"
        assert 0 < pos["percent_complete"] < 100
        assert pos["miles_to_next"] == 107 - 50

    def test_at_boston(self):
        pos = calculate_position(TOTAL_ROUTE_DISTANCE)
        assert pos["effective_miles"] == TOTAL_ROUTE_DISTANCE
        assert pos["current_waypoint"]["city"] == "Boston, MA"
        assert pos["miles_to_next"] == 0
        assert pos["percent_complete"] == 100

    def test_exact_completion_not_reset_to_seattle(self):
        pos = calculate_position(TOTAL_ROUTE_DISTANCE)
        assert pos["current_waypoint"]["city"] == "Boston, MA"
        assert pos["current_waypoint"]["city"] != "Seattle, WA"

    def test_multiple_crossings(self):
        total = TOTAL_ROUTE_DISTANCE * 2 + 500
        pos = calculate_position(total)
        assert pos["crossings_completed"] == 2
        assert pos["effective_miles"] == 500

    def test_miles_traveled_preserved(self):
        pos = calculate_position(5000)
        assert pos["miles_traveled"] == 5000

    def test_position_at_chicago(self):
        pos = calculate_position(1850)
        assert pos["current_waypoint"]["city"] == "Chicago, IL"

    def test_lat_lon_within_reasonable_bounds(self):
        pos = calculate_position(1000)
        assert 24 < pos["lat"] < 50
        assert -125 < pos["lon"] < -67
