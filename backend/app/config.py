"""Runtime configuration for the RoutePulse backend.

Values are read from environment variables so the service can be launched
locally without editing code. Sensible defaults match the Vite dev server and
the sample campus data shipped with the repository.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Immutable application settings resolved from the environment."""

    host: str = os.getenv("ROUTEPULSE_HOST", "127.0.0.1")
    port: int = int(os.getenv("ROUTEPULSE_PORT", "8000"))
    cors_origins: list[str] = field(
        default_factory=lambda: _env_list(
            "ROUTEPULSE_CORS_ORIGINS",
            ["http://localhost:5173", "http://127.0.0.1:5173"],
        )
    )
    avg_speed_kmh: float = float(os.getenv("ROUTEPULSE_AVG_SPEED_KMH", "20.0"))
    sim_seed: int = int(os.getenv("ROUTEPULSE_SIM_SEED", "42"))

    network_path: Path = DATA_DIR / "network.json"
    scenarios_path: Path = DATA_DIR / "scenarios.json"


settings = Settings()
