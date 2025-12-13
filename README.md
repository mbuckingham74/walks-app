# Walks Tracker

A personal dashboard to visualize walking progress as a journey across the United States via I-90 from Seattle to Boston.

## Features

- Pull walking activities and daily step data from Garmin Connect
- Interactive map showing progress along I-90 (2,850 miles)
- Daily steps chart with goal tracking
- Statistics dashboard with total distance, walks, and crossings

## Tech Stack

- **Frontend**: React 18 + Vite + Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **Database**: MySQL 8
- **Mapping**: Leaflet + React-Leaflet
- **Charts**: Recharts
- **Deployment**: Docker Compose

## Setup

### 1. Clone and Configure

```bash
git clone https://github.com/mbuckingham74/walks-app.git
cd walks-app
cp .env.example .env
# Edit .env with your credentials
```

### 2. Initialize Database

```bash
mysql -u root -p < backend/schema.sql
```

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

### 4. Production Deployment

```bash
cd docker
docker-compose up -d --build
```

## Environment Variables

See `.env.example` for required configuration.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sync` | Trigger full sync from Garmin |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/steps` | Daily steps data |
| GET | `/api/activities` | Walking activities list |
| GET | `/api/route` | I-90 waypoints |

## License

MIT
