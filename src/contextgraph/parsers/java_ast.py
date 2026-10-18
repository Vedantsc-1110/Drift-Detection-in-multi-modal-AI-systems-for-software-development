"""AST extractor: classes/methods/calls from .java and .groovy (PART1_PLAN Task 1.4).

Uses tree-sitter + tree-sitter-java for BOTH suffixes. Constraint (verified
by probe): Groovy sources must use semicolon statement terminators for a
clean parse — bare-newline Groovy yields ERROR nodes under the Java grammar
(Groovy semicolons are optional in the language, so fixtures comply).
Bare-newline real-world scripts are a documented Task 1.9 coverage risk.
Does NOT use tree-sitter-python here (Task 1.5 uses stdlib ast instead).

Standalone in Task 1.4: emits direct facts with file + line provenance.
Pipeline wiring (scanner roles for .java/.groovy) lands in Task 1.8/1.9 so
the locked order-only metrics stay untouched until integration.
"""

from __future__ import annotations

from .. import EXTRACTOR_NAME, EXTRACTOR_VERSION
from ..facts import make_fact, uri

METHOD = "tree-sitter-java"

_parser = None


def _get_parser():
    global _parser
    if _parser is None:
        from tree_sitter import Language, Parser
        import tree_sitter_java

        _parser = Parser(Language(tree_sitter_java.language()))
    return _parser


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


def _text(source: bytes, node) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _line(node) -> int:
    return int(node.start_point.row) + 1


def parse_source(path, ctx):
    """Parse one .java/.groovy file; return (facts, candidates)."""
    source = path.read_bytes()
    tree = _get_parser().parse(source)
    facts = []
    candidates: list = []
    _walk(tree.root_node, source, ctx, facts, current_class="", current_method="")
    return facts, candidates


def _walk(node, source: bytes, ctx, facts: list, current_class: str, current_method: str):
    ntype = node.type
    if ntype == "import_declaration":
        for child in node.named_children:
            if child.type in ("scoped_identifier", "identifier", "asterisk"):
                facts.append(
                    make_fact(
                        "java_import",
                        uri("import", ctx.component_name, _text(source, child).replace(".", "/")),
                        {"import": _text(source, child), "file_class": current_class},
                        _prov(ctx, _line(node)),
                    )
                )
                break
        return
    if ntype == "class_declaration":
        name = ""
        for child in node.named_children:
            if child.type == "identifier":
                name = _text(source, child)
                break
        if name:
            facts.append(
                make_fact("java_class", uri("class", ctx.component_name, name), {"name": name}, _prov(ctx, _line(node)))
            )
        for child in node.named_children:
            _walk(child, source, ctx, facts, current_class=name or current_class, current_method="")
        return
    if ntype == "method_declaration":
        name = ""
        return_type = ""
        params: list = []
        children = node.named_children
        for i, child in enumerate(children):
            if child.type == "identifier":
                name = _text(source, child)
                # Return type = the type node immediately before the name.
                if i > 0 and children[i - 1].type not in ("modifiers", "formal_parameters", "block"):
                    return_type = _text(source, children[i - 1])
                break
        for child in children:
            if child.type == "formal_parameters":
                for param in child.named_children:
                    if param.type == "formal_parameter":
                        pname, ptype = "", ""
                        for sub in param.named_children:
                            if sub.type == "identifier":
                                pname = _text(source, sub)
                            else:
                                ptype = _text(source, sub)
                        params.append({"name": pname, "type": ptype})
        if name:
            facts.append(
                make_fact(
                    "java_method",
                    uri("method", ctx.component_name, current_class, name),
                    {"class": current_class, "name": name, "params": params, "return_type": return_type},
                    _prov(ctx, _line(node)),
                )
            )
        for child in children:
            _walk(child, source, ctx, facts, current_class=current_class, current_method=name or current_method)
        return
    if ntype == "method_invocation":
        named = node.named_children
        ids = [_text(source, c) for c in named if c.type == "identifier"]
        if named and named[0].type == "field_access":
            receiver, callee = _text(source, named[0]), (ids[0] if ids else "")
        elif len(ids) >= 2:
            receiver, callee = ids[0], ids[1]
        elif len(ids) == 1:
            receiver, callee = "", ids[0]
        else:
            receiver, callee = "", ""
        if callee and current_method:
            facts.append(
                make_fact(
                    "java_call",
                    uri("call", ctx.component_name, current_class, current_method, callee, str(_line(node))),
                    {
                        "caller_class": current_class,
                        "caller_method": current_method,
                        "callee": callee,
                        "receiver": receiver,
                    },
                    _prov(ctx, _line(node)),
                )
            )
        for child in node.named_children:
            _walk(child, source, ctx, facts, current_class=current_class, current_method=current_method)
        return
    for child in node.named_children:
        _walk(child, source, ctx, facts, current_class=current_class, current_method=current_method)


def parse(path, ctx):
    return parse_source(path, ctx)
