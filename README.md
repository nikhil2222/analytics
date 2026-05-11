# Real-Time Analytics & Reporting Platform

A lightweight multi-tenant analytics platform inspired by Mixpanel/Metabase. It supports event ingestion from API and CSV, dashboard widgets, threshold-based alerts, live updates via WebSockets, and background processing with Celery.

## Features

### Authentication & Multi-Tenancy
- Email/password authentication
- JWT access + refresh token flow
- Organization-level data isolation
- Role-based access control: Owner, Admin, Analyst, Viewer

### Event Ingestion
- Single event ingestion
- Batch event ingestion
- CSV upload ingestion
- API key management per organization
- Pydantic validation for request payloads
- Background post-processing via Celery
- Rate limiting on ingest endpoints

### Dashboards
- Custom dashboards
- Widget types: KPI, line, bar, pie, table
- Configurable time ranges
- Auto-refresh support
- Live updates with WebSockets

### Alerts
- Threshold-based alerts
- In-app notification path
- Webhook notification support
- Scheduled evaluation via Celery Beat
- Alert history and status tracking

## Tech Stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- Axios / React Query
- Recharts

### Backend
- FastAPI
- SQLAlchemy Async
- Alembic
- PostgreSQL
- Redis
- Celery
- WebSockets

## Architecture

The backend follows a layered architecture:

- **Routers**: API endpoints and request wiring
- **Services**: business logic
- **Repositories**: database access
- **Models**: SQLAlchemy ORM models
- **Schemas**: Pydantic request/response validation

Background tasks are handled by Celery workers, while Celery Beat runs scheduled alert evaluation jobs. Redis is used as both broker and caching/queue infrastructure.

## Project Structure

```bash
analytics-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── tasks/
│   ├── alembic/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
└── docker-compose.yml
```

## Setup

### 1. Clone repository
```bash
git clone <your-repo-url>
cd analytics-platform
```

### 2. Start PostgreSQL and Redis
```bash
docker compose up db redis -d
```

### 3. Backend setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://analytics:analytics123@localhost:5432/analyticsdb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Run migrations:
```bash
alembic upgrade head
```

Start backend:
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Start Celery worker
```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

### 5. Start Celery Beat
```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app beat --loglevel=info
```

### 6. Frontend setup
```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1
```

Start frontend:
```bash
npm run dev
```

Frontend: `http://localhost:3000`  
Backend docs: `http://localhost:8000/docs`

## Smoke Test

1. Register a user and create an organization
2. Create an API key
3. Ingest events via API or CSV
4. Create an alert on an event name
5. Wait 60 seconds for Celery Beat to evaluate alerts
6. Confirm the alert status updates automatically

## Completed

- JWT auth with refresh token flow
- Multi-tenant org isolation
- Role-based access control
- API key management
- Event ingestion: single, batch, CSV
- Dashboard widgets
- WebSocket live event updates
- Celery worker + beat integration
- Threshold alert evaluation
- Rate limiting

## Partial / Future Work

- Invite flow polish
- Public dashboard sharing
- Email delivery integration
- Scheduled PDF/PNG report generation
- Production deployment hardening

## Notes

This project prioritizes the assignment’s must-have modules and production-oriented architecture: async processing, layered design, validation, background jobs, and real-time updates.
