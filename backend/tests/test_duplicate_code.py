"""No function may be defined in more than one file with an identical body.

Round 124 removed one instance: `owner_scope_user_id` existed as **three byte-identical copies** under
`app/domains/{config,file,quote}/policies/`, and `app/core/data_scope.py`'s own `scope_predicate` docstring names
that helper as one half of a historical contradiction — two implementations of one four-valued enum that disagreed
about DEPARTMENT scope. **A fix applied in three places is a fix that can diverge three ways**, which is how that
contradiction arose the first time.

The class is mechanical, so it is checked mechanically: same function name, same body with comments, docstrings and
whitespace normalised away, different files. Bodies are compared **after** docstrings are stripped, so copies that
differ only in prose still count as one implementation.

The five entries below were read in round 124 and are all genuine duplication rather than deliberate divergence;
each carries what it is. **They are recorded, not silently accepted** — a new one fails here, and so does an entry
that no longer applies.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
SKIP_PARTS = {"__pycache__", ".venv"}
LINE_COMMENT = re.compile(r"#[^\n]*")
DUPLICATE = re.compile(r"\s+")

# (function name, number of files, what the copies are). The body hash is deliberately not pinned: a change to one
# copy must fail this test rather than rotate a hash quietly.
#
# `_page` was here as ten identical copies plus a diverged eleventh in `admin_service`; round 125 moved the
# implementation to `app/schemas/common.py` and made all eleven services import it as `_page`, so the entry is gone.
# `uptime_seconds` was here as two copies, one in `app/core/enterprise_metrics.py` (the live surface, feeding
# `/health/metrics`) and one in `app/core/monitoring.py`; round 128 showed the second was a dead class — nothing
# anywhere referenced `RuntimeMetrics` or its `runtime_metrics` singleton, and `main.py` imports that module for
# `now_perf()` alone — so the class was deleted rather than consolidated.
# `commit_session` and `_money` were here as two copies each; round 129 moved them to `app/repositories/base.py` and
# `app/core/money.py` and made the four modules import them, so both entries are gone. `_money` mattered most: two
# money rounders that agree today are two that can disagree later, and the signature comparison added this round is
# what makes a silent change to either one fail.
# `save_request` stays pinned: its three copies differ in the annotated model type and its body performs a
# **transaction boundary** (`flush`, `commit`, `refresh`) inside a repository, so consolidating it is a decision
# about who owns the unit of work rather than a move.
REVIEWED_DUPLICATES: dict[str, tuple[int, str]] = {
    "save_request": (3, "request-number persistence, identical in three repositories"),
}


def signature_of(node: ast.AST, source: str) -> str:
    """The `def` line with type annotations removed, parameter names and defaults kept.

    The body alone is not enough: two functions with the same body and **different parameters** would compare equal,
    and a different default is a real difference — a rounding or pagination helper could disagree that way. Type
    annotations are stripped precisely because they do not change what runs, which is why `save_request`'s three
    copies over three model types are still one implementation.
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ""
    arguments = node.args
    names = [argument.arg for argument in arguments.posonlyargs + arguments.args + arguments.kwonlyargs]
    if arguments.vararg:
        names.append("*" + arguments.vararg.arg)
    if arguments.kwarg:
        names.append("**" + arguments.kwarg.arg)
    defaults = [ast.unparse(default) for default in arguments.defaults]
    kw_defaults = [
        f"{argument.arg}={ast.unparse(default)}"
        for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=False)
        if default is not None
    ]
    return f"{node.name}({','.join(names)}) defaults={defaults}{kw_defaults}"


def normalise(node: ast.AST, source: str) -> str:
    """The signature plus the body as one line, without docstring, comments or whitespace."""
    body = list(getattr(node, "body", []))
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    signature = signature_of(node, source)
    if not body:
        return signature
    start = min(item.lineno for item in body)
    end = max(getattr(item, "end_lineno", item.lineno) for item in body)
    snippet = "\n".join(source.splitlines()[start - 1 : end])
    return f"{signature} => {DUPLICATE.sub(' ', LINE_COMMENT.sub('', snippet)).strip()}"


def duplicate_bodies() -> dict[str, set[str]]:
    """name -> the files that define a body shared with at least one other file."""
    seen: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for path in sorted(APP.rglob("*.py")):
        if SKIP_PARTS & set(path.parts):
            continue
        relative = path.relative_to(BACKEND.parent).as_posix()
        source = path.read_text(encoding="utf-8", errors="replace")
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            text = normalise(node, source)
            if not text:
                continue
            seen[node.name][hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]].add(relative)
    return {
        name: {relative for files in by_body.values() if len(files) > 1 for relative in files}
        for name, by_body in seen.items()
        if any(len(files) > 1 for files in by_body.values())
    }


def test_the_normaliser_separates_the_two_known_cases():
    same_a = ast.parse('def f():\n    """One explanation."""\n    return 1 + 1\n')
    same_b = ast.parse('def f():\n    """Another explanation."""\n    # a comment\n    return 1 + 1\n')
    other = ast.parse("def f():\n    return 2 + 2\n")
    body_a = normalise(same_a.body[0], 'def f():\n    """One explanation."""\n    return 1 + 1\n')
    body_b = normalise(same_b.body[0], 'def f():\n    """Another explanation."""\n    # a comment\n    return 1 + 1\n')
    body_c = normalise(other.body[0], "def f():\n    return 2 + 2\n")
    assert body_a and body_a == body_b, "copies differing only in prose and comments must compare equal"
    assert body_a != body_c, "functions with different bodies must not compare equal"


def test_no_function_is_defined_identically_in_two_files():
    found = duplicate_bodies()
    # A scan that found nothing would make both verdicts meaningless.
    assert len(found) >= 1, f"only {len(found)} duplicated names were found, which is too few to be real"

    new = sorted(name for name in found if name not in REVIEWED_DUPLICATES)
    stale = sorted(name for name in REVIEWED_DUPLICATES if name not in found)
    assert not new, (
        "these functions are defined with identical bodies in more than one file, so a fix applied to one copy "
        "will not reach the others. Extract the shared implementation, or record it in REVIEWED_DUPLICATES with "
        "what the copies are:\n" + "\n".join(f"    {name}: {sorted(found[name])}" for name in new)
    )
    assert not stale, (
        "these names are recorded as duplicated across files and are not any more, so the record is out of date:\n"
        + "\n".join(f"    {name}" for name in stale)
    )
    wrong_count = sorted(
        name for name in REVIEWED_DUPLICATES if len(found.get(name, set())) != REVIEWED_DUPLICATES[name][0]
    )
    assert not wrong_count, (
        "these duplicates changed how many files they appear in, so the copies have diverged or spread:\n"
        + "\n".join(
            f"    {name}: recorded {REVIEWED_DUPLICATES[name][0]}, found {len(found[name])}" for name in wrong_count
        )
    )
