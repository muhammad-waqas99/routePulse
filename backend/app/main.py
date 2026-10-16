"""FastAPI application entry point.

OWNED BY: integration / API workstream.

Wires the prediction engine behind ``POST /api/v1/prediction`` and mounts the
network/scenarios/optimization/evaluation routers described in
``Wild Bugs.md`` ("API contracts"). A module-level ``app`` FastAPI instance is
exposed so ASGI servers and platforms such as Vercel can discover it
(``uvicorn app.main:app``); ``create_app()`` remains available for the
factory-style ``uvicorn app.main:create_app --factory`` invocation.
"""
from __future__ import annotations


def create_app():
    """Build the FastAPI app (imports FastAPI lazily)."""
    import os                 

    from fastapi import FastAPI                 
    from fastapi.middleware.cors import CORSMiddleware                 

    app = FastAPI(title="RoutePulse API", version="0.1.0")

                                                                                
                                                                              
    configured_origins = os.environ.get("ROUTEPULSE_CORS_ORIGINS")
    allow_origins = (
        [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
        if configured_origins
        else ["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

                                                              
    from app.api.validation import router as validation_router                 
    from app.api.operations import router as operations_router                 
    from app.api.network import router as network_router                 
    from app.api.scenarios import router as scenarios_router                 
    from app.api.optimization import router as optimization_router                 
    from app.api.evaluation import router as evaluation_router                 
    from app.api.runs import router as runs_router                 

    app.include_router(network_router)
    app.include_router(scenarios_router)
    app.include_router(optimization_router)
    app.include_router(evaluation_router)
    app.include_router(runs_router)
    app.include_router(validation_router)
    app.include_router(operations_router)

    return app


                                                                               
                                                                        
app = create_app()
