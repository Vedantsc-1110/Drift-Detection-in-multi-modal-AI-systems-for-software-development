"""Model clients behind one interface. OllamaClient = live path (stdlib only).
StubClient = deterministic stand-in for tests/demos, always labeled as stub."""
from __future__ import annotations

import json
import urllib.request


class ModelClient:
    name = "base"

    def complete_json(self, system: str, user: str):
        """Return the model's raw text response (expected to be a JSON array)."""
        raise NotImplementedError


class OllamaClient(ModelClient):
    def __init__(self, model, host="http://localhost:11434", timeout=300, seed=42):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.seed = seed
        self.name = "ollama:%s" % model

    def ping(self) -> bool:
        try:
            with urllib.request.urlopen(self.host + "/api/tags", timeout=10) as resp:
                return resp.status == 200
        except Exception:
            return False

    def complete_json(self, system: str, user: str):
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "format": "json",
                "stream": False,
                "options": {"temperature": 0, "seed": self.seed},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            self.host + "/api/chat", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["message"]["content"]


class StubClient(ModelClient):
    """Clearly-labeled deterministic stand-in. NEVER presented as an LLM."""

    name = "stub-test-client"

    def __init__(self, canned_text="[]"):
        self.canned_text = canned_text

    def complete_json(self, system: str, user: str):
        return self.canned_text
