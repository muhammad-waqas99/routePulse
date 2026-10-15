from future import annotations

def create_app():
"""Build the FastAPI application."""
from fastapi import FastAPI
from app.api.validation import router as validation_router

app = FastAPI(
    title="RoutePulse API",
    version="0.1.0",
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

# Independent constraint validator: POST /api/v1/validate.
app.include_router(validation_router)

# TODO(api): mount the remaining routers and expose POST /api/v1/prediction.

return app