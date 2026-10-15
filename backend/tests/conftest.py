"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import run_store


@pytest.fixture(autouse=True)
def clean_run_store():
    """Start and end each test with an empty run store."""

    run_store.clear()
    yield
    run_store.clear()


@pytest.fixture
def client():
    """A TestClient that runs the app lifespan (seeds evaluation runs)."""

    with TestClient(app) as test_client:
        yield test_client
