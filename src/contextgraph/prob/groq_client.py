"""Groq primary LLM client (PART2_PLAN Task 2.1, Algorithm 2).

Llama 3.3 70B via the Groq OpenAI-compatible endpoint (stdlib urllib only).
Contract extractedBy label: "llama-3.3-70b".

Offline-first design: the HTTP transport is injectable, so unit tests run
with fakes and never touch the network. Live calls need GROQ_API_KEY.
"""

from __future__ import annotations

import json
import os
import urllib.request

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL_ID = "llama-3.3-70b-versatile"
EXTRACTED_BY = "llama-3.3-70b"


class GroqError(RuntimeError):
    pass


class GroqClient:
    name = "groq:" + MODEL_ID

    def __init__(self, model=MODEL_ID, api_key=None, timeout=120, transport=None):
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.timeout = timeout
        self.transport = transport or self._live_transport

    def complete_json(self, system: str, user: str) -> str:
        """Return the assistant's raw text (expected JSON). Raises GroqError."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        try:
            body = self.transport(payload)
        except GroqError:
            raise
        except Exception as exc:  # noqa: BLE001 - router decides fallback
            raise GroqError("groq transport failed: %s" % exc) from exc
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GroqError("unexpected Groq response shape") from exc

    def _live_transport(self, payload: dict) -> dict:
        if not self.api_key:
            raise GroqError("GROQ_API_KEY is not set")
        req = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except GroqError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise GroqError("groq HTTP call failed: %s" % exc) from exc
