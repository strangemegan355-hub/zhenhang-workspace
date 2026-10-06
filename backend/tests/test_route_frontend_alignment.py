"""The API surface and the front end must agree, in the direction that is a defect.

Round 107 measured this and was wrong twice, both times producing **every URL unmatched and every route
unreached**: `include_router` is called as an attribute (`api_router.include_router(...)`) rather than a bare
name, and the `/api/v1` prefix is applied on a second level, in `main.py:121`, over module-relative prefixes in
`router.py`. Both were caught by comparing against routes known to exist, which is why this file asserts controls
before it concludes anything — a parse that silently finds nothing looks exactly like a codebase with no routes.

Two directions, and only one is a defect:

* **every front-end URL must match a route.** A URL that does not is a 404 in production, and nothing else in
  this repository catches it — `tsc` is happy with a string, and the integration tests call the API directly.
* **routes no front-end URL reaches are listed, not condemned.** Scripts, tests and external integrations call
  the API too; the list exists so that a new one is noticed and a stale entry fails, which forces a look rather
  than a verdict.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Routes that must be found, so a broken extraction cannot pass by finding nothing.
CONTROLS = (
    ("GET", "/api/v1/accounting/entries"),
    ("GET", "/api/v1/work-orders/summary"),
    ("GET", "/api/v1/users/me"),
    ("POST", "/api/v1/auth/login"),
)

# Measured in round 107. A path appearing here is a question ("who calls this?"), not a defect.
UNREACHED_BY_THE_FRONT_END = {
    "/api/v1/accounting/procurement-payable-requests/by-entry/{entry_id}",
    "/api/v1/auth/refresh",
    "/api/v1/boms/{bom_id}/actions/transition",
    "/api/v1/configs",
    "/api/v1/configs/{config_id}",
    "/api/v1/customers/contacts/{contact_id}",
    "/api/v1/customers/followups/{followup_id}",
    "/api/v1/files/relations",
    "/api/v1/files/{file_id}/preview",
    "/api/v1/health/live",
    "/api/v1/health/metrics",
    "/api/v1/health/ready",
    "/api/v1/mes/equipment-signals",
    "/api/v1/mes/oee-snapshots",
    "/api/v1/quotes/events/replay-dead-letter",
    "/api/v1/realtime/replay",
    "/api/v1/realtime/stream",
    "/api/v1/realtime/ticket",
    "/api/v1/workflows/seed",
    "/api/v1/workflows/states",
    "/api/v1/workflows/transitions",
}

# `$Ellipsis` interpolations become a wildcard segment: a literal cannot say what they hold.
INTERPOLATION = re.compile(r"\$\{[^}]*\}")
URL_LITERAL = re.compile(r"[\"'`](/api/v1/[^\"'`]*)")


def _routes() -> set[tuple[str, str]]:
    import ast

    backend = REPO / "backend"
    settings_text = (backend / "app" / "config" / "settings.py").read_text(encoding="utf-8")
    outer = re.search(r'api_v1_prefix:\s*str\s*=\s*"([^"]+)"', settings_text).group(1)

    tree = ast.parse((backend / "app" / "api" / "v1" / "router.py").read_text(encoding="utf-8"))
    prefixes: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        called = node.func
        is_include = (isinstance(called, ast.Name) and called.id == "include_router") or (
            isinstance(called, ast.Attribute) and called.attr == "include_router"
        )
        if not is_include or not node.args:
            continue
        target = node.args[0]
        module = ""
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            module = target.value.id
        elif isinstance(target, ast.Name):
            module = target.id
        prefix = ""
        for keyword in node.keywords:
            if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant):
                prefix = str(keyword.value.value)
        if module:
            prefixes[module] = prefix

    methods = {"get", "post", "put", "patch", "delete", "head", "options"}
    routes: set[tuple[str, str]] = set()
    for path in sorted((backend / "app" / "api" / "v1" / "endpoints").glob("*.py")):
        if path.name.startswith("_"):
            continue
        prefix = outer + prefixes.get(path.stem, "")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                if not isinstance(decorator.func.value, ast.Name) or decorator.func.value.id != "router":
                    continue
                if decorator.func.attr not in methods or not decorator.args:
                    continue
                if isinstance(decorator.args[0], ast.Constant):
                    routes.add((decorator.func.attr.upper(), prefix + str(decorator.args[0].value)))
    return routes


def _frontend_urls() -> set[str]:
    found: set[str] = set()
    roots = (
        REPO / "apps" / "web-admin" / "src",
        REPO / "apps" / "workshop-terminal" / "src",
        REPO / "apps" / "mobile-app" / "src",
        REPO / "packages",
    )
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix not in {".ts", ".tsx", ".mts", ".js", ".jsx"} or not path.is_file():
                continue
            if any(part in {"node_modules", "dist", ".next"} for part in path.parts):
                continue
            for url in URL_LITERAL.findall(path.read_text(encoding="utf-8", errors="replace")):
                found.add(INTERPOLATION.sub("*", url.split("?")[0].split("#")[0]).rstrip("/"))
    return found


def _matches(url: str, routes: set[tuple[str, str]]) -> bool:
    wanted = [segment for segment in url.split("/") if segment]
    for _method, route in routes:
        parts = [segment for segment in route.split("/") if segment]
        if len(parts) != len(wanted):
            continue
        if all(
            actual == "*" or expected.startswith("{") or expected == actual
            for expected, actual in zip(parts, wanted, strict=True)
        ):
            return True
    return False


def test_the_route_extraction_finds_routes_that_exist():
    routes = _routes()
    assert len(routes) >= 200, f"only {len(routes)} routes were found, which is too few to be real"
    missing = [control for control in CONTROLS if control not in routes]
    assert not missing, (
        f"these routes exist in the code but were not extracted, so every verdict below is suspect: {missing}"
    )


def test_every_front_end_url_matches_a_route():
    routes = _routes()
    unmatched = sorted(url for url in _frontend_urls() if not _matches(url, routes))
    assert unmatched == [], (
        "the front end calls URLs the back end does not serve, which is a 404 in production:\n"
        + "\n".join(f"    {url}" for url in unmatched)
    )


def test_the_routes_no_front_end_url_reaches_are_the_reviewed_ones():
    routes = _routes()
    called = _frontend_urls()
    paths = {route for _, route in routes}
    reached = {route for route in paths if any(_matches(url, {("GET", route)}) for url in called)}
    unreached = paths - reached

    new = sorted(unreached - UNREACHED_BY_THE_FRONT_END)
    stale = sorted(UNREACHED_BY_THE_FRONT_END - unreached)
    assert not new, (
        "these routes are reached by no front-end URL and are not in the reviewed list. A script, a test or an "
        "external integration may legitimately call one, so add it with that reason:\n"
        + "\n".join(f"    {path}" for path in new)
    )
    assert not stale, (
        "these routes are in the reviewed list but a front-end URL now reaches them, so the list is out of date:\n"
        + "\n".join(f"    {path}" for path in stale)
    )
