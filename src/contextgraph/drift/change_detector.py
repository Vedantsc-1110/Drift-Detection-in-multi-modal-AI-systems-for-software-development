"""Change event detection from git history (§7.3 Step 1, PART4 Task 4.2).

Given a repo path, reports the newest commit (SHA, message) plus the changed
file paths classified for extractor routing (source / document / workflow /
other). Committed history only — deterministic. No network access.
"""

from __future__ import annotations

from pathlib import Path

SOURCE_SUFFIXES = {".xml", ".java", ".groovy", ".gradle", ".py", ".properties"}
DOCUMENT_SUFFIXES = {".md", ".docx", ".pdf", ".txt", ".rst"}
WORKFLOW_SUFFIXES = {".yml", ".yaml"}


def classify(path: str) -> str:
    """Route a repo-relative path to its extractor family."""
    suffix = Path(path).suffix.lower()
    if suffix in WORKFLOW_SUFFIXES:
        return "workflow"
    if suffix in DOCUMENT_SUFFIXES:
        return "document"
    if suffix in SOURCE_SUFFIXES:
        return "source"
    return "other"


def _repo(repo_path):
    import git

    return git.Repo(repo_path)


def detect_changes(repo_path, since_sha: str | None = None) -> dict:
    """Diff since_sha..HEAD (default: HEAD against its first parent).

    Returns {commit_sha, message, changed: [{path, change_type, category}]}.
    change_type is git --name-status status (A/M/D/R...). Raises ValueError
    for unknown revisions; RuntimeError when HEAD has no commits.
    """
    repo = _repo(repo_path)
    try:
        head = repo.head.commit
    except ValueError as exc:
        raise RuntimeError("repository has no commits") from exc
    if since_sha is None:
        parents = head.parents
        base = parents[0] if parents else None
        if base is None:
            raw = repo.git.diff("--name-status", "--no-renames", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "HEAD")
        else:
            raw = repo.git.diff("--name-status", "--no-renames", base.hexsha, "HEAD")
    else:
        try:
            repo.git.cat_file("-e", since_sha + "^{commit}")
        except Exception as exc:  # noqa: BLE001 - unknown revision
            raise ValueError("unknown revision: %s" % since_sha) from exc
        raw = repo.git.diff("--name-status", "--no-renames", since_sha, "HEAD")
    changed = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        status, _, path = line.partition("\t")
        status, path = status.strip(), path.strip()
        if status.startswith("R"):
            old, _, new = path.partition("\t")
            changed.append({"path": new, "change_type": "R", "category": classify(new),
                            "old_path": old})
        elif path:
            changed.append({"path": path, "change_type": status[:1], "category": classify(path)})
    changed.sort(key=lambda c: c["path"])
    return {"commit_sha": head.hexsha, "message": head.message.strip(),
            "committed_at": head.committed_datetime.isoformat(), "changed": changed}
