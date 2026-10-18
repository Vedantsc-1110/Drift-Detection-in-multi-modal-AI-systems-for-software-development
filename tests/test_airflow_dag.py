"""Task 1.5 tests: Airflow DAG extractor (PART1_PLAN Task 1.5).

Standalone on tests/fixtures/airflow (synthetic). Uses stdlib ast only.
Every DAG/task/edge extracted; operator types and schedules match;
docstrings/comments recorded; full provenance; graph == urn:airflow.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.parsers import airflow_dag  # noqa: E402
from contextgraph.provenance import ParseContext, artifact_for  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "airflow"


def _parse(name):
    path = FIXTURES / name
    assert path.is_file(), "missing fixture %s" % name
    artifact = artifact_for(PROJECT_ROOT, path, "airflow-dag")
    assert len(artifact.sha256) == 64
    ctx = ParseContext(repo_root=PROJECT_ROOT, repo_id="fixture-airflow", artifact=artifact, tree=None)
    ctx.component_name = "airflow"
    return airflow_dag.parse(path, ctx)


def _by_kind(facts, kind):
    return [f for f in facts if f["kind"] == kind]


def test_etl_dag_id_schedule_and_tasks():
    facts, _ = _parse("dag_orders_etl.py")
    dags = _by_kind(facts, "airflow_dag")
    assert len(dags) == 1
    dag = dags[0]
    assert dag["props"]["dag_id"] == "orders_etl"
    assert dag["props"]["schedule"] == "@daily"
    assert dag["props"]["default_args"] == {"owner": "data-eng", "retries": 1}
    tasks = {f["props"]["task_id"]: f for f in _by_kind(facts, "airflow_task")}
    assert set(tasks) == {"extract_orders", "transform_orders", "audit_orders", "load_orders"}
    assert tasks["extract_orders"]["props"]["operator"] == "PythonOperator"
    assert tasks["transform_orders"]["props"]["operator"] == "PythonOperator"
    assert tasks["audit_orders"]["props"]["operator"] == "BashOperator"
    assert tasks["load_orders"]["props"]["operator"] == "BashOperator"


def test_etl_chain_edges_with_list_fan():
    facts, _ = _parse("dag_orders_etl.py")
    edges = {(f["props"]["from"].rsplit("/", 1)[-1], f["props"]["to"].rsplit("/", 1)[-1]) for f in _by_kind(facts, "edge")}
    # (downstream, upstream): fan-out then fan-in around transform/audit.
    assert edges == {
        ("transform_orders", "extract_orders"),
        ("audit_orders", "extract_orders"),
        ("load_orders", "transform_orders"),
        ("load_orders", "audit_orders"),
    }
    for f in _by_kind(facts, "edge"):
        assert f["props"]["predicate"] == "dependsOn"


def test_hourly_dag_with_statement_and_lshift():
    facts, _ = _parse("dag_inventory_sync.py")
    dags = _by_kind(facts, "airflow_dag")
    assert len(dags) == 1 and dags[0]["props"]["dag_id"] == "inventory_sync"
    assert dags[0]["props"]["schedule"] == "@hourly"
    tasks = {f["props"]["task_id"]: f for f in _by_kind(facts, "airflow_task")}
    assert set(tasks) == {"check_stock", "reorder"}
    edges = {(f["props"]["from"].rsplit("/", 1)[-1], f["props"]["to"].rsplit("/", 1)[-1]) for f in _by_kind(facts, "edge")}
    assert edges == {("reorder", "check_stock")}


def test_docstrings_comments_provenance_and_graph():
    for name in ("dag_orders_etl.py", "dag_inventory_sync.py"):
        facts, _ = _parse(name)
        assert facts, name
        for fact in facts:
            assert fact["props"].get("graph") == "urn:airflow", fact["id"]
            prov = fact["prov"]
            assert prov["file"].startswith("tests/fixtures/airflow/"), fact["id"]
            assert prov["line"] and prov["line"] > 0, fact["id"]
            assert prov["extraction_type"] == "direct", fact["id"]
    facts, _ = _parse("dag_orders_etl.py")
    dag = _by_kind(facts, "airflow_dag")[0]
    assert "ETL pipeline" in dag["props"]["docstring"]
    assert any("02:00" in c["text"] for c in dag["props"]["comments"])
