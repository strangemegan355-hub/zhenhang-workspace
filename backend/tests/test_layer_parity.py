"""Layer parity, as enforced invariants rather than a one-off audit.

Three gaps this file makes impossible to ship silently, each of which was checked by hand first:

  * an endpoint module that exists but is never mounted in the router — the route would simply not
    exist, and neither tsc nor the suite would notice;
  * a hook domain file that is never re-exported from `packages/query-hooks/src/index.ts` — the
    hooks would be unreachable from every page;
  * a model whose table the migration chain never creates — the schema would not build.

The third compiles the chain to SQL, which needs no database and takes a couple of seconds. An
earlier hand check of the same property produced a false alarm because it grepped migration source
for `create_table('x'`, which the migrations wrap across lines; the generated DDL is the authority.
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
APP = BACKEND / "app"
ENDPOINTS = APP / "api" / "v1" / "endpoints"
ROUTER = APP / "api" / "v1" / "router.py"
HOOK_INDEX = REPO / "packages" / "query-hooks" / "src" / "index.ts"
HOOK_DOMAINS = REPO / "packages" / "query-hooks" / "src" / "domains"


def test_every_endpoint_module_is_mounted():
    modules = {path.stem for path in ENDPOINTS.glob("*.py") if path.stem != "__init__"}
    assert modules, "no endpoint modules found"
    router = ROUTER.read_text(encoding="utf-8")
    # The router lists its imports one per line inside a parenthesised import block.
    mounted = set(re.findall(r"^\s{4}(\w+),", router, re.M))
    assert modules - mounted == set(), (
        "these endpoint modules exist but the router never imports them, so their routes are not "
        f"served: {sorted(modules - mounted)}"
    )


def test_every_hook_domain_is_exported():
    files = {path.stem for path in HOOK_DOMAINS.glob("*.ts")} - {"keys"}
    assert files, "no hook domain files found"
    index = HOOK_INDEX.read_text(encoding="utf-8")
    exported = set(re.findall(r'export \* from "\./domains/([\w-]+)"', index))
    assert files - exported == set(), (
        f"these hook domains are never re-exported, so no page can import them: "
        f"{sorted(files - exported)}"
    )


def test_every_model_table_is_created_by_the_chain():
    tables: set[str] = set()
    for path in (APP / "models").glob("*.py"):
        if path.stem in {"__init__", "base", "associations"}:
            continue
        tables |= set(re.findall(r'__tablename__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8")))
    assert tables, "no model tables found"

    env = dict(os.environ)
    env["PYTHONPATH"] = str(BACKEND)
    env.setdefault("SECRET_KEY", "0123456789012345678901234567890123")
    env.setdefault("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/erp")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"the migration chain could not be compiled:\n{result.stderr[-2000:]}"
    created = set(re.findall(r"CREATE TABLE (\w+)", result.stdout))
    missing = sorted(table for table in tables if table not in created)
    assert missing == [], (
        "these model tables are never created by any migration, so a fresh database lacks them: "
        f"{missing}"
    )


# --- layer direction -----------------------------------------------------------------------------

DOMAIN_LAYER = APP / "domains"
LEGACY_LAYERS = (APP / "repositories", APP / "services")

# Every dependency today: the newer domain layer using the older layer's *public* surface. The
# migration exists to remove these, so the set may shrink — the test only fails when it grows.
LEGACY_EDGES: set[tuple[str, str]] = {
    ("app/domains/audit/__init__.py", "app.services.audit_service"),
    ("app/domains/audit/application/__init__.py", "app.services.audit_service"),
    ("app/domains/auth/__init__.py", "app.services.auth_service"),
    ("app/domains/auth/application/__init__.py", "app.services.auth_service"),
    ("app/domains/config/application/config_application_service.py", "app.services.audit_service"),
    ("app/domains/customer/__init__.py", "app.services.customer_service"),
    ("app/domains/customer/application/__init__.py", "app.services.customer_service"),
    ("app/domains/events/event_handlers/audit_event_handlers.py", "app.services.audit_service"),
    ("app/domains/events/event_handlers/quote_export_handlers.py", "app.services.quote_export_payload"),
    ("app/domains/events/event_handlers/quote_export_handlers.py", "app.services.quote_template_engine"),
    ("app/domains/file/application/file_application_service.py", "app.services.audit_service"),
    ("app/domains/machine/__init__.py", "app.services.machine_service"),
    ("app/domains/machine/application/__init__.py", "app.services.machine_service"),
    ("app/domains/quote/application/quote_application_service.py", "app.services.audit_service"),
    ("app/domains/quote/application/quote_application_service.py", "app.services.business_settings_service"),
    ("app/domains/quote/application/quote_application_service.py", "app.services.industrial_copilot"),
    ("app/domains/quote/application/quote_application_service.py", "app.services.product_pricing_service"),
    ("app/domains/quote/application/quote_application_service.py", "app.services.product_service"),
    ("app/domains/quote/application/quote_application_service.py", "app.services.quote_template_engine"),
    ("app/domains/quote/application/quote_application_service.py", "app.services.workflow_service"),
    ("app/domains/workflow/__init__.py", "app.services.workflow_service"),
    ("app/domains/workflow/application/__init__.py", "app.services.workflow_service"),
}

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(app\.(?:domains|repositories|services)[\w.]*)")


def _layer_imports(root: Path) -> set[tuple[str, str]]:
    """(file relative to backend, imported module) for every import of one of the layers."""
    found: set[tuple[str, str]] = set()
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(BACKEND).as_posix()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = IMPORT_RE.match(line)
            if match:
                found.add((relative, match.group(1)))
    return found


def test_the_domain_layer_never_imports_a_repository():
    """Repositories are the legacy layer's internals; services are its public surface."""
    offenders = sorted(
        f"{relative} imports {module}"
        for relative, module in _layer_imports(DOMAIN_LAYER)
        if module == "app.repositories" or module.startswith("app.repositories.")
    )
    assert offenders == [], (
        "the domain layer reached into the legacy layer's repositories; depend on a service instead: "
        f"{offenders}"
    )


