# RoutePulse

Campus transportation operations and recovery-optimization system.

- `frontend/` — React + TypeScript + Vite dashboard (Operations, Recovery
  Planner, Performance Lab).
- `backend/` — FastAPI service that serves live network data, scenarios, and a
  real optimization pipeline. See [`backend/README.md`](backend/README.md).

The frontend consumes the backend over HTTP; the mock-data modules under
`frontend/src/mocks/` are retained as fixtures/tests only and are no longer on
the active data path.

## Run locally

Start the backend first:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Then start the frontend (new terminal):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The frontend calls `http://localhost:8000` by
default; override with `frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Tests

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest
```

## Frontend checks

```bash
cd frontend
npm run lint
npm run build
```

## How the pieces connect

| Frontend consumer | Backend endpoint |
| --- | --- |
| Operations page + header notifications | `GET /api/operations/overview` |
| Recovery Planner scenario cards | `GET /api/scenarios` |
| Recovery Planner "Run Optimization" | `POST /api/optimize` |
| Performance Lab run/metric panels | `GET /api/evaluation`, `GET /api/evaluation/{run_id}` |
| Health | `GET /api/health` |
