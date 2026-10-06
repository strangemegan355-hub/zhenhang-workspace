"""No view may render unescaped markup, and the guard proves it can fail.

Phase 4 names "渲染/编码缺陷" as something to remove. The encoding half is already guarded by the text-integrity test;
the rendering half was never checked at all. Measured across every `.tsx` and `.ts` under all three front-ends:

    dangerouslySetInnerHTML      0
    .innerHTML =                 0
    eval(                        0
    document.write(              0
    new Function(                0

Zero in every app, which means **a guard here pins a real invariant and needs no reviewed-exception list** — the
cleanest kind, and the opposite of the guards that pin open holes.

Three properties keep it from being decoration:

  * a **positive control** runs the same detector over a crafted string and must catch it, so a detector that silently
    stopped working fails the test instead of passing it;
  * the **floor is derived from the filesystem**, not a constant: the scan must have actually read the three apps and a
    plausible number of files, so a broken glob fails rather than vacuously passes;
  * it reports the **file and line** of any hit, so the failure says where to look.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
APPS = REPO / "apps"
SOURCE_SUFFIXES = (".ts", ".tsx")

HAZARDS: dict[str, re.Pattern[str]] = {
    "dangerouslySetInnerHTML": re.compile(r"dangerouslySetInnerHTML"),
    "innerHTML assignment": re.compile(r"\.innerHTML\s*="),
    "eval call": re.compile(r"(?<![\w.])eval\s*\("),
    "document.write": re.compile(r"document\s*\.\s*write\s*\("),
    "new Function": re.compile(r"new\s+Function\s*\("),
}


def _scan(text: str) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for label, pattern in HAZARDS.items():
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            hits.append((label, line_no, text.splitlines()[line_no - 1].strip()[:100]))
    return hits


def _sources() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for path in sorted(APPS.rglob("*")):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if any(part in {"node_modules", "dist", ".next", "build"} for part in path.parts):
            continue
        found.append((path, path.read_text(encoding="utf-8", errors="replace")))
    return found


def test_the_detector_catches_what_it_claims_to():
    """Without this, a detector that matches nothing would pass every other assertion in the file."""
    crafted = (
        'const a = <div dangerouslySetInnerHTML={{ __html: x }} />;\n'
        'el.innerHTML = userInput;\n'
        'eval("1");\n'
        'document.write("<b>");\n'
        'const f = new Function("return 1");\n'
    )
    caught = {label for label, _line, _text in _scan(crafted)}
    assert caught == set(HAZARDS), f"the detector missed: {sorted(set(HAZARDS) - caught)}"


def test_no_view_renders_unescaped_markup():
    sources = _sources()
    apps_seen = {path.relative_to(APPS).parts[0] for path, _text in sources}

    # The floor is the filesystem's, not a number I chose: all three apps must have been read, and a scan that read
    # almost nothing must fail rather than pass vacuously.
    expected_apps = {path.name for path in APPS.iterdir() if path.is_dir() and (path / "package.json").exists()}
    assert apps_seen == expected_apps, (
        f"the scan read {sorted(apps_seen)} but {sorted(expected_apps)} are the front-ends that exist; "
        "a missing app means the glob broke, not that the app is clean"
    )
    assert len(sources) > 50, f"the scan read only {len(sources)} sources, which is too few to mean anything"

    offenders = [
        f"{path.relative_to(REPO).as_posix()}:{line_no}  [{label}] {text}"
        for path, source in sources
        for label, line_no, text in _scan(source)
    ]
    assert offenders == [], (
        "a view renders unescaped markup or evaluates code. React escapes text by default; use that, or sanitise "
        "explicitly and add the site to this test's reasoning: " + repr(offenders)
    )
