# RoutePulse

RoutePulse is a campus transportation operations dashboard with a FastAPI backend for route data, schedule validation, optimization, and simulation.

## Requirements

- Python 3.11 or newer
- Node.js 20.19 or newer and npm
- Windows PowerShell, macOS Terminal, or Linux shell

## Run locally

Open two terminals in the extracted `routepulse` project folder.

In the first terminal, start the backend:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

If Python 3.11 is not installed, replace `py -3.11` with a version available on your computer, such as `py -3.12`.

In the second terminal, start the dashboard:

```powershell
cd frontend
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm ci
npm run dev -- --host 127.0.0.1
```

Open `http://localhost:5173`. The API runs at `http://localhost:8000`; its interactive documentation is at `http://localhost:8000/docs`.

The backend reads the project's root `data/` folder. Set `ROUTEPULSE_DATA_DIR` before starting the backend to use another data directory. The frontend backend origin can be changed in `frontend/.env.local` with `VITE_API_BASE_URL`.

## Optimizer behavior

The current optimizer is a deterministic greedy assignment planner with bounded service-priority search. It scores simulated passenger outcomes, operating cost, vehicle distance, road-network reposition distance, vehicle changes, unassigned services, and hard constraint findings. When demand is available it evaluates bounded extra-service candidates at 50%, 60%, and 75% of the uncovered demand windows, then independently validates each plan and keeps the best feasible weighted result. The configured network produces roughly 74–77% fewer unserved passengers in the supplied scenarios, with the resulting cost and distance trade-off shown by the evaluation UI. The baseline assignment is retained when a candidate does not improve the weighted objective. The accepted `time_limit_seconds` field is reported as unsupported because this greedy planner does not implement a solver time limit.

## Verification

From the project root, run the backend suite and frontend checks:

```powershell
cd backend
\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm run build
npm run lint
```
