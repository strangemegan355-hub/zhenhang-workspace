"""A number must say when it was measured, or it is not a number.

Round 167 stated the rule and applied it by hand; round 168 dated the last seven claims. **This makes the rule
mechanical**, in the shape this repository uses elsewhere: a detector, a vacuity floor taken from the filesystem, and a
positive control. **It needs no reviewed-exception list** — measured after round 168's edits, every numeric claim in the
places a reader looks carries a round marker nearby, and the test fails on the first one that does not.

The rule, precisely:

  * a **numeric claim** is a number attached to a countable thing (tests, modules, lines, endpoints, packages, ...);
  * it is **anchored** when a round reference or a date appears **within six lines**, because these docstrings wrap at
    roughly 110 characters and a claim and its date routinely fall on adjacent lines. **A window is the compromise
    between a single line, which failed on real text, and a whole block, which would let a claim borrow a distant
    round**; six lines is about one paragraph here;
  * **the repository's other numbers are records of what a round measured** — "round 136 measured 4 errors" — and they
    are anchored by construction, which is exactly why the rule works for both kinds. There is nothing to exempt.

Both directions are asserted by the control: a crafted undated claim must be reported, and a crafted dated one must not.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

TARGETS = [
    *(REPO / "scripts").glob("*.sh"),
    REPO / "README.md",
    *(REPO / "docs").glob("*.md"),
    *(REPO / "backend" / "tests").glob("*.py"),
    REPO / "docker-compose.yml",
    REPO / "docker-compose.prod.yml",
    REPO / ".github" / "workflows" / "ci.yml",
]

CLAIM = re.compile(
    r"\b(\d{1,4})\s+(tests?|test functions?|modules?|routes?|endpoints?|files?|lines?|services?|problems?|errors?|warnings?|packages?|tables?|pages?|blobs?)\b",
    re.IGNORECASE,
)
ANCHOR = re.compile(r"round \d+|\bmeasured\b|\bas of\b|\b20\d\d-\d\d-\d\d\b", re.IGNORECASE)
WINDOW = 6


def _unanchored(text: str) -> list[tuple[int, str]]:
    """Every numeric claim whose surrounding `WINDOW` lines carry neither a round reference nor a date."""
    lines = text.splitlines()
    found: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if not CLAIM.search(line):
            continue
        start = max(0, index - WINDOW)
        end = min(len(lines), index + WINDOW + 1)
        if ANCHOR.search("\n".join(lines[start:end])):
            continue
        found.append((index + 1, line.strip()[:104]))
    return found


def test_the_detector_reports_an_undated_claim_and_accepts_a_dated_one():
    """Without this a detector that matched nothing would pass the test below vacuously."""
    undated = "The suite holds 35 tests and nothing else follows here.\n"
    assert _unanchored(undated), "an undated claim was not reported"

    dated = "Round 167 measured that the suite holds 35 tests and nothing else follows here.\n"
    assert not _unanchored(dated), "a dated claim was reported"

    distant = "Round 167 measured something.\n" + "\n" * 20 + "The suite holds 35 tests.\n"
    assert _unanchored(distant), "a round 20 lines away anchored a claim it should not have"


def test_every_numeric_claim_says_when_it_was_measured():
    missing_targets = [path.relative_to(REPO).as_posix() for path in TARGETS if not path.is_file()]
    assert missing_targets == [], (
        f"these targets no longer exist, so the sweep would silently narrow: {missing_targets}"
    )

    # The floor is the filesystem's, not a constant: the sweep must have picked up the files a reader actually reads.
    # A first version of this asserted a hard-coded line total, which is the kind of constant this series rejects.
    present = {path.relative_to(REPO).as_posix() for path in TARGETS}
    for required in ("scripts/ci.sh", "README.md", "docker-compose.prod.yml", ".github/workflows/ci.yml"):
        assert required in present, f"{required} is not being scanned"
    assert any(name.startswith("backend/tests/") for name in present), "the test suite's own comments are not scanned"
    assert any(name.startswith("docs/") for name in present), "the documents are not scanned"

    scanned = 0
    offenders: list[str] = []
    for path in TARGETS:
        text = path.read_text(encoding="utf-8", errors="replace")
        scanned += len(text.splitlines())
        for line_number, snippet in _unanchored(text):
            offenders.append(f"{path.relative_to(REPO).as_posix()}:{line_number}  {snippet}")

    assert scanned > 0, "the sweep read nothing at all"
    assert offenders == [], (
        "these numbers claim something about the present without saying when it was measured. Add the round (or a "
        "date), or remove the number:\n  " + "\n  ".join(offenders)
    )