def test_the_domain_layer_does_not_grow_new_legacy_dependencies():
    found = _layer_imports(DOMAIN_LAYER)
    new_edges = sorted(edge for edge in found if edge[1].startswith("app.services.") and edge not in LEGACY_EDGES)
    assert new_edges == [], (
        "the domain layer gained a dependency on the legacy layer. The migration moves the other way; "
        "if the dependency is deliberate, add it to LEGACY_EDGES with the reason: " + f"{new_edges}"
    )


# The reverse direction is real and was found by this gate's first run, not by the one-off script that
# preceded it: seven legacy services import from `app.domains.quote.*` or `app.domains.config.*`, so the
# migration is bidirectional and neither generation can be retired alone. These edges are pinned so the
# coupling cannot deepen; the set may only shrink.
REVERSE_EDGES: set[tuple[str, str]] = {
    ("app/services/approval_hub_service.py", "app.domains.quote.application"),
    ("app/services/approval_hub_service.py", "app.domains.quote.repositories"),
    ("app/services/business_settings_service.py", "app.domains.config.repositories"),
    ("app/services/dashboard_service.py", "app.domains.quote.policies.data_scope_policy"),
    ("app/services/dashboard_service.py", "app.domains.quote.repositories"),
    ("app/services/industrial_copilot.py", "app.domains.quote.repositories"),
    ("app/services/quote_export_payload.py", "app.domains.quote.repositories"),
    ("app/services/quote_option_service.py", "app.domains.quote.repositories"),
    ("app/services/quote_receivable_service.py", "app.domains.quote.repositories"),
}


def test_the_legacy_layer_imports_the_domain_layer_only_where_listed():
    """Pinned, because the intended direction is the other way and this coupling must not grow."""
    found: set[tuple[str, str]] = set()
    for root in LEGACY_LAYERS:
        found |= {
            (relative, module)
            for relative, module in _layer_imports(root)
            if module == "app.domains" or module.startswith("app.domains.")
        }
    new_edges = sorted(found - REVERSE_EDGES)
    assert new_edges == [], (
        "the legacy layer gained a dependency on the domain layer, which is the direction the "
        "migration is meant to remove. If it is deliberate, add it to REVERSE_EDGES with the reason: "
        f"{new_edges}"
    )
