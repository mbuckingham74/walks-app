import { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';

// Custom marker icons
const createIcon = (color, size = 12) => L.divIcon({
  className: 'custom-marker',
  html: `<div style="
    width: ${size}px;
    height: ${size}px;
    background: ${color};
    border: 2px solid white;
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
  "></div>`,
  iconSize: [size, size],
  iconAnchor: [size / 2, size / 2],
});

const createCurrentIcon = () => L.divIcon({
  className: 'current-marker pulse-marker',
  html: `<div style="
    width: 20px;
    height: 20px;
    background: #16a34a;
    border: 3px solid white;
    border-radius: 50%;
    box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.3), 0 2px 8px rgba(0,0,0,0.3);
  "></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

const waypointIcon = createIcon('#3b82f6', 10);
const startIcon = createIcon('#22c55e', 14);
const endIcon = createIcon('#ef4444', 14);
const currentIcon = createCurrentIcon();

function MapBounds({ waypoints, currentPosition }) {
  const map = useMap();

  useEffect(() => {
    if (waypoints && waypoints.length > 0) {
      const bounds = waypoints.map(wp => [wp.lat, wp.lon]);
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [map, waypoints]);

  return null;
}

export function RouteMap({ route, currentPosition }) {
  const waypoints = route?.waypoints || [];

  const routeCoords = useMemo(() =>
    waypoints.map(wp => [wp.lat, wp.lon]),
    [waypoints]
  );

  // Split route into completed and remaining segments
  const { completedCoords, remainingCoords } = useMemo(() => {
    if (!currentPosition || waypoints.length === 0) {
      return { completedCoords: [], remainingCoords: routeCoords };
    }

    const currentLat = currentPosition.lat;
    const currentLon = currentPosition.lon;
    const currentWaypointIndex = currentPosition.current_waypoint?.index || 0;

    // Completed: from start to current position
    const completed = [
      ...routeCoords.slice(0, currentWaypointIndex + 1),
      [currentLat, currentLon]
    ];

    // Remaining: from current position to end
    const remaining = [
      [currentLat, currentLon],
      ...routeCoords.slice(currentWaypointIndex + 1)
    ];

    return { completedCoords: completed, remainingCoords: remaining };
  }, [routeCoords, currentPosition, waypoints]);

  if (waypoints.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-100 rounded-xl">
        <p className="text-gray-500">Loading map...</p>
      </div>
    );
  }

  const center = [42.5, -96]; // Center of US

  return (
    <MapContainer
      center={center}
      zoom={4}
      scrollWheelZoom={true}
      className="h-full w-full rounded-xl"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <MapBounds waypoints={waypoints} currentPosition={currentPosition} />

      {/* Completed route segment (green) */}
      {completedCoords.length > 1 && (
        <Polyline
          positions={completedCoords}
          color="#16a34a"
          weight={4}
          opacity={0.9}
        />
      )}

      {/* Remaining route segment (gray) */}
      {remainingCoords.length > 1 && (
        <Polyline
          positions={remainingCoords}
          color="#9ca3af"
          weight={3}
          opacity={0.6}
          dashArray="8, 8"
        />
      )}

      {/* Waypoint markers */}
      {waypoints.map((wp, idx) => {
        let icon = waypointIcon;
        if (idx === 0) icon = startIcon;
        else if (idx === waypoints.length - 1) icon = endIcon;

        return (
          <Marker key={wp.index} position={[wp.lat, wp.lon]} icon={icon}>
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{wp.city}</p>
                <p className="text-gray-600">{wp.miles_from_start} miles from Seattle</p>
              </div>
            </Popup>
          </Marker>
        );
      })}

      {/* Current position marker */}
      {currentPosition && (
        <Marker
          position={[currentPosition.lat, currentPosition.lon]}
          icon={currentIcon}
        >
          <Popup>
            <div className="text-sm">
              <p className="font-semibold">You are here!</p>
              <p className="text-gray-600">
                {currentPosition.effective_miles?.toFixed(1) || currentPosition.miles_traveled?.toFixed(1)} miles traveled
              </p>
              {currentPosition.next_waypoint && (
                <p className="text-gray-600">
                  {currentPosition.miles_to_next?.toFixed(1)} mi to {currentPosition.next_waypoint.city}
                </p>
              )}
            </div>
          </Popup>
        </Marker>
      )}
    </MapContainer>
  );
}
