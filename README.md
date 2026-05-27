# Breathe ESG — Ingestion + Review Prototype (Django + React)

Prototype that ingests three realistic source types (SAP export, utility portal export, corporate travel export), normalizes into a canonical table, and provides an analyst review UI to approve rows and lock a job for audit.

## Local run (fast)

### Backend

```powershell
cd backend
../.venv/Scripts/python.exe manage.py migrate
../.venv/Scripts/python.exe manage.py seed_demo
../.venv/Scripts/python.exe manage.py runserver 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Login (seeded): `admin` / `demo1234`

Sample CSVs live in `sample_data/`.

## Local run (Docker)

```powershell
docker compose up --build
```

Frontend: http://localhost:5173
Backend: http://localhost:8000

## Deploy (Render)

This repo includes a Render Blueprint in `render.yaml`.

1. Push this repo to GitHub.
2. In Render: **New** → **Blueprint** → select the repo.
3. Create the services + database.
4. After first deploy, open the backend shell (or use the service “Shell” tab) and run:

```bash
python manage.py migrate
python manage.py seed_demo
```

### Required env vars (Render)

Backend service (`breatheesg-backend`):
- `DJANGO_SECRET_KEY` (Render generates this via blueprint)
- `DJANGO_DEBUG=0`
- `DJANGO_ALLOWED_HOSTS=.onrender.com`
- `DATABASE_URL` (wired to the Render Postgres)

Frontend service (`breatheesg-frontend`):
- `API_UPSTREAM=https://breatheesg-backend.onrender.com`

The frontend container reverse-proxies `/api/*` and `/media/*` to `API_UPSTREAM`, so the React app can keep using relative `/api/...` calls.

## Key URLs

- JWT token: `POST /api/auth/token/`
- My orgs: `GET /api/orgs/`
- Upload ingest: `POST /api/orgs/{org_slug}/ingest/upload/` (multipart: `source_type`, `file`)
- Jobs: `GET /api/orgs/{org_slug}/jobs/`

## Docs for the assignment

- `MODEL.md`
- `DECISIONS.md`
- `TRADEOFFS.md`
- `SOURCES.md`
