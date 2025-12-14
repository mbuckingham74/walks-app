from dataclasses import dataclass
from math import sqrt


@dataclass
class Waypoint:
    index: int
    city: str
    miles_from_start: int
    lat: float
    lon: float


# I-90 route from Seattle to Boston with intermediate waypoints
ROUTE_WAYPOINTS = [
    Waypoint(0, "Seattle, WA", 0, 47.6080, -122.3375),
    Waypoint(1, "Ellensburg, WA", 107, 46.9965, -120.5478),
    Waypoint(2, "Spokane, WA", 280, 47.6588, -117.4260),
    Waypoint(3, "Coeur d'Alene, ID", 312, 47.6777, -116.7805),
    Waypoint(4, "Missoula, MT", 473, 46.8721, -113.9940),
    Waypoint(5, "Butte, MT", 593, 46.0038, -112.5348),
    Waypoint(6, "Bozeman, MT", 665, 45.6770, -111.0429),
    Waypoint(7, "Billings, MT", 740, 45.7833, -108.5007),
    Waypoint(8, "Sheridan, WY", 870, 44.7972, -106.9561),
    Waypoint(9, "Gillette, WY", 950, 44.2911, -105.5022),
    Waypoint(10, "Rapid City, SD", 1040, 44.0805, -103.2310),
    Waypoint(11, "Wall, SD", 1095, 43.9925, -102.2413),
    Waypoint(12, "Chamberlain, SD", 1215, 43.8108, -99.3307),
    Waypoint(13, "Mitchell, SD", 1290, 43.7094, -98.0298),
    Waypoint(14, "Sioux Falls, SD", 1390, 43.5460, -96.7313),
    Waypoint(15, "Worthington, MN", 1450, 43.6199, -95.5964),
    Waypoint(16, "Albert Lea, MN", 1530, 43.6480, -93.3683),
    Waypoint(17, "Rochester, MN", 1590, 44.0121, -92.4802),
    Waypoint(18, "La Crosse, WI", 1650, 43.8014, -91.2396),
    Waypoint(19, "Madison, WI", 1700, 43.0731, -89.4012),
    Waypoint(20, "Rockford, IL", 1770, 42.2711, -89.0940),
    Waypoint(21, "Chicago, IL", 1850, 41.8781, -87.6298),
    Waypoint(22, "Gary, IN", 1880, 41.5934, -87.3465),
    Waypoint(23, "South Bend, IN", 1970, 41.6764, -86.2520),
    Waypoint(24, "Toledo, OH", 2090, 41.6528, -83.5379),
    Waypoint(25, "Cleveland, OH", 2190, 41.4993, -81.6944),
    Waypoint(26, "Erie, PA", 2290, 42.1292, -80.0851),
    Waypoint(27, "Buffalo, NY", 2380, 42.8864, -78.8784),
    Waypoint(28, "Rochester, NY", 2450, 43.1566, -77.6088),
    Waypoint(29, "Syracuse, NY", 2530, 43.0481, -76.1474),
    Waypoint(30, "Utica, NY", 2585, 43.1009, -75.2327),
    Waypoint(31, "Albany, NY", 2660, 42.6526, -73.7562),
    Waypoint(32, "Springfield, MA", 2750, 42.1015, -72.5898),
    Waypoint(33, "Boston, MA", 2850, 42.3601, -71.0589),
]

TOTAL_ROUTE_DISTANCE = 2850  # miles


def get_route_waypoints() -> list[Waypoint]:
    return ROUTE_WAYPOINTS


def calculate_position(total_miles: float) -> dict:
    """
    Calculate current position on the route given total miles walked.
    Returns position info including lat/lon, current waypoint, and distance to next.
    """
    # Handle multiple crossings
    effective_miles = total_miles % TOTAL_ROUTE_DISTANCE
    crossings = int(total_miles // TOTAL_ROUTE_DISTANCE)

    # Find current segment
    current_wp = ROUTE_WAYPOINTS[0]
    next_wp = None

    for i, wp in enumerate(ROUTE_WAYPOINTS):
        if effective_miles >= wp.miles_from_start:
            current_wp = wp
            if i < len(ROUTE_WAYPOINTS) - 1:
                next_wp = ROUTE_WAYPOINTS[i + 1]
        else:
            break

    # Interpolate position between waypoints
    if next_wp:
        segment_start = current_wp.miles_from_start
        segment_end = next_wp.miles_from_start
        segment_length = segment_end - segment_start
        progress_in_segment = effective_miles - segment_start
        segment_ratio = progress_in_segment / segment_length if segment_length > 0 else 0

        # Linear interpolation
        lat = current_wp.lat + (next_wp.lat - current_wp.lat) * segment_ratio
        lon = current_wp.lon + (next_wp.lon - current_wp.lon) * segment_ratio
        miles_to_next = segment_end - effective_miles
    else:
        # At or past Boston
        lat = current_wp.lat
        lon = current_wp.lon
        miles_to_next = 0

    return {
        "lat": lat,
        "lon": lon,
        "miles_traveled": total_miles,
        "effective_miles": effective_miles,
        "crossings_completed": crossings,
        "current_waypoint": {
            "index": current_wp.index,
            "city": current_wp.city,
            "miles_from_start": current_wp.miles_from_start,
            "lat": current_wp.lat,
            "lon": current_wp.lon,
        },
        "next_waypoint": {
            "index": next_wp.index,
            "city": next_wp.city,
            "miles_from_start": next_wp.miles_from_start,
            "lat": next_wp.lat,
            "lon": next_wp.lon,
        } if next_wp else None,
        "miles_to_next": miles_to_next,
        "percent_complete": (effective_miles / TOTAL_ROUTE_DISTANCE) * 100,
    }
