"""Probabilistic extraction layer (Ollama). Separate from the deterministic path.

Guarantees: every output is marked probabilistic, carries evidence +
confidence + model + prompt version + timestamp, starts as `proposed`, and
can NEVER overwrite deterministic facts (guarded at review time).
"""
