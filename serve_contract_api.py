"""Serve a local explorer from demo fixtures or contract pipeline outputs.

Run ``python serve_contract_api.py --demo`` for the labeled fixture demo, or
``python serve_contract_api.py --data outputs/my-run`` for extracted Turtle.
The source files are read-only; the temporary quad store is discarded on exit.
"""
import argparse
import sys
from tempfile import TemporaryDirectory
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from contextgraph.contract_api import create_app
from contextgraph.contract_store import ContractStore, GRAPH_FILES

LOADS = (("structural.ttl", "urn:ofbiz_structural"), ("airflow.ttl", "urn:airflow"),
         ("semantic.ttl", "urn:ofbiz_semantic"), ("cuad.ttl", "urn:cuad"),
         ("bridges.ttl", "urn:bridges"))


def load_data(store: ContractStore, directory: Path) -> dict[str, int]:
    """Load canonical output names, with aliases for the original API fixtures."""
    if not directory.is_dir():
        raise ValueError(f"Data directory does not exist: {directory}")
    aliases = {graph: filename for filename, graph in LOADS}
    files = {**GRAPH_FILES, "urn:bridges": "bridges.ttl"}
    loaded = {}
    for graph, filename in files.items():
        path = directory / filename
        if not path.is_file():
            path = directory / aliases.get(graph, filename)
        if path.is_file():
            loaded[graph] = store.load_file(path, graph)
    if not loaded:
        raise ValueError("No recognized Turtle files found. Use --demo or a contract pipeline output directory.")
    return loaded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--data", type=Path, help="Directory containing contract .ttl outputs")
    source.add_argument("--demo", action="store_true", help="Load curated API test fixtures")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    import uvicorn

    data = (Path(__file__).resolve().parent / "tests/fixtures/contract/api" if args.demo else args.data).resolve()
    fixture_root = Path(__file__).resolve().parent / "tests/fixtures"
    mode = "demo" if args.demo or data.is_relative_to(fixture_root) else "local"
    with TemporaryDirectory(prefix="context-atlas-") as directory:
        store = ContractStore(Path(directory) / "quads")
        try:
            loaded = load_data(store, data)
            print(f"Loaded {store.count()} triples across {len(loaded)} graphs ({mode}).")
            print(f"Open http://127.0.0.1:{args.port}/dashboard")
            uvicorn.run(create_app(store, data_info={"mode": mode, "source": str(data)}),
                        host="127.0.0.1", port=args.port, log_level="warning")
        except ValueError as exc:
            parser.error(str(exc))
        finally:
            store.close()
            # Release the embedded store lock before TemporaryDirectory cleans up.
            del store._store


if __name__ == "__main__":
    main()
