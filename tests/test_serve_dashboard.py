"""Server loading must support the actual contract pipeline output names."""

import runpy
from pathlib import Path

import pytest

from contextgraph.contract_store import ContractStore, GRAPH_FILES


SERVER = runpy.run_path(str(Path(__file__).resolve().parents[1] / "serve_contract_api.py"))
TTL = '@prefix ctx: <http://context.example.org/> . ctx:Example a ctx:Service .'


def test_server_loads_all_canonical_pipeline_files(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    for name in [*GRAPH_FILES.values(), "bridges.ttl"]:
        (data / name).write_text(TTL, encoding="utf-8")
    store = ContractStore(tmp_path / "store")
    try:
        assert "load_data" in SERVER, "Server needs a reusable canonical/fixture loader"
        loaded = SERVER["load_data"](store, data)
        assert set(loaded) == {*GRAPH_FILES, "urn:bridges"}
        assert store.count() == 8
    finally:
        store.close()


def test_server_rejects_empty_directory(tmp_path):
    store = ContractStore(tmp_path / "store")
    try:
        assert "load_data" in SERVER
        with pytest.raises(ValueError, match="No recognized Turtle"):
            SERVER["load_data"](store, tmp_path)
    finally:
        store.close()
