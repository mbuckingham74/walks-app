import { describe, expect, it } from 'vitest';
import { interpolateRoutePosition } from './route';

const waypoints = [
  { lat: 0, lon: 0, miles_from_start: 0 },
  { lat: 10, lon: 20, miles_from_start: 100 },
];

describe('interpolateRoutePosition', () => {
  it('returns the mileage property consumed by the goal-pace marker', () => {
    expect(interpolateRoutePosition(50, waypoints, 100)).toEqual({
      lat: 5,
      lon: 10,
      effectiveMiles: 50,
    });
  });

  it('keeps exact completed routes at the final waypoint', () => {
    expect(interpolateRoutePosition(100, waypoints, 100)).toMatchObject({
      lat: 10,
      lon: 20,
      effectiveMiles: 100,
    });
  });
});
