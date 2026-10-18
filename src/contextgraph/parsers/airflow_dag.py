"""Airflow DAG extractor (PART1_PLAN Task 1.5, proposal §7.2 1.2).

Uses Python's built-in ``ast`` module — NOT tree-sitter-python. Extracts
DAG IDs, schedules, default args, operator tasks, and >> / << dependency
chains. Docstrings (ast) and comments (tokenize) are recorded for semantic
enrichment. Every fact carries an internal ``graph`` field ``"urn:airflow"``
(serialized by Task 1.7; files stay plain Turtle).

Edge convention: ``>>`` means left runs first, so the edge reads
``<downstream> dependsOn <upstream>`` (from=downstream task, to=upstream).
"""

from __future__ import annotations

import ast
import io
import tokenize

from .. import EXTRACTOR_NAME, EXTRACTOR_VERSION
from ..facts import make_fact, uri

METHOD = "python-ast"
GRAPH = "urn:airflow"


def _prov(ctx, line):
    return {
        "repository": ctx.repo_id,
        "file": ctx.artifact.relpath,
        "line": line,
        "xpath": None,
        "extractor": EXTRACTOR_NAME,
        "extractor_version": EXTRACTOR_VERSION,
        "method": METHOD,
        "extraction_type": "direct",
        "evidence": [],
    }


def _const(node):
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _str_dict(node):
    """Best-effort scalar dict for default_args; non-literals become None."""
    if not isinstance(node, ast.Dict):
        return None
    out = {}
    for k, v in zip(node.keys, node.values):
        key = _const(k)
        try:
            out[str(key)] = ast.literal_eval(v)
        except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
            out[str(key)] = None
    return out


def _func_name(func):
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def parse(path, ctx):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=path.name)
    facts: list = []
    candidates: list = []

    try:
        comments = [
            {"line": line, "text": text}
            for tok, text, (line, _), _, _ in tokenize.generate_tokens(io.StringIO(source).readline)
            if tok == tokenize.COMMENT
        ]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        comments = []
    module_doc = ast.get_docstring(tree) or ""

    # Module-level `NAME = {...}` dicts (e.g. default_args) for kwarg resolution.
    dict_assigns: dict[str, ast.Dict] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Dict)
        ):
            dict_assigns[node.targets[0].id] = node.value

    dag_vars: dict[str, str] = {}  # variable name -> dag_id
    dag_nodes: list = []  # (var/None, dag_id, schedule, default_args, lineno)

    for node in tree.body:
        found = _find_dag(node)
        if found:
            var, call = found
            dag_id = _dag_id(call)
            if dag_id:
                schedule = _kw_str(call, "schedule_interval") or _kw_str(call, "schedule") or ""
                default_args = None
                for kw in call.keywords:
                    if kw.arg == "default_args":
                        target = dict_assigns.get(kw.value.id) if isinstance(kw.value, ast.Name) else kw.value
                        default_args = _str_dict(target)
                dag_nodes.append((var, dag_id, schedule, default_args, node.lineno))
                if var:
                    dag_vars[var] = dag_id

    for var, dag_id, schedule, default_args, lineno in sorted(dag_nodes, key=lambda d: d[1]):
        facts.append(
            make_fact(
                "airflow_dag",
                uri("dag", dag_id),
                {
                    "dag_id": dag_id,
                    "schedule": schedule,
                    "default_args": default_args,
                    "docstring": module_doc,
                    "comments": comments,
                    "graph": GRAPH,
                },
                _prov(ctx, lineno),
            )
        )

    tasks: dict[str, dict] = {}  # task_id -> {operator, dag_id, lineno}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _func_name(node.func)
        if not name.endswith("Operator"):
            continue
        task_id = _kw_str(node, "task_id")
        if not task_id:
            continue
        dag_ref = _kw_name(node, "dag")
        dag_id = dag_vars.get(dag_ref, "") if dag_ref else (next(iter(sorted(dag_vars.values())), "") if len(dag_vars) == 1 else "")
        if not dag_id and dag_nodes:
            dag_id = sorted(d[1] for d in dag_nodes)[0]
        if task_id not in tasks:
            tasks[task_id] = {"operator": name, "dag_id": dag_id, "lineno": node.lineno}

    for task_id in sorted(tasks):
        info = tasks[task_id]
        facts.append(
            make_fact(
                "airflow_task",
                uri("task", info["dag_id"], task_id),
                {"dag": info["dag_id"], "task_id": task_id, "operator": info["operator"], "graph": GRAPH},
                _prov(ctx, info["lineno"]),
            )
        )

    edges: set[tuple[str, str, int]] = set()  # (downstream, upstream, lineno)
    for node in tree.body:
        for expr in _iter_chain_exprs(node):
            for down, up in _chain_pairs(expr, set(tasks)):
                edges.add((down, up, expr.lineno))
    for down, up, lineno in sorted(edges):
        dag_id = tasks[down]["dag_id"]
        facts.append(
            make_fact(
                "edge",
                uri("edge", "dependsOn", dag_id, down, up),
                {
                    "predicate": "dependsOn",
                    "from": uri("task", dag_id, down),
                    "to": uri("task", dag_id, up),
                    "via": "bitshift-chain",
                    "graph": GRAPH,
                },
                _prov(ctx, lineno),
            )
        )
    return facts, candidates


