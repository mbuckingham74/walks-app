# Walks Tracker

Personal dashboard tracking walking progress as a virtual journey across I-90 from Seattle to Boston.

## Deployment

**Deploy from local, not GitHub pull on server:**
```bash
./deploy.sh
```

**Server:** tachyon (ssh alias for michael@tachyonfuture.com)
**Path on server:** ~/walks-tracker/

`deploy.sh` handles rsync, `docker compose up -d --build --remove-orphans`, waits for health checks, and prunes old Docker builder/image layers after a successful deploy.

## Architecture

- **Frontend:** React 18 + Vite + Tailwind, served by nginx on port 3080
- **Backend:** FastAPI (Python 3.11), internal port 8000 (not exposed to host)
- **Database:** MySQL 8
- **Network:** Docker internal network, frontend proxies to `walks-api:8000`

## Key Files

- `backend/app/main.py` - API endpoints
- `backend/app/config.py` - Settings including business constants (steps_per_mile, daily_goal)
- `backend/app/route.py` - I-90 waypoints and position calculation
- `frontend/src/components/Dashboard.jsx` - Main dashboard
- `docker/docker-compose.yml` - Container orchestration

## Business Logic

- **Conversion:** 2000 steps = 1 mile (configurable via STEPS_PER_MILE env var)
- **Daily goal:** 15000 steps (configurable via DAILY_GOAL env var)
- **Route:** 2850 miles, 34 waypoints across 11 states
- **Data source:** iOS Shortcut posts to the public `POST /api/steps` endpoint

## API Authentication

- `GET /api/stats`, `GET /api/steps`, `GET /api/route`, and `POST /api/steps` are public
- `GET /api/activities` is optional and private when `API_KEY` is configured

## Common Tasks

**After changing frontend code:**
```bash
cd frontend && npm run build  # Build happens in Docker, but test locally first
```

**After changing package.json:**
```bash
cd frontend && npm install  # Regenerate package-lock.json before deploy
```

**Check logs on server:**
```bash
ssh tachyon "docker logs walks-api --tail 50"
ssh tachyon "docker logs walks-frontend --tail 50"
```

**Test API from inside Docker network:**
```bash
ssh tachyon "docker exec walks-frontend curl -s http://walks-api:8000/api/health"
```
