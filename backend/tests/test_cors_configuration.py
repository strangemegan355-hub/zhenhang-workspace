"""CORS is configured safely, and nothing asserted it until now.

Round 203 measured the backend's security surfaces against the test suite and found three that are **controlled but
unguarded**. CORS was the sharpest: `app/main.py` mounts `CORSMiddleware` and **no test pins what it allows**.

Reading it, the configuration is already correct and fail-safe:

* `app/config/settings.py` — `cors_origins: list[str] = Field(default_factory=list)`, so a deployment that forgets the
  environment variable **allows no origin at all** rather than defaulting to permissive;
* `app/main.py` passes that setting through with `allow_credentials=True`, `allow_methods=["*"]` and `allow_headers=["*"]`.

**The property worth pinning is the combination, not the list**: `allow_credentials=True` together with a wildcard origin
is the classic CORS misconfiguration, and it is invisible in a diff that only looks at one of the two lines. This asserts
the three facts that make the current state safe, so a later edit has to change one of them deliberately.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

MAIN = BACKEND / "app" / "main.py"


def _cors_call() -> ast.Call:
    """The `app.add_middleware(CORSMiddleware, ...)` call, located by parsing rather than by matching text."""
    tree = ast.parse(MAIN.read_text(encoding="utf-8", errors="replace"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name != "add_middleware":
            continue
        if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "CORSMiddleware":
            return node
    raise AssertionError("app/main.py no longer mounts CORSMiddleware; this guard has lost its subject")


def test_the_cors_origins_default_is_empty():
    """The safe default: forgetting the environment variable must not open the API to every origin."""
    from app.config.settings import Settings

    field = Settings.model_fields["cors_origins"]
    factory = field.default_factory
    assert factory is not None, "cors_origins has no default_factory, so a forgotten variable may default permissively"
    assert factory() == [], f"cors_origins now defaults to {factory()!r}, which is not the safe empty default"


def test_credentials_are_never_combined_with_a_wildcard_origin():
    call = _cors_call()
    keywords = {kw.arg: kw.value for kw in call.keywords}

    credentials = keywords.get("allow_credentials")
    assert isinstance(credentials, ast.Constant) and credentials.value is True, (
        "allow_credentials is no longer a literal True, so this guard cannot reason about it — read the new form and "
        "update this test deliberately"
    )

    origins = keywords.get("allow_origins")
    is_wildcard = (
        isinstance(origins, ast.List)
        and any(isinstance(elt, ast.Constant) and elt.value == "*" for elt in origins.elts)
    ) or (isinstance(origins, ast.Constant) and origins.value == "*")

    assert not is_wildcard, (
        "CORSMiddleware is mounted with allow_credentials=True and a wildcard origin. Browsers reject that combination, "
        "and where they do not it exposes credentialed requests to any site. Use `settings.cors_origins`."
    )


def test_the_origins_come_from_configuration_rather_than_a_literal():
    call = _cors_call()
    origins = {kw.arg: kw.value for kw in call.keywords}.get("allow_origins")
    assert origins is not None, "allow_origins is gone from the CORSMiddleware call"
    rendered = ast.unparse(origins) if hasattr(ast, "unparse") else ""
    assert "settings" in rendered or isinstance(origins, ast.Name), (
        f"allow_origins is no longer read from settings (found {rendered!r}); a literal list here cannot be changed per "
        "deployment"
    )
