# Frontend and backend integration

Use the two-terminal setup in [README.md](README.md) to run the app. The frontend API base is configured through `frontend/.env.local`; the backend reads the root `data/` directory unless `ROUTEPULSE_DATA_DIR` is set.

## Connected flows

- Operations loads routes, stops, vehicles, trips, demand, ETAs, and alerts from the operations API.
- Recovery Planner requests a baseline and optimized evaluation from `POST /api/v1/evaluate`.
- The evaluation returns both plans, simulator metrics, validation results, and the full service assignment lists.
- Performance Lab reads recent evaluation summaries and requests selected evaluation details from the backend.
- Route geometry comes from the configured network and the frontend's saved road geometry. Baseline and optimized assignments are held separately for map rendering.

## Optimizer behavior

The active planner is deterministic and greedy. It uses objective weights for operating cost, vehicle distance, road-network reposition distance, vehicle changes, passenger wait, unserved passengers, unassigned services, and constraint findings. It evaluates candidate schedules with the simulator and retains the baseline assignment when the candidate objective is not lower or the candidate has worse hard-constraint results. The API accepts `time_limit_seconds` for compatibility and reports that the current greedy planner does not apply it.

Simulation history is held in backend process memory and resets when the process restarts. Run one backend process when using Performance Lab history.
