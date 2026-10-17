# RoutePulse backend

FastAPI service for RoutePulse network data, schedule validation, optimization, and simulation.

From the project root, create the environment and start the API:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

The service reads the project-level `data/` directory by default. `ROUTEPULSE_DATA_DIR` can point it to a different dataset. API documentation is at `http://localhost:8000/docs` while the service is running.
