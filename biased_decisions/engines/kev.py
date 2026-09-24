"""HTTP adapter for a user-run Kev ``/v1/systemone`` server.

No Kev SDK or hosted endpoint is selected implicitly. The adapter uses its own KEV_* settings
and standard-library HTTP, keeping ordinary imports usable without optional engine packages.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import re
from typing import Any, Dict, Mapping, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


class KevEngine:
    name = "kev"

    def __init__(self, *, base_url: Optional[str] = None, api_key: Optional[str] = None,
                 model: Optional[str] = None, timeout: float = 120.0, transport: Any = None):
        self.base_url = (base_url if base_url is not None else os.getenv("KEV_BASE_URL", "")).rstrip("/")
        if not self.base_url:
            raise ValueError("KEV_BASE_URL is required to use Kev")
        self.api_key = api_key if api_key is not None else os.getenv("KEV_API_KEY")
        self.model_name = model if model is not None else os.getenv("KEV_MODEL", "kev-latest")
        self.timeout = timeout
        self._transport = transport
        self.model: Optional[str] = None
        self.usage: Optional[dict] = None
        self.latency_ms: Optional[float] = None

    def _post(self, url: str, payload: dict, headers: dict, timeout: float) -> dict:
        if self._transport is not None:
            return self._transport.post(url, payload, headers, timeout)
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers,
                          method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, OSError) as error:
            # Avoid rendering request headers or the configured URL/key in errors.
            raise RuntimeError(f"Kev request failed ({type(error).__name__})") from None

    def get_models(self) -> dict:
        """Return the server's model identity document without exposing credentials."""
        if self._transport is not None:
            return self._transport.get(f"{self.base_url}/v1/models", self._headers(), self.timeout)
        request = Request(f"{self.base_url}/v1/models", headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, OSError) as error:
            raise RuntimeError(f"Kev model lookup failed ({type(error).__name__})") from None

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def provenance(self, *, server_revision: str, base_revision: str, backend: str, dtype: str,
                   calibration: str) -> dict:
        """Require concrete run identity; alias-only records are not reproducible."""
        models = self.get_models()
        requested = self.model_name
        candidates = models.get("data", models.get("models", [])) if isinstance(models, Mapping) else []
        entry = next((m for m in candidates if m.get("id") == requested or
                      m.get("model") == requested or m.get("name") == requested), None) if isinstance(candidates, list) else None
        if entry is None:
            raise ValueError("Kev /v1/models did not identify the requested model")
        checkpoint = entry.get("revision") or entry.get("checkpoint") or entry.get("run")
        if not isinstance(checkpoint, str) or not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", checkpoint):
            raise ValueError("Kev /v1/models must expose an immutable repository@40-hex checkpoint")
        if not re.fullmatch(r"[0-9a-f]{40}", server_revision or ""):
            raise ValueError("Kev server revision must be a 40-hex git commit")
        if not re.fullmatch(r"[0-9a-f]{40}", base_revision or ""):
            raise ValueError("Kev base revision must be a 40-hex git commit")
        actual_backend = entry.get("backend") or backend
        actual_dtype = entry.get("dtype") or dtype
        temperature = entry.get("temperature")
        if entry.get("backend") and backend != actual_backend:
            raise ValueError("requested Kev backend does not match /v1/models")
        if entry.get("dtype") and dtype != actual_dtype:
            raise ValueError("requested Kev dtype does not match /v1/models")
        if temperature is not None and calibration not in (str(temperature), f"temperature={temperature}"):
            raise ValueError("Kev calibration identity must match the /v1/models temperature")
        cache = entry.get("prefix_cache")
        cache_config = ({key: cache[key] for key in ("enabled", "size", "min_state_tokens")
                         if key in cache} if isinstance(cache, Mapping) else
                        ({"enabled": cache} if isinstance(cache, bool) else None))
        return {"model": entry.get("id") or entry.get("model") or entry.get("name"),
                "checkpoint": checkpoint, "base": entry.get("base"),
                "base_revision": base_revision,
                "server_revision": server_revision,
                "backend": actual_backend, "dtype": actual_dtype,
                "calibration": f"temperature={temperature}" if temperature is not None else calibration,
                "prefix_cache": cache_config}

    async def answer(self, text: str, questions: Mapping[str, Mapping[str, Any]]) -> Dict[str, dict]:
        payload = {"state": text, "model": self.model_name, "questions": dict(questions)}
        headers = self._headers()
        response = await asyncio.to_thread(self._post, f"{self.base_url}/v1/systemone",
                                           payload, headers, self.timeout)
        if not isinstance(response, Mapping) or not isinstance(response.get("answers"), Mapping):
            raise ValueError("Kev returned an invalid response")
        answers = response["answers"]
        if set(answers) != set(questions):
            raise ValueError("Kev response question coverage does not match the request")
        checked: Dict[str, dict] = {}
        for name, question in questions.items():
            answer = answers[name]
            if not isinstance(answer, Mapping):
                raise ValueError(f"Kev answer {name!r} is invalid")
            answer = dict(answer)
            if question.get("type") == "choice":
                options = list(question.get("criteria", {}))
                probabilities = answer.get("probabilities")
                if not isinstance(probabilities, Mapping) or set(probabilities) != set(options):
                    raise ValueError(f"Kev probabilities for {name!r} do not cover the options")
                for value in probabilities.values():
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                        raise ValueError(f"Kev probabilities for {name!r} must be finite values from 0 to 1")
                # The pinned upstream API rounds each option probability to four decimals.
                # Permit one half-unit per option of accumulated serialization error.
                tolerance = len(options) * 0.0000500001
                if abs(math.fsum(probabilities.values()) - 1.0) > tolerance:
                    raise ValueError(f"Kev probabilities for {name!r} must sum to 1 within {tolerance:g}")
                if answer.get("choice") not in options:
                    raise ValueError(f"Kev choice for {name!r} is not a requested option")
                # JSON object order is preserved by Python. Keep the task's option order in the
                # record even if a server serializes the returned map differently.
                answer["probabilities"] = {option: probabilities[option] for option in options}
            elif question.get("type") == "noul":
                value = answer.get("noul")
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError(f"Kev noul value for {name!r} must be finite and between 0 and 1")
            if answer.get("type") != question.get("type"):
                raise ValueError(f"Kev answer type for {name!r} does not match the request")
            checked[name] = answer
        self.model = response.get("model")
        self.usage = response.get("usage")
        self.latency_ms = response.get("latency_ms")
        return checked
