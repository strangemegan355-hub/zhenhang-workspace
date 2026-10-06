"""The hook layer's URLs must exist in the API — the one edge of the eight layers nobody checked.

Alignment has been measured between endpoints and mounted routers, hooks and exported domain modules, models and the
migration chain (all in `test_layer_parity.py`), and pages and URLs (round 133). **Hook URLs against the API's actual
route table was the missing edge**, and the hook layer is named in the objective's eight layers.

Measured before writing this: the hook modules contain **108 distinct `/api/v1/...` literals**, and the only backend
file that mentions the hook package is `test_layer_parity.py`, which relates **module names**, not paths.

How a literal is matched:

  * an exact path matches its route;
  * a literal ending in `/` is a prefix concatenated with an id at the call site, so it matches a route that continues
    with a `{parameter}` segment — `/api/v1/machines/` matches `/api/v1/machines/{machine_id}`;
  * a literal containing a template (`${...}`) is normalised to `{}` and matched the same way.

Three properties keep it honest: a **positive control** (a fabricated URL no route serves must be reported), a floor
**derived from the filesystem** rather than a constant, and failures that name the **file and the literal**.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / "packages" / "query-hooks" / "src"

URL_LITERAL = re.compile(r"""["'`](/api/v1/[^"'`\s]*)""")
TEMPLATE_SEGMENT = re.compile(r"\$\{[^}]*\}|\{[^}]*\}")


def _normalise(url: str) -> str:
    """A URL with its template segments replaced, and any trailing slash kept for prefix matching."""
    cleaned = TEMPLATE_SEGMENT.sub("{}", url).split("?")[0].split("#")[0]
    return cleaned


def _hook_urls() -> list[tuple[str, str]]:
    """Every `/api/v1/...` literal in the hook layer, with the file it came from."""
    found: list[tuple[str, str]] = []
    for path in sorted(HOOKS.rglob("*.ts")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in URL_LITERAL.finditer(text):
            found.append((path.relative_to(REPO).as_posix(), _normalise(match.group(1))))
    return found


def _api_paths() -> set[str]:
    from app.main import app

    return {getattr(route, "path", "") for route in app.routes if getattr(route, "path", "").startswith("/api/v1")}


def _serves(literal: str, api_paths: set[str]) -> bool:
    if literal in api_paths:
        return True
    if literal.endswith("/"):
        return any(path.startswith(literal) and path != literal for path in api_paths)
    # A literal may itself carry a parameter the route spells differently, e.g. `{}` against `{quote_id}`.
    pattern = re.compile("^" + re.escape(literal).replace(re.escape("{}"), r"\{[^/]+\}") + "$")
    return any(pattern.match(path) for path in api_paths)


def test_the_matcher_catches_a_url_no_route_serves():
    """Without this, a matcher that answered "yes" to everything would pass the test below."""
    api_paths = _api_paths()
    assert _serves("/api/v1/machines/{machine_id}", api_paths), "an exact route should match"
    assert _serves("/api/v1/machines/", api_paths), "a trailing-slash prefix should match a parameterised route"
    assert not _serves("/api/v1/definitely-not-a-route-xyz", api_paths), "a fabricated URL matched something"


def test_every_hook_url_is_served_by_the_api():
    urls = _hook_urls()
    api_paths = _api_paths()

    # The floor is the filesystem's: the hook layer must have been read, and a scan that found almost nothing must
    # fail rather than pass vacuously.
    assert HOOKS.is_dir(), f"the hook layer is not where this test expects it: {HOOKS}"
    ts_files = list(HOOKS.rglob("*.ts"))
    assert len(ts_files) > 5, f"only {len(ts_files)} hook source files were read"
    assert len(urls) > 20, f"only {len(urls)} hook URLs were found, too few to mean anything"

    unmatched = sorted({f"{path}  {url}" for path, url in urls if not _serves(url, api_paths)})
    assert unmatched == [], (
        "the hook layer calls URLs the API does not serve. Either the route is missing, or the hook's path is wrong; "
        "a hook that 404s is invisible until a page uses it:\n  " + "\n  ".join(unmatched)
    )
