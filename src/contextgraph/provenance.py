"""Provenance helpers: file hashing, artifact records, parse contexts (read-only)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from . import REPO_ID


@dataclass(frozen=True)
class Artifact:
    repo_id: str
    relpath: str  # repo-relative, forward slashes
    sha256: str
    artifact_type: str


@dataclass
class ParseContext:
    repo_root: Path
    repo_id: str
    artifact: Artifact
    tree: object = None  # lxml element tree, set by parsers
    file_index: int = 0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_for(repo_root: Path, path: Path, artifact_type: str) -> Artifact:
    rel = path.relative_to(repo_root).as_posix()
    return Artifact(
        repo_id=REPO_ID,
        relpath=rel,
        sha256=sha256_file(path),
        artifact_type=artifact_type,
    )


def parse_xml(path: Path):
    """Parse XML with line numbers. Raises on malformed input (caller records)."""
    parser = etree.XMLParser(remove_comments=False, recover=False)
    return etree.parse(str(path), parser)


def localname(element) -> str:
    tag = element.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def child_text(element, name: str):
    for child in element:
        if localname(child) == name and child.text and child.text.strip():
            return child.text.strip()
    return None
