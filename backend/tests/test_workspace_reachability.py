"""Which workspace packages does anything depend on, and which four does nothing?

Round 158 measured reachability for the backend and round 172 for the unit suite's infrastructure. **The workspace itself
had never been measured**, and the manifest walk in round 175 found four packages named by no `dependencies` block and
invoked by no script:

    @zhenhang/file-center             6 code lines, 2 files
    @zhenhang/query-governance       16 code lines, 2 files
    @zhenhang/quote                   7 code lines, 2 files
    @zhenhang/workflow                1 code line,  2 files

**A fifth looked the same at first and is not: `@zhenhang/api-sdk` is invoked by the root script `sdk:generate`**
(`npm run generate -w @zhenhang/api-sdk`), which is what the test below asserts. **The deletion proposal has to account
for that — removing the package removes `sdk:generate` with it.**

**The manifest graph is the reliable layer, and this test pins it.** A first attempt also tried to detect usage by
scanning every file for the package's specifier; it reported **the same list for all six packages**, which proved the
detector wrong rather than the packages unused — so that claim is not made here. What the attempt did establish is worth
recording: **`query-policy-registry` (137 code lines) is referenced by `apps/mobile-app/vite.config.ts`**, so "no manifest
depends on it" is not the same as "unused".

The four are **recorded, not deleted**: removing packages is the pending decision, and `api-sdk` is the one already named
in that proposal.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKIP = {"node_modules", ".git", ".venv", "dist", ".next", "build", "__pycache__"}

# `@zhenhang/api-sdk` was briefly listed here and is **not**: the root script `sdk:generate` is
# `npm run generate -w @zhenhang/api-sdk`, so a script invokes it by name. **That is a fact the deletion proposal has to
# account for** — removing the package removes `sdk:generate` with it.
#
# The sizes below were measured in round 175.
UNREFERENCED_PACKAGES: dict[str, str] = {
    "@zhenhang/file-center": "6 code lines in 2 files; scaffolding from an earlier structure",
    "@zhenhang/query-governance": "16 code lines in 2 files; scaffolding",
    "@zhenhang/quote": "7 code lines in 2 files; scaffolding",
    "@zhenhang/workflow": "1 code line in 2 files; the smallest package in the workspace",
}


def _manifests() -> list[Path]:
    return [
        path
        for path in sorted(REPO.rglob("package.json"))
        if not any(part in SKIP for part in path.relative_to(REPO).parts)
    ]


def _packages() -> dict[str, Path]:
    packages: dict[str, Path] = {}
    for path in _manifests():
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        name = data.get("name")
        if name and path.parent != REPO:
            packages[name] = path.parent
    return packages


def _dependents(packages: dict[str, Path]) -> dict[str, list[str]]:
    dependents: dict[str, list[str]] = {}
    for path in _manifests():
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        owner = path.parent.relative_to(REPO).as_posix() or "<root>"
        for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            for name in (data.get(field) or {}):
                if name in packages:
                    dependents.setdefault(name, []).append(f"{owner} ({field})")
    return dependents


def test_the_walk_finds_the_workspace():
    packages = _packages()
    # The floor is the filesystem's: the three apps and the packages must all be present.
    assert len(packages) >= 25, f"only {len(packages)} workspace packages were found"
    for required in ("web-admin", "workshop-terminal", "mobile-app", "@zhenhang/query-hooks", "@zhenhang/ui"):
        assert required in packages, f"{required} is missing from the workspace walk"


def test_every_unreferenced_package_is_recorded():
    packages = _packages()
    dependents = _dependents(packages)
    root_scripts = "\n".join(json.loads((REPO / "package.json").read_text(encoding="utf-8")).get("scripts", {}).values())

    found = {
        name
        for name in packages
        if not dependents.get(name)
        # A root script can invoke a package by **path** rather than by name — `analyze:deps` is
        # `node packages/dependency-analyzer/src/cli.mjs` — so both forms count. Checking only the name flagged that
        # package, which is the live caller of the workspace's own architectural checker.
        and name not in root_scripts
        and f"packages/{name.split('/')[-1]}" not in root_scripts
        and not name.startswith(("web-admin", "workshop", "mobile"))
    }
    unreviewed = sorted(found - set(UNREFERENCED_PACKAGES))
    assert unreviewed == [], (
        "these workspace packages are depended on by nothing. If a package is dead, delete it with its last reference; "
        "if it is deliberately kept, add it here with what it contains:\n  " + "\n  ".join(unreviewed)
    )

    stale = sorted(set(UNREFERENCED_PACKAGES) - found)
    assert stale == [], (
        "these packages are recorded as unreferenced but something now depends on them, so the record is out of date:\n  "
        + "\n  ".join(stale)
    )


def test_the_recorded_packages_are_the_sizes_they_claim():
    """A recorded reason that says "6 code lines" must not survive the package growing into real code."""
    for name, reason in UNREFERENCED_PACKAGES.items():
        directory = REPO / "packages" / name.split("/")[-1]
        assert directory.is_dir(), f"{name} is recorded but {directory} does not exist"
        lines = sum(
            len(path.read_text(encoding="utf-8", errors="replace").splitlines())
            for path in directory.rglob("*")
            if path.is_file() and path.suffix in {".ts", ".tsx", ".mjs", ".js"}
            and not any(part in SKIP for part in path.parts)
        )
        assert lines <= 60, (
            f"{name} now holds {lines} code lines, so it is no longer scaffolding and the reason recorded for it "
            f"({reason!r}) needs revisiting"
        )


# Where each unreferenced package is still named **outside its own directory**, so a deletion knows what to clean. The
# lockfile lists every workspace package and is regenerated by `npm install`, so it is expected and is not listed.
EXPECTED_REMOVAL_SURFACE: dict[str, set[str]] = {
    "@zhenhang/file-center": set(),
    "@zhenhang/query-governance": set(),
    "@zhenhang/quote": set(),
    "@zhenhang/workflow": set(),
}


def _outside_mentions(name: str) -> set[str]:
    """Files naming the package **as a whole string**, which excludes `quote-builder` when looking for `quote`.

    Round 176's first attempt searched plain substrings and reported twenty files for `@zhenhang/quote`, most of them
    `@zhenhang/quote-builder` and `@zhenhang/quote-runtime` — **packages that are used.** A deletion driven by that list
    would have been told to clean entries belonging to live packages, so the search requires a boundary after the name.
    """
    directory = f"packages/{name.split('/')[-1]}"
    quoted = re.compile(rf"[\"']({re.escape(name)})[\"']")
    # The path form needs a boundary too: `packages/quote` is a prefix of `packages/quote-runtime`, which is a **live**
    # package, and a substring search reported `tsconfig.base.json` and `test_package_lint.py` for it.
    path_form = re.compile(rf"{re.escape(directory)}(?=[/\"'\s,\]]|$)")
    found: set[str] = set()
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or path.name == "package-lock.json":
            continue
        relative = path.relative_to(REPO).as_posix()
        if relative.startswith(directory + "/") or any(part in SKIP for part in path.parts):
            continue
        if path.suffix not in {".ts", ".tsx", ".mjs", ".js", ".json", ".sh", ".yml", ".yaml", ".md", ".py", ".mjs"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if quoted.search(text) or path_form.search(text):
            found.add(relative)
    return found


def test_the_removal_surface_of_each_unreferenced_package_is_recorded():
    """Both directions: a new mention of an unreferenced package is reported, and a stale record fails too."""
    for name, expected in EXPECTED_REMOVAL_SURFACE.items():
        actual = _outside_mentions(name)
        # This file names them all, by design.
        actual.discard(Path(__file__).resolve().relative_to(REPO).as_posix())
        assert actual == expected, (
            f"{name} is named outside its own directory in {sorted(actual)} but the record says {sorted(expected)}. "
            "A deletion has to clean exactly these; update the record with the change that creates or removes one."
        )

