# Steps Tracker

A personal dashboard to visualize steps and walking progress as a virtual journey across the United States via I-90 from Seattle to Boston (2,850 miles).

![Light Mode](https://img.shields.io/badge/theme-light-lightgrey) ![Dark Mode](https://img.shields.io/badge/theme-dark-darkblue)

## Features

- **Virtual Cross-Country Journey**: Track your real-world steps as progress along I-90
- **Interactive Map**: Leaflet-powered map showing your current position and route waypoints
- **Daily Steps Chart**: Visualize step counts with goal tracking and date range filters
- **Statistics Dashboard**: Total distance, steps, days tracked, and crossing count
- **Dark Mode**: System-aware theme with manual toggle
- **iOS Shortcut Integration**: Push daily steps from Apple Health via iOS Shortcuts

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI (Python 3.11+) |
| Database | MySQL 8 |
| Mapping | Leaflet + React-Leaflet |
| Charts | Recharts |
| Deployment | Docker Compose |

## Data Flow

```
Apple Health → iOS Shortcut → POST /api/steps → MySQL → Dashboard
```

Steps are converted to miles at a rate of **2,000 steps = 1 mile**.

## Setup

### 1. Clone and Configure

```bash
git clone https://github.com/mbuckingham74/walks-app.git
cd walks-app
cp .env.example .env
# Edit .env with your credentials
```

### 2. Production Deployment

```bash
cd docker
docker compose up -d --build
```

The frontend runs on port 3080 by default. Configure your reverse proxy (nginx, Traefik, etc.) to route traffic.

### 3. Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MYSQL_HOST` | Database hostname |
| `MYSQL_PORT` | Database port (default: 3306) |
| `MYSQL_USER` | Database user |
| `MYSQL_PASSWORD` | Database password |
| `MYSQL_DATABASE` | Database name |
| `MYSQL_ROOT_PASSWORD` | Root password for initial setup |
| `CORS_ORIGINS` | Allowed origins for API |

See `.env.example` for a complete template.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/steps` | Upsert daily steps (for iOS Shortcut) |
| `GET` | `/api/stats` | Dashboard statistics for a year |
| `GET` | `/api/steps` | Daily steps data with date range |
| `GET` | `/api/route` | I-90 waypoints for map rendering |
| `GET` | `/api/health` | Health check |

### iOS Shortcut Integration

Create an iOS Shortcut that:
1. Gets today's step count from Health
2. Sends a POST request to your API:

```
POST https://your-domain.com/api/steps
Content-Type: application/json

{
  "date": "2025-12-13",
  "steps": 8500
}
```

Run the shortcut daily (manually or via automation) to sync your steps.

## Route Waypoints

The I-90 route includes major cities:
- Seattle, WA (start)
- Spokane, WA
- Missoula, MT
- Butte, MT
- Billings, MT
- Rapid City, SD
- Sioux Falls, SD
- Albert Lea, MN
- Madison, WI
- Chicago, IL
- Toledo, OH
- Cleveland, OH
- Erie, PA
- Buffalo, NY
- Syracuse, NY
- Albany, NY
- Boston, MA (finish)

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  walks-frontend │────▶│    walks-api    │────▶│   walks-mysql   │
│   (React/Nginx) │     │    (FastAPI)    │     │    (MySQL 8)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │
         ▼
   npm_network (nginx proxy manager)
```

## License

MIT
