"""Run every self-contained test, excluding external OFBiz and live Ollama.

Usage: python scripts/run_offline_tests.py [additional pytest arguments]
The excluded integration suites remain runnable with python -m pytest once
their real-data prerequisites are installed. Skips are reported, not counted
as passes. Browser tests opt in separately via RUN_BROWSER_TESTS=1.
"""

import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
REQUIRES_OFBIZ = {
    "test_component.py", "test_datamodel.py", "test_eca.py", "test_entity.py",
    "test_graph.py", "test_inspect.py", "test_integration_focused.py",
    "test_pipeline.py", "test_report.py", "test_service.py", "test_shacl.py",
    "test_store.py",
}


def main() -> int:
    """Run fixture, API, graph, semantic, and drift checks without network."""
    tests = [str(path.relative_to(PROJECT)) for path in sorted((PROJECT / "tests").glob("test_*.py"))
             if path.name not in REQUIRES_OFBIZ]
    print(f"Running {len(tests)} self-contained test modules; {len(REQUIRES_OFBIZ)} real-OFBiz modules excluded.", flush=True)
    command = [sys.executable, "-m", "pytest", *tests, "-q", "-p", "no:cacheprovider",
               "-k", "not live_ollama_gated", *sys.argv[1:]]
    return subprocess.call(command, cwd=PROJECT)


if __name__ == "__main__":
    raise SystemExit(main())
