"""Primary/fallback router (PART2_PLAN Task 2.1): Groq -> Ollama fallback.

Any exception from the primary routes to the fallback; the failure is
recorded in the returned errors list, never silently dropped. The caller
learns which model actually answered via the returned model name.
"""

from __future__ import annotations


class Router:
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def complete_json(self, system: str, user: str):
        """Return (text, model_name, errors)."""
        try:
            return self.primary.complete_json(system, user), self.primary.name, []
        except Exception as exc:  # noqa: BLE001 - fallback path is the point
            errors = ["primary %s failed: %s" % (self.primary.name, exc)]
            try:
                return self.fallback.complete_json(system, user), self.fallback.name, errors
            except Exception as exc2:  # noqa: BLE001
                errors.append("fallback %s failed: %s" % (self.fallback.name, exc2))
                raise RuntimeError("; ".join(errors)) from exc2
