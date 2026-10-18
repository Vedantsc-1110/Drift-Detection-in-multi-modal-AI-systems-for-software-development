"""Incremental file scanner per PART1_PLAN Task 1.1 (Algorithm 1 "File Scanner").

Adapted to existing repo layout: lives in src/contextgraph/ instead of
part1_deterministic/pipeline/. API matches P1.1 prompt:

    scan(root, extensions, cache_path) -> list[Path]

- Recursively scans ``root`` for files whose suffix is in ``extensions``.
- Computes SHA-256 per file, compares against JSON cache at ``cache_path``.
- Returns only changed or new files (sorted, deterministic).
- Updates the cache after processing. Missing (or corrupt) cache -> first
  run returns all files.
- Stdlib only (pathlib, hashlib, json). No network access.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

__all__ = ["scan", "sha256_file", "DEFAULT_EXTENSIONS"]

DEFAULT_EXTENSIONS = (".xml", ".java", ".groovy", ".gradle")


def sha256_file(path: Path) -> str:
    """SHA-256 hex digest of a file (chunked, read-only)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_extensions(extensions) -> set[str]:
    normalized: set[str] = set()
    for ext in extensions:
        e = str(ext).lower()
        if not e.startswith("."):
            e = "." + e
        normalized.add(e)
    return normalized


def _load_cache(cache_path: Path) -> dict:
    try:
        with open(cache_path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError, ValueError):
        pass
    return {}


def scan(root, extensions=DEFAULT_EXTENSIONS, cache_path=None) -> list[Path]:
    """Scan ``root`` and return changed/new files vs the SHA-256 cache.

    Args:
        root: directory to scan recursively.
        extensions: iterable of suffixes, e.g. (".xml", ".java"). The list
            is a parameter (not hardcoded) so Airflow .py and workflow
            .yml files reuse the same path in Tasks 1.5/1.6.
        cache_path: JSON file mapping repo-rel posix path -> sha256 hex.
            Defaults to ``<root>/.hash_cache.json`` when omitted.

    Returns:
        Sorted list of absolute Paths that are new or changed.
    """
    root = Path(root)
    if cache_path is None:
        cache_path = root / ".hash_cache.json"
    else:
        cache_path = Path(cache_path)

    wanted = _normalize_extensions(extensions)
    current: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in wanted:
            continue
        # Never treat the cache file itself as a scanned artifact.
        try:
            if path.resolve() == cache_path.resolve():
                continue
        except OSError:
            if path == cache_path:
                continue
        rel = path.relative_to(root).as_posix()
        current[rel] = path

    previous = _load_cache(cache_path)

    changed: list[Path] = []
    new_cache: dict[str, str] = {}
    for rel in sorted(current):
        digest = sha256_file(current[rel])
        new_cache[rel] = digest
        if previous.get(rel) != digest:
            changed.append(current[rel])

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(new_cache, fh, indent=2, sort_keys=True)
        fh.write("\n")

    return changed
