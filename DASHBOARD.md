# Steps Tracker Dashboard

A web dashboard that tracks daily steps and visualizes progress along the I-90 route from Seattle to Boston (2,850 miles).

## Stats Cards

The top section displays 8 stat tiles:

| Stat | Description |
|------|-------------|
| **Total Distance** | Cumulative miles walked (steps ÷ 2000) |
| **Total Steps** | Sum of all recorded daily steps |
| **Daily Average** | Average steps per day across all tracked days |
| **Current Streak** | Consecutive days meeting the 10,000 step goal |
| **Best Day** | Highest single-day step count with date |
| **Goals Met** | Number of days reaching 10,000+ steps (with percentage) |
| **Progress** | Percentage of the Seattle-to-Boston route completed |
| **ETA Boston** | Projected arrival date based on current pace |

## Route Progress Map

An interactive Leaflet map showing:
- **Green marker**: Starting point (Seattle)
- **Red marker**: Destination (Boston)
- **Blue markers**: Waypoints along I-90 (Spokane, Missoula, Billings, etc.)
- **Green line**: Completed portion of the route
- **Gray line**: Remaining portion of the route

## Current Progress Panel

- Progress bar showing percentage complete
- Current location (nearest city)
- Next waypoint with distance remaining

## This Week vs Last Week

- Percentage change in steps compared to the previous week
- Green/red indicator for improvement/decline
- Step counts for both weeks

## Year Statistics

- Miles remaining to Boston
- Total days tracked
- Number of complete America crossings (if applicable)

## Daily Steps Chart

An area chart with time range filters:
- **Week**: Last 7 days
- **Month**: Last 30 days (default)
- **Year**: Current year
- **All**: All recorded data

The chart displays:
- Daily step counts as a filled area
- 10,000 step goal as a dashed reference line
- Tooltips with exact values on hover

## Data Source

Steps are synced from Apple Health via an iOS Shortcut that posts to the `/api/steps` endpoint.
