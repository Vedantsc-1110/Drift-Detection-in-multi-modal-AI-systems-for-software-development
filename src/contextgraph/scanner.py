"""Read-only scanner: discover in-scope artifact files under a component directory.

Explicit dependency scope: a component may declare additional artifacts from
other components (e.g. order -> datamodel entity models). Dependencies are an
explicit, reviewable map below -- never inferred. Dependency files keep their
owning component as owner for attribution.
"""
from __future__ import annotations

from pathlib import Path

# component -> {"component_xml": repo-rel path, "files": [(repo-rel path, role)]}
# Roles: component | service | entity | eca (same parser registry keys).
COMPONENT_DEPENDENCIES = {
    "order": {
        "component_xml": "applications/datamodel/ofbiz-component.xml",
        "files": [
            ("applications/datamodel/entitydef/order-entitymodel.xml", "entity"),
        ],
    },
}


def discover(component_dir: Path, repo_root: Path = None, include_dependencies: bool = False):
    """Return {role: [(path, owner)]}. owner = owning component directory name.

    Default (flag off) is exactly the old behavior: only the component's own
    directory. Never writes to the dataset.
    """
    component_dir = Path(component_dir)
    if repo_root is None:
        repo_root = component_dir.parent.parent
    repo_root = Path(repo_root)
    owner = component_dir.name
    out = {"component": [], "service": [], "entity": [], "eca": [], "controller": [], "gradle": []}
    comp = component_dir / "ofbiz-component.xml"
    if comp.is_file():
        out["component"].append((comp, owner))
    servicedef = component_dir / "servicedef"
    if servicedef.is_dir():
        for path in sorted(servicedef.glob("*.xml")):
            name = path.name
            if name in ("secas.xml",) or name.startswith("secas_") or "eca" in name.lower():
                out["eca"].append((path, owner))
            else:
                out["service"].append((path, owner))
    entitydef = component_dir / "entitydef"
    if entitydef.is_dir():
        for path in sorted(entitydef.glob("*.xml")):
            name = path.name
            if name in ("eecas.xml",) or "eca" in name.lower():
                out["eca"].append((path, owner))
            else:
                out["entity"].append((path, owner))
    # Plan fixture layout (Task 1.3): testdef/*.xml holds <eca> rules.
    testdef = component_dir / "testdef"
    if testdef.is_dir():
        for path in sorted(testdef.glob("*.xml")):
            out["eca"].append((path, owner))
    if include_dependencies:
        for dep_xml, dep_files in _deps_for(owner):
            full = repo_root / dep_xml
            if full.is_file():
                out["component"].append((full, _owner_of(full, repo_root)))
            for rel, role in dep_files:
                full = repo_root / rel
                if full.is_file() and role in out:
                    out[role].append((full, _owner_of(full, repo_root)))
    # Controller routes (webapp/**/controller.xml) + module build file.
    webapp = component_dir / "webapp"
    if webapp.is_dir():
        for path in sorted(webapp.rglob("controller.xml")):
            out["controller"].append((path, owner))
    direct_controller = component_dir / "controller.xml"
    if direct_controller.is_file():
        out["controller"].append((direct_controller, owner))
    gradle = component_dir / "build.gradle"
    if gradle.is_file():
        out["gradle"].append((gradle, owner))
    for key in out:
        out[key] = sorted(out[key], key=lambda t: t[0].as_posix())
    return out


def _deps_for(owner):
    entry = COMPONENT_DEPENDENCIES.get(owner)
    if not entry:
        return []
    return [(entry["component_xml"], entry.get("files", []))]


def _owner_of(path: Path, repo_root: Path) -> str:
    """Owning component = directory containing ofbiz-component.xml upward search."""
    node = path.parent
    while node != repo_root and repo_root in node.parents:
        if (node / "ofbiz-component.xml").is_file():
            return node.name
        node = node.parent
    if (node / "ofbiz-component.xml").is_file():
        return node.name
    return node.name
