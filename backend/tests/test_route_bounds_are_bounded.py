"""What bounds a list endpoint: `page_size` at the route, and the offset at the one chokepoint.

Round 227 extracted all **101** policy-shaped numeric defaults under `app/` and found **86 bounded, 15 not** — and the
split is not random:

* **all 86 bounded ones are at the HTTP layer**, every `page_size`/`limit` carrying `ge=1, le=100` or `le=200`;
* all 15 unbounded ones are internal methods, whose endpoints bound the value above them.

**But the first version of this guard demanded a `le` on `page` too and failed on the untouched tree** — which is how the
real shape emerged: **`page_size` bounds the rows returned; `page` bounds the offset**, and across the route modules **not
one `page` carried an upper bound (42 of them, measured in round 227).** `common_repository.paginate_query` computed
`.offset((page - 1) * page_size)` directly, so `?page=100000000&page_size=100` asked the database for `OFFSET 9999999900`
on every list endpoint.

**The offset is what costs, and `paginate_query` is the one place all 42 flow through**, so the ceiling lives there and the
route parameters stay as they are. These tests pin both halves so neither is mistaken for the other again.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ENDPOINTS = BACKEND / "app" / "api" / "v1" / "endpoints"
COMMON = BACKEND / "app" / "repositories" / "common_repository.py"

# Names that size the ROWS a route returns — these belong at the route, where a bad value is a 422.
ROWS = re.compile(r"^(page_size|per_page|limit|top)$", re.IGNORECASE)
WRAPPERS = {"Query", "Path", "Body"}


def _route_bounds() -> list[tuple[str, int, str, str]]:
    found: list[tuple[str, int, str, str]] = []
    for path in sorted(ENDPOINTS.rglob("*.py")):
        source = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(BACKEND).as_posix()
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            pairs = list(zip(node.args.args[-len(node.args.defaults) :], node.args.defaults)) if node.args.defaults else []
            pairs += list(zip(node.args.kwonlyargs, node.args.kw_defaults))
            for arg, default in pairs:
                if default is None or not ROWS.match(arg.arg):
                    continue
                if not (isinstance(default, ast.Call) and getattr(default.func, "id", "") in WRAPPERS):
                    continue
                bounds = ", ".join(f"{kw.arg}={ast.unparse(kw.value)}" for kw in default.keywords)
                found.append((relative, node.lineno, arg.arg, bounds or "no bound"))
    return found


def test_every_row_sizing_route_parameter_has_an_upper_bound():
    params = _route_bounds()
    # A floor from the codebase's side: round 227 measured 86 bounded parameters across the route modules, so a scan
    # finding a handful would mean the walk broke rather than that the API stopped taking page sizes.
    assert len(params) >= 40, f"only {len(params)} route parameters were found, so this guard is not seeing the routes"

    offenders = [f"{relative}:{line} {name} [{bounds}]" for relative, line, name, bounds in params if "le=" not in bounds]
    assert offenders == [], (
        "**these route parameters size the rows a response returns without an upper bound**, so a caller may ask for the "
        "whole table and the parameter is a name rather than a bound. Add `le=` to the `Query(...)`:\n  "
        + "\n  ".join(offenders)
    )


def test_the_row_bound_is_not_merely_present_but_reasonable():
    """`le=1000000` would satisfy the rule above and bound nothing worth bounding."""
    offenders: list[str] = []
    for relative, line, name, bounds in _route_bounds():
        for piece in bounds.split(", "):
            if piece.startswith("le="):
                try:
                    value = int(piece[3:])
                except ValueError:
                    continue
                if value > 1000:
                    offenders.append(f"{relative}:{line} {name} [{piece}]")

    assert offenders == [], (
        "these bounds are so large that they do not bound anything a database would notice:\n  " + "\n  ".join(offenders)
    )


def test_the_offset_is_capped_where_all_the_routes_flow_through():
    """`page` carries no route-level bound by design — **this is the bound**, and it has to stay."""
    source = COMMON.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source)

    offsets = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "offset"
    ]
    assert offsets, "`paginate_query` no longer sets an offset, so this guard has lost its subject"

    for call in offsets:
        rendered = ast.unparse(call.args[0])
        assert rendered.startswith("min("), (
            "**the offset is no longer capped**, so `?page=100000000&page_size=100` reaches the database as `OFFSET "
            f"9999999900` again — on every list endpoint. The expression is now: {rendered}"
        )
    assert "MAX_OFFSET" in source, (
        "the cap has no named constant, so a reader cannot see what the ceiling is or change it deliberately"
    )
