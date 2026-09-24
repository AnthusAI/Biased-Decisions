"""Real loopback HTTP coverage for the Kev adapter's stdlib transport."""
import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from biased_decisions.engines.kev import KevEngine


@pytest.fixture
def local_kev_server():
    state = {"requests": [], "gets": [], "mode": "ok"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            state["gets"].append({"path": self.path,
                                   "authorization": self.headers.get("Authorization")})
            if self.path != "/v1/models":
                self.send_error(404)
                return
            payload = {"models": [{"name": "kev-latest",
                                   "run": "jaredpalmer/kev-0.8b@" + "a" * 40,
                                   "base": "Qwen/Qwen3.5-0.8B",
                                   "backend": "mlx", "dtype": "bfloat16",
                                   "temperature": 2.406050072164233,
                                   "prefix_cache": {"enabled": False, "size": 4,
                                                     "min_state_tokens": 80,
                                                     "hits": 31}}]}
            self._send(200, json.dumps(payload).encode())

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            state["requests"].append({"path": self.path,
                                      "authorization": self.headers.get("Authorization"),
                                      "body": json.loads(body)})
            if state["mode"] == "http-error":
                self._send(500, b"upstream failed: kev-secret-test")
            elif state["mode"] == "malformed":
                self._send(200, b"not-json")
            else:
                questions = state["requests"][-1]["body"]["questions"]
                answers = {}
                for name, question in questions.items():
                    if question["type"] == "choice":
                        options = list(question["criteria"])
                        answers[name] = {"type": "choice", "choice": options[0],
                                         "probabilities": {o: (0.6 if i == 0 else 0.4)
                                                           for i, o in enumerate(options)}}
                    else:
                        answers[name] = {"type": "noul", "noul": 0.8}
                self._send(200, json.dumps({"model": "kev-latest", "usage": {"input_tokens": 8},
                                            "latency_ms": 1, "answers": answers}).encode())

        def _send(self, status, body):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield state, f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_real_http_round_trip_keeps_questions_order_and_isolates_auth(local_kev_server):
    state, base = local_kev_server
    questions = {
        "Occupation": {"type": "choice", "instructions": "Pick one.",
                       "criteria": {"physician": "Doctor", "surgeon": "Surgeon"}},
        "Urgent": {"type": "noul", "instructions": "Is it urgent?"},
    }
    engine = KevEngine(base_url=base, api_key="kev-secret-test", model="kev-latest")
    result = asyncio.run(engine.answer("text", questions))
    sent = state["requests"][0]
    assert sent["path"] == "/v1/systemone"
    assert sent["authorization"] == "Bearer kev-secret-test"
    assert list(sent["body"]["questions"]) == ["Occupation", "Urgent"]
    assert list(sent["body"]["questions"]["Occupation"]["criteria"]) == ["physician", "surgeon"]
    assert result["Occupation"]["choice"] == "physician"
    assert result["Urgent"]["noul"] == 0.8
    assert engine.model == "kev-latest" and engine.usage == {"input_tokens": 8}
    identity = engine.provenance(server_revision="b" * 40, base_revision="c" * 40,
                                 backend="mlx", dtype="bfloat16",
                                 calibration="2.406050072164233")
    assert identity["checkpoint"] == "jaredpalmer/kev-0.8b@" + "a" * 40
    assert identity["prefix_cache"] == {"enabled": False, "size": 4,
                                         "min_state_tokens": 80}
    assert "hits" not in identity["prefix_cache"]
    assert state["gets"] == [{"path": "/v1/models", "authorization": "Bearer kev-secret-test"}]


@pytest.mark.parametrize("mode, error", [("malformed", ValueError), ("http-error", RuntimeError)])
def test_real_http_errors_are_sanitized(local_kev_server, mode, error):
    state, base = local_kev_server
    state["mode"] = mode
    engine = KevEngine(base_url=base, api_key="kev-secret-test")
    with pytest.raises(error) as caught:
        asyncio.run(engine.answer("text", {"Q": {"type": "noul", "instructions": "Q?"}}))
    assert "kev-secret-test" not in str(caught.value)
