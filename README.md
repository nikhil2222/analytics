# Real-Time Analytics & Reporting Platform

A lightweight multi-tenant analytics platform inspired by Mixpanel/Metabase. It supports event ingestion from API, CSV, and webhooks, dashboard widgets, threshold-based alerts, live updates via WebSockets, public dashboard sharing, scheduled reports, and background processing with Celery.

## Features

### Authentication & Multi-Tenancy
- Email/password authentication
- JWT access + refresh token flow
- Invite-based onboarding
- Organization-level data isolation
- Role-based access control: Owner, Admin, Analyst, Viewer

### Event Ingestion
- Single event ingestion
- Batch event ingestion
- CSV upload ingestion
- Webhook-based event ingestion
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
- Public dashboard sharing via slug-based public link
- Disable public sharing
- Full-screen dashboard presentation mode

### Alerts
- Threshold-based alerts
- In-app notification path
- Webhook notification support
- Scheduled evaluation via Celery Beat
- Alert history and status tracking
- Manual alert evaluation
- Mute and unmute support

### Reports
- Create reports from dashboards
- Manual and scheduled report execution
- Frequencies: manual, daily, weekly, monthly
- PNG snapshot generation for dashboards
- Report run history
- Download generated reports
- Email delivery via SMTP

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
- Playwright

## Architecture

The backend follows a layered architecture:

- **Routers**: API endpoints and request wiring
- **Services**: business logic
- **Repositories**: database access
- **Models**: SQLAlchemy ORM models
- **Schemas**: Pydantic request/response validation

Background tasks are handled by Celery workers, while Celery Beat runs scheduled jobs for alert evaluation, report execution, and event cleanup. Redis is used as both broker and queue infrastructure.

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
│   ├── src/
│   ├── components/
│   └── lib/
└── README.md
```

## Setup

### 1. Clone repository
```bash
git clone <your-repo-url>
cd analytics-platform
```

### 2. Backend setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install playwright psycopg2-binary
playwright install chromium
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://analytics:analytics123@localhost:5432/analyticsdb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_FROM=your_email@gmail.com
FRONTEND_URL=http://localhost:3000
```

Run migrations:
```bash
alembic upgrade head
```

Start backend:
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Start Celery worker
```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

### 4. Start Celery Beat
```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

### 5. Frontend setup
```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=http://localhost:8000
```

Start frontend:
```bash
npm run dev
```

Frontend: `http://localhost:3000`  
Backend docs: `http://localhost:8000/docs`

## Deployment

### Frontend
- Deployed on **Vercel**

### Backend
- Deployed on **Render**

## Smoke Test

1. Register a user and create an organization
2. Create an API key
3. Ingest events via API, CSV, or webhook
4. Create a dashboard and add widgets
5. Enable public dashboard sharing and open the public link
6. Create an alert on an event name
7. Wait for Celery Beat to evaluate alerts
8. Create a report and run it manually
9. Confirm dashboard widgets refresh in real time

## Completed

- JWT auth with refresh token flow
- Multi-tenant org isolation
- Role-based access control
- Invite-based onboarding
- API key management
- Event ingestion: single, batch, CSV, webhook
- Dashboard widgets
- Public dashboard sharing
- Full-screen dashboard presentation mode
- WebSocket live event updates
- Celery worker + beat integration
- Threshold alert evaluation
- Alert mute/unmute and manual evaluation
- Scheduled reports
- PNG report generation
- Report email delivery via SMTP
- Rate limiting
- Frontend deployed on Vercel
- Backend deployed on Render

## Partial / Future Work

- OAuth/social login
- PDF report generation
- Advanced dashboard layout editing
- More alert delivery channels
- External file storage for report exports
- Production monitoring and observability improvements

## Notes

This project prioritizes the assignment’s must-have modules and production-oriented architecture: async processing, layered design, validation, background jobs, scheduled workflows, public sharing, and real-time updates.