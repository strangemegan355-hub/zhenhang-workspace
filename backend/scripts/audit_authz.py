"""Static authorization audit for the Zhenhang ERP backend.

Loads the FastAPI app in-process (no database needed) and extracts, for every
route, the permission codes actually enforced by its dependency tree. Permission
codes live inside `require_permissions(...)` / `require_any_permission(...)`
closures, so they are read from `Dependant.call.__closure__` rather than guessed
from source text.

The catalogue of record is not "every code literal in the repo": it is the set of
codes that the seeding scripts actually create rows for, extracted with `ast` from
`_ensure_permission(...)` arguments and `Permission(...)` calls. A code required by
a route but absent from that set can never be granted to a non-superuser, so the
route is a permanent 403 for every ordinary role.

Usage:  python audit_authz.py [--backend DIR] [--out FILE]
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import Counter, defaultdict

# Permission codes in this repo are colon-separated lowercase segments. Both shapes
# occur: two-segment ("dashboard:view") and three-segment ("business:quote:read"), so
# the pattern must accept two or more segments rather than exactly three.
CODE_RE = re.compile(r"^[a-z][a-z0-9_]*(?::[a-z][a-z0-9_]*)+$")
AUTH_MARKERS = ("get_current", "require_")

# Only these two scripts can grant a code to a NON-superuser role:
#   * setup_trial_users.py builds the seven trial roles from TRIAL_ROLE_DEFS;
#   * bootstrap_admin.py creates system:user:read and the superuser (which bypasses
#     every permission check, so its own grants do not gate anything).
# seed_demo_quote.py and import_initial_master_data.py attach permissions to the admin
# role, i.e. to a superuser, so they cannot make an ordinary role pass a check.
TRIAL_CATALOGUE_FILES = ("scripts/setup_trial_users.py", "scripts/bootstrap_admin.py")
TRIAL_ASSIGNMENT = "TRIAL_ROLE_DEFS"


def extract_seeded_codes(backend: str) -> tuple[dict[str, list[str]], list[str]]:
    """Return {code: [sources]} for every code a non-superuser role can actually hold.

    Extraction is structural, not textual, because a permission tuple is
    (code, name, resource, action) and the resource ("business:quote") looks like a
    shorter code. Matching every colon-separated literal would therefore pull resource
    names into the catalogue as well; only element 0 of each permission tuple is a code.
    """
    seeded: dict[str, list[str]] = defaultdict(list)
    scanned: list[str] = []

    trial = os.path.join(backend, "scripts/setup_trial_users.py")
    if os.path.isfile(trial):
        scanned.append("scripts/setup_trial_users.py")
        tree = ast.parse(open(trial, encoding="utf-8").read(), filename=trial)
        for node in ast.walk(tree):
            if not isinstance(node, ast.AnnAssign):
                continue
            if not (isinstance(node.target, ast.Name) and node.target.id == TRIAL_ASSIGNMENT):
                continue
            for role in node.value.elts:  # (role_code, role_name, data_scope, [perm tuples])
                permissions = role.elts[3]
                for permission in permissions.elts:
                    code = permission.elts[0]
                    if isinstance(code, ast.Constant) and isinstance(code.value, str):
                        seeded[code.value].append("TRIAL_ROLE_DEFS")

    bootstrap = os.path.join(backend, "scripts/bootstrap_admin.py")
    if os.path.isfile(bootstrap):
        scanned.append("scripts/bootstrap_admin.py")
        tree = ast.parse(open(bootstrap, encoding="utf-8").read(), filename=bootstrap)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Permission":
                for keyword in node.keywords:
                    if keyword.arg == "code" and isinstance(keyword.value, ast.Constant):
                        if isinstance(keyword.value.value, str):
                            seeded[keyword.value.value].append("bootstrap_admin.py")

    return seeded, scanned


def extract_policy_forbidden(backend: str) -> dict[str, list[str]]:
    """Return {code: [sources]} for codes the project forbids trial roles to hold.

    `scripts/verify_permissions.py` defines FORBIDDEN_FOR_TRIAL and asserts that no
    non-superuser trial account holds any of those codes. A route requiring one of them
    is therefore reachable only by the superuser BY POLICY, and reporting it as a defect
    would contradict the project's own gate. Reading the set from the script keeps this
    audit and that gate in agreement instead of hard-coding a copy here.
    """
    forbidden: dict[str, list[str]] = defaultdict(list)
    path = os.path.join(backend, "scripts/verify_permissions.py")
    if not os.path.isfile(path):
        return forbidden
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "FORBIDDEN_FOR_TRIAL" not in names:
            continue
        # The value is `frozenset({...})`, so walk the whole subtree instead of reading
        # `elts` off the assignment value. This set holds permission codes only, so every
        # colon-separated literal inside it is a code.
        for inner in ast.walk(node.value):
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                if CODE_RE.match(inner.value):
                    forbidden[inner.value].append("FORBIDDEN_FOR_TRIAL")
    return forbidden


def closure_tuples(call) -> list[tuple[str, ...]]:
    """Return string-tuples captured in a callable's closure."""
    found: list[tuple[str, ...]] = []
    for cell in getattr(call, "__closure__", None) or ():
        try:
            value = cell.cell_contents
        except ValueError:
            continue
        if isinstance(value, tuple) and value and all(isinstance(item, str) for item in value):
            found.append(value)
    return found


def walk(dependant, acc: list[tuple[str, str, tuple[str, ...]]]) -> None:
    """Record every dependency, including code-less ones such as the auth guard."""
    call = dependant.call
    qualname = getattr(call, "__qualname__", None) or getattr(call, "__name__", "") or repr(call)
    found = closure_tuples(call)
    if found:
        for codes in found:
            acc.append((qualname, "any" if "require_any_permission" in qualname else "all", codes))
    else:
        acc.append((qualname, "auth", ()))
    for sub in dependant.dependencies:
        walk(sub, acc)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=os.environ.get("ERP_BACKEND", os.getcwd()))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    backend = os.path.abspath(args.backend)
    if backend not in sys.path:
        sys.path.insert(0, backend)

    os.environ.setdefault("SECRET_KEY", "0123456789012345678901234567890123")
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://erp:erp@127.0.0.1:5432/erp_db")
    os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")

    from fastapi.routing import APIRoute

    from app.main import app

    routes = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        acc: list[tuple[str, str, tuple[str, ...]]] = []
        walk(route.dependant, acc)
        all_of: set[str] = set()
        any_of: set[str] = set()
        auth_required = False
        for qualname, kind, codes in acc:
            if kind == "any":
                any_of.update(codes)
            elif kind == "all":
                all_of.update(codes)
            if any(marker in qualname for marker in AUTH_MARKERS) or "require_permissions" in qualname:
                auth_required = True
        routes.append(
            {
                "methods": sorted(route.methods - {"HEAD", "OPTIONS"}),
                "path": route.path,
                "name": route.name,
                "endpoint": route.endpoint.__qualname__,
                "module": route.endpoint.__module__,
                "all_of": sorted(all_of),
                "any_of": sorted(any_of),
                "auth_required": auth_required,
            }
        )

    seeded, scanned = extract_seeded_codes(backend)
    used: set[str] = set()
    for route in routes:
        used.update(route["all_of"])
        used.update(route["any_of"])

    unprotected = [r for r in routes if not r["all_of"] and not r["any_of"]]
    public = [r for r in unprotected if not r["auth_required"]]
    auth_only = [r for r in unprotected if r["auth_required"]]

    forbidden = extract_policy_forbidden(backend)
    missing: dict[str, list[str]] = defaultdict(list)
    for route in routes:
        for code in route["all_of"] + route["any_of"]:
            if code not in seeded:
                missing[code].append(f"{'/'.join(route['methods'])} {route['path']}")

    missing_by_policy = {code: targets for code, targets in missing.items() if code in forbidden}
    missing_defects = {code: targets for code, targets in missing.items() if code not in forbidden}

    report = {
        "backend": backend,
        "route_count": len(routes),
        "used_code_count": len(used),
        "seeded_code_count": len(seeded),
        "seeder_files_scanned": scanned,
        "policy_forbidden_codes": sorted(forbidden),
        "routes": routes,
        "unprotected_routes": unprotected,
        "public_routes": public,
        "auth_only_routes": auth_only,
        "codes_required_but_not_seeded": {code: sorted(targets) for code, targets in sorted(missing.items())},
        "codes_unreachable_by_policy": {code: sorted(targets) for code, targets in sorted(missing_by_policy.items())},
        "codes_unreachable_defect": {code: sorted(targets) for code, targets in sorted(missing_defects.items())},
        "seeded_codes_never_required": sorted(set(seeded) - used),
    }

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "authz-audit.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(f"backend                     : {backend}")
    print(f"routes                      : {len(routes)}")
    print(f"seeded permission codes     : {len(seeded)}  (from {len(scanned)} seeder scripts)")
    print(f"codes required by routes    : {len(used)}")
    print(f"routes with no permission   : {len(unprotected)}  (public={len(public)}, auth-only={len(auth_only)})")
    print(f"policy-forbidden codes      : {len(forbidden)}  (superuser-only by project policy)")
    print(f"unreachable BY DEFECT       : {len(missing_defects)}   <-- actionable")
    print(f"unreachable BY POLICY       : {len(missing_by_policy)}   <-- intentional")
    print()

    print("== public routes (no auth, no permission) ==")
    for r in public:
        print(f"   {'/'.join(r['methods']):12} {r['path']:50} {r['endpoint']}")
    print()
    print("== auth-only routes (logged in, no specific permission) ==")
    for r in auth_only:
        print(f"   {'/'.join(r['methods']):12} {r['path']:50} {r['endpoint']}")
    print()

    print("== ACTIONABLE: codes required by routes that no provisioned role can hold ==")
    if not missing_defects:
        print("   none")
    for code in sorted(missing_defects):
        print(f"   {code}   ({len(missing_defects[code])} route(s))")
        for target in sorted(missing_defects[code])[:4]:
            print(f"        {target}")
    print()

    print("== INTENTIONAL: codes unreachable because verify_permissions.py forbids them for trial roles ==")
    if not missing_by_policy:
        print("   none")
    for code in sorted(missing_by_policy):
        print(f"   {code}   ({len(missing_by_policy[code])} route(s))")
    print()

    print(f"== seeded codes no route requires: {len(report['seeded_codes_never_required'])} ==")
    for code in report["seeded_codes_never_required"]:
        print(f"   {code}")
    print()

    by_module: Counter[str] = Counter(r["module"].replace("app.api.v1.endpoints.", "") for r in routes)
    print("== routes per module ==")
    for module, count in sorted(by_module.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"   {count:3}  {module}")

    print()
    print(f"full JSON report: {out}")
    print()
    if missing_defects:
        print(f"RESULT: FAIL — {len(missing_defects)} permission code(s) unreachable by every provisioned role")
        return 1
    print("RESULT: PASS — every code a route requires is either granted to a role or forbidden by policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
