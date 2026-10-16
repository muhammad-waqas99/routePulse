"""Optional Groq LLM explanation layer.

The numerical predictions are computed entirely in Python (deterministic, no
LLM tokens). This module ONLY converts those results into short plain-English
explanations using Groq's ``openai/gpt-oss-20b``.

Design rules (keep API usage low):
- Never part of the core prediction path (lazy, called explicitly).
- Send summaries, not raw data.
- Ask for 2-3 concise sentences.
- Cache by input fingerprint.
- Best-effort: a failed call returns ``None`` and never breaks the pipeline.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.request

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"

_SYSTEM_PROMPT = (
    "You are the RoutePulse transport assistant. Explain predictions and "
    "suggest operator actions in 2-3 concise sentences. Never invent numbers."
)


def _repo_root() -> str:
                                                                    
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def load_api_key() -> str | None:
    """Load GROQ_API_KEY from the environment or the repo-root .env.

    Accepts both ``KEY=VALUE`` and ``KEY: VALUE`` separators.
    """
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key

    env_path = os.environ.get("ROUTEPULSE_ENV") or os.path.join(_repo_root(), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for sep in ("=", ":"):
                    if sep in line:
                        k, v = line.split(sep, 1)
                        if k.strip().lower() in ("groq_api_key", "groqapikey"):
                            return v.strip().strip('"').strip("'")
    except OSError:
        return None
    return None


class GroqExplainer:
    """Lazy, cached Groq-based explanation layer."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key if api_key is not None else load_api_key()
        self._cache: dict[str, str] = {}

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def explain(self, prompt: str, max_tokens: int = 150) -> str | None:
        if not self.available:
            return None

        fingerprint = hashlib.sha256((self.model + prompt).encode("utf-8")).hexdigest()
        if fingerprint in self._cache:
            return self._cache[fingerprint]

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        try:
            req = urllib.request.Request(
                GROQ_CHAT_URL,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                                                                             
                    "User-Agent": "RoutePulse/0.1 (+https://github.com/muhammad-waqas99/routePulse)",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"].strip()
            self._cache[fingerprint] = text
            return text
        except Exception as exc:                                             
            return f"(explanation unavailable: {exc})"

    def explain_stop(self, forecast) -> str | None:
        """Explain a single StopForecast."""
        prompt = (
            f"Stop {forecast.stop_id} is predicted to have "
            f"{forecast.predicted_passengers} passengers "
            f"(range {forecast.demand_lower}-{forecast.demand_upper}) in the next "
            f"{forecast.horizon_minutes} minutes. Available capacity is "
            f"{forecast.available_capacity}, shortfall {forecast.capacity_shortfall}, "
            f"crowding risk {forecast.crowding_risk}. "
            f"Explain why and suggest one operator action."
        )
        return self.explain(prompt)
