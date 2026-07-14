export const TOTAL_ROUTE_DISTANCE = 2850;

export function interpolateRoutePosition(totalMiles, waypoints, totalDistance = TOTAL_ROUTE_DISTANCE) {
  if (!waypoints || waypoints.length === 0) return null;
  let effectiveMiles = totalMiles % totalDistance;
  if (totalMiles > 0 && effectiveMiles === 0) {
    effectiveMiles = totalDistance;
  }
  let current = waypoints[0];
  let next = null;
  for (let i = 0; i < waypoints.length; i++) {
    if (effectiveMiles >= waypoints[i].miles_from_start) {
      current = waypoints[i];
      if (i < waypoints.length - 1) next = waypoints[i + 1];
    } else {
      break;
    }
  }
  let lat;
  let lon;
  if (next) {
    const segLen = next.miles_from_start - current.miles_from_start;
    const ratio = segLen > 0 ? (effectiveMiles - current.miles_from_start) / segLen : 0;
    lat = current.lat + (next.lat - current.lat) * ratio;
    lon = current.lon + (next.lon - current.lon) * ratio;
  } else {
    lat = current.lat;
    lon = current.lon;
  }
  return { lat, lon, effectiveMiles };
}
