"""FastAPI application entry point.

OWNED BY: integration / API workstream.

Wires the prediction engine behind ``POST /api/v1/prediction`` and mounts the
network/scenarios/optimization/evaluation routers described in
``Wild Bugs.md`` ("API contracts"). Kept as a stub until the API workstream
finalizes the endpoints; importing this module must not require FastAPI.
"""
from __future__ import annotations


def create_app():
    """Build the FastAPI app (imports FastAPI lazily)."""
    from fastapi import FastAPI  # noqa: PLC0415

    app = FastAPI(title="RoutePulse API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

<<<<<<< HEAD
    # Independent constraint validator: POST /api/v1/validate.
    from app.api.validation import router as validation_router  # noqa: PLC0415

    app.include_router(validation_router)

    # TODO(api): mount the remaining routers and expose POST /api/v1/prediction.
=======
    # TODO(api): mount routers and expose POST /api/v1/prediction.
>>>>>>> 5fd910e332bd2dd15be8e0bad5e9bf0fa44b5a52
    return app

app = create_app()
