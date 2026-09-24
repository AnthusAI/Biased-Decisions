"""HTTP adapter for a user-run Kev ``/v1/systemone`` server.

No Kev SDK or hosted endpoint is selected implicitly. The adapter uses its own KEV_* settings
and standard-library HTTP, keeping ordinary imports usable without optional engine packages.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
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

    async def answer(self, text: str, questions: Mapping[str, Mapping[str, Any]]) -> Dict[str, dict]:
        payload = {"state": text, "model": self.model_name, "questions": dict(questions)}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
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
                if answer.get("choice") not in options:
                    raise ValueError(f"Kev choice for {name!r} is not a requested option")
            checked[name] = answer
        self.model = response.get("model")
        self.usage = response.get("usage")
        self.latency_ms = response.get("latency_ms")
        return checked
