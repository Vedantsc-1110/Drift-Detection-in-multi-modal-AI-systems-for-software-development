"""Incremental re-extraction hook (§7.3 Step 2, PART4 Task 4.3).

SHA-256 per file vs a JSON cache; unchanged files are skipped; the
configured extractor COMMAND (never an import — Step 2 discipline) runs via
subprocess once per changed file and must write Turtle to its {out} path.
Outputs merge into one rdflib graph. No network access.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import rdflib


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_cache(cache_path: Path) -> dict:
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return dict(data) if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        return {}


def run_incremental(root, cache_path, extractor_cmd: list, out_dir,
                    extensions=(".xml",), merged_name: str = "merged.ttl") -> dict:
    """Run the extractor command only for new/changed files.

    extractor_cmd: argv template with {file} (source) and {out} (.ttl target)
    placeholders. Returns {processed, skipped, merged, triples, cache}.
    """
    root, cache_path, out_dir = Path(root), Path(cache_path), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if "{file}" not in extractor_cmd or "{out}" not in extractor_cmd:
        raise ValueError("extractor_cmd must contain {file} and {out} placeholders")
    wanted = {e.lower() if e.startswith(".") else "." + e.lower() for e in extensions}
    candidates = sorted(p for p in root.rglob("*")
                        if p.is_file() and p.suffix.lower() in wanted)
    previous = _load_cache(cache_path)
    cache, processed, skipped = {}, [], []
    for path in candidates:
        rel = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        cache[rel] = digest
        # Preserve the whole relative path and source suffix: same-named files
        # in different components (or a.xml versus a.java) must never collide.
        target = out_dir / (rel + ".ttl")
        if previous.get(rel) == digest and target.is_file():
            skipped.append(rel)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        argv = [arg.format(file=str(path), out=str(target)) for arg in extractor_cmd]
        completed = subprocess.run(argv, capture_output=True, text=True, timeout=300)
        if completed.returncode != 0:
            raise RuntimeError("extractor failed for %s: %s" % (rel, completed.stderr.strip()))
        if not target.is_file():
            raise RuntimeError("extractor produced no .ttl for %s" % rel)
        processed.append(rel)
    processed.sort()
    skipped.sort()
    merged = rdflib.Graph()
    for rel in processed:
        merged.parse(str(out_dir / (rel + ".ttl")), format="turtle")
    merged_path = out_dir / merged_name
    merged_path.write_text(merged.serialize(format="turtle"), encoding="utf-8")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"processed": processed, "skipped": skipped, "merged": str(merged_path),
            "triples": len(merged), "cache": cache}
