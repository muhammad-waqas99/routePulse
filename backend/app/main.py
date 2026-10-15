"""FastAPI application entry point for the RoutePulse backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api import evaluation, health, operations, optimization, scenarios
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("routepulse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate the seed data and pre-compute evaluation runs so the Performance
    # Lab has real data immediately.
    from app.services.operations_service import referential_integrity_errors
    from app.services.pipeline_service import seed_runs

    errors = referential_integrity_errors()
    if errors:
        logger.warning("Seed network integrity issues: %s", "; ".join(errors))
    else:
        logger.info("Seed network referential integrity OK")

    try:
        count = seed_runs()
        logger.info("Pre-computed %d evaluation run(s) at startup", count)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to pre-compute startup evaluation runs")

    yield


app = FastAPI(
    title="RoutePulse Campus Transportation API",
    version=__version__,
    description=(
        "Operations overview, scenario management, recovery optimization, "
        "independent validation and simulation-based evaluation."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(operations.router)
app.include_router(scenarios.router)
app.include_router(optimization.router)
app.include_router(evaluation.router)


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "service": "routepulse-backend",
        "version": __version__,
        "docs": "/docs",
    }


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "error": "http_error",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "The request body or parameters are invalid.",
            "error": "validation_error",
            "detail": str(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred.",
            "error": "internal_error",
        },
    )
