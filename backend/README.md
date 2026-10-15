# RoutePulse Backend

FastAPI service that powers the RoutePulse campus transportation dashboard. It
serves the live operations network, the selectable disruption scenarios, and a
real recovery-optimization pipeline (optimize → independent validate →
deterministic simulate → evaluate).

All plans, validation results and metrics are computed at request time. Nothing
is hardcoded or pre-claimed as an improvement.

## Prerequisites

- Python 3.11+ (tested on 3.11.9).
- The frontend (`../frontend`) runs separately on Vite's dev server.

## Setup

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# macOS/Linux
python -m pip install -r requirements.txt
```

## Start the backend

```bash
# from backend/
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

The app validates the seed network and pre-computes evaluation runs at startup,
so the Performance Lab has data immediately. Interactive docs: http://localhost:8000/docs

## Run the tests

```bash
.\.venv\Scripts\python.exe -m pytest
```

## Environment variables

Copy `.env.example` to `.env` and adjust as needed (uvicorn reads `.env` via the
`standard` extra's `--env-file` is not used; export variables in the shell or
rely on the defaults below):

| Variable | Default | Purpose |
| --- | --- | --- |
| `ROUTEPULSE_HOST` | `127.0.0.1` | Host to bind when starting uvicorn manually |
| `ROUTEPULSE_PORT` | `8000` | Port |
| `ROUTEPULSE_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed CORS origins |
| `ROUTEPULSE_AVG_SPEED_KMH` | `20.0` | Average speed used to derive travel times from coordinates |
| `ROUTEPULSE_SIM_SEED` | `42` | Fixed seed keeping simulation deterministic |

## API endpoints

Every data endpoint returns the envelope `{ success, message, data }`. Errors
return `{ success: false, message, error, detail? }`.

### `GET /api/health`

```json
{ "success": true, "status": "ok", "service": "routepulse-backend", "version": "1.0.0" }
```

### `GET /api/operations/overview`

Populated `data` with `routes`, `stops`, `vehicles`, `trips`, `demand`, `etas`,
`alerts` in the exact field names the frontend renders.

### `GET /api/scenarios`

`data` is an array of scenarios (`normal_operations`, `demand_spike`,
`vehicle_unavailable`) including `id`, `name`, `category`, `description`,
`type`, `demandMultiplierPercent`, `availableVehicles`, `affectedPeriod`,
`evaluationHorizonMin`.

### `POST /api/optimize`

Request:

```json
{ "scenarioId": "demand_spike" }
```

Response is a superset of the frontend `RecoveryPlanResult`: `status`,
`originalTrips`, `proposedTrips`, `totalTrips`, `constraints`,
`hardViolationCount`, `metrics`, plus `runId`, `scenarioName`, `message`,
`baselinePlan`, `optimizedPlan`, `validation`, `simulation`,
`baselineMetrics`, `optimizedMetrics`, `differences`, `warnings`.

- Unknown scenario → `404`.
- Malformed body → `422`.
- Infeasible scenario → `200` with `status = "infeasible"` and an explanatory
  `message`/`warnings` (never a silently-invalid plan).

### `GET /api/evaluation` and `GET /api/evaluation/{run_id}`

`data` matches the frontend `PerformanceRun` shape (`metrics`,
`passengerOutcome`, `fleetUtilization`, `etaWithinThreeMinutes`, `keyFinding`).
Unknown run ids → `404`.

## Optimization model and assumptions

Fleet selection, then a constructive heuristic, then a local-search repair pass
(see `app/optimizer/solve.py`). No commercial solver is used, so the result is a
feasible plan, not a proven optimum. Constraints enforced and independently
re-checked by `app/validation/constraints.py`:

| id | Constraint |
| --- | --- |
| `vehicle-assignment` | Every trip references a known route and vehicle |
| `vehicle-availability` | Only eligible vehicles; count ≤ `availableVehicles` |
| `departure-windows` | Departures inside `affectedPeriod`; arrival within horizon |
| `vehicle-turnaround` | ≥ turnaround minutes between a vehicle's trips |
| `segment-capacity` | Cumulative boardings never exceed vehicle capacity |
| `transfer-buffer` | ≥ transfer buffer at the terminal between trips |

Documented assumptions: inbound-only trips ending at the route terminal;
single-destination demand so capacity = cumulative boardings; travel time from
haversine distance / average speed; fixed dwell and turnaround; deterministic
congestion factor derived from demand buckets; 5-minute departure steps.

## Simulation and evaluation

`app/simulation/engine.py` runs a deterministic discrete-event simulation
(fixed seed). Metrics are computed from simulation output only:

- Passengers served / unserved (missed connections, capacity-denied).
- Average waiting time.
- Trips completed, vehicle distance, total travel time, capacity violations.
- ETA MAE and share of ETAs within 3 minutes.
- Per-vehicle utilization.

Baseline and optimized plans are always simulated under the **same** demand and
scenario conditions (`app/evaluation/metrics.py`, `comparison.py`).

## Limitations

- Single-destination inbound model; terminal/outbound demand is treated as
  out of scope.
- ETA is a deterministic schedule-based estimate, not an ML model.
- Evaluation runs are stored in memory for the current process; restart clears
  them (they are re-seeded at startup).
- No real-time GPS or historical data source is wired in.