def _find_dag(node):
    """Return (var_name_or_None, Call) for DAG(...) at assign or with-item."""
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and _func_name(node.value.func) == "DAG":
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            return node.targets[0].id, node.value
        return None, node.value
    if isinstance(node, ast.With):
        for item in node.items:
            if isinstance(item.context_expr, ast.Call) and _func_name(item.context_expr.func) == "DAG":
                var = item.optional_vars.id if isinstance(item.optional_vars, ast.Name) else None
                return var, item.context_expr
    return None


def _dag_id(call):
    if call.args and isinstance(call.args[0], ast.Constant):
        return str(call.args[0].value)
    return _kw_str(call, "dag_id") or ""


def _kw_str(call, name):
    for kw in call.keywords:
        if kw.arg == name and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return ""


def _kw_name(call, name):
    for kw in call.keywords:
        if kw.arg == name and isinstance(kw.value, ast.Name):
            return kw.value.id
    return ""


def _iter_chain_exprs(node):
    """Yield BinOp >> / << expressions from Expr statements (incl. With bodies)."""
    bodies = [node]
    if isinstance(node, ast.With):
        bodies = list(node.body)
    for stmt in bodies:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.BinOp) and isinstance(stmt.value.op, (ast.RShift, ast.LShift)):
            yield stmt.value


def _names(node):
    """Task variable names referenced by a chain operand."""
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.List, ast.Tuple)):
        out: set[str] = set()
        for elt in node.elts:
            out |= _names(elt)
        return out
    return set()


def _chain_pairs(node, known):
    """Pairs (downstream, upstream) for a >> / << BinOp, incl. nested chains."""
    pairs: set[tuple[str, str]] = set()

    def sinks(n):
        if isinstance(n, ast.BinOp) and type(n.op) is type(node.op):
            return sinks(n.right)
        return _names(n) & known

    def sources(n):
        if isinstance(n, ast.BinOp) and type(n.op) is type(node.op):
            return sources(n.left)
        return _names(n) & known

    def visit(n):
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.RShift, ast.LShift)):
            if type(n.op) is type(node.op):
                visit(n.left)
                visit(n.right)
                if isinstance(node.op, ast.RShift):
                    for u in sinks(n.left):
                        for d in sources(n.right):
                            pairs.add((d, u))
                else:
                    for u in sinks(n.right):
                        for d in sources(n.left):
                            pairs.add((d, u))

    visit(node)
    # Filter to known tasks only (unknown names skipped deterministically).
    return {(d, u) for d, u in pairs if d in known and u in known}
