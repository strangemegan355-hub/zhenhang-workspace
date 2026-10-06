"""No tracked text file may carry encoding damage, and the three definitions of damage are exact.

Round 84 found one file genuinely damaged — zero CJK characters and 156 literal question marks where Chinese
belonged — and the skill recorded the lesson: a console decodes a child process's UTF-8 as GBK, so correct Chinese
looks broken on screen, and **counting CJK characters is not a test** because an em dash is outside the CJK block.
Only three things are damage:

1. bytes that **fail** UTF-8 decoding;
2. **U+FFFD** replacement characters;
3. a literal **`?` sandwiched between two CJK characters** — which cannot be TypeScript.

The third definition is narrow on purpose. A first attempt also flagged any string or template literal holding CJK
and a run of question marks, and the detector's first version, in round 84, reported **91 false positives across 43 files**: `??` (nullish coalescing),
`?.` (optional chaining) and template-literal boundaries are all legal beside Chinese. The file round 84 named now
holds 136 CJK characters and 51 question marks, **none of them damage**.

The damaged sample this test checks itself against is **composed at runtime**, so no file in the repository
contains one — the same rule the secret gate learned when its own positive control tripped it.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKIP_PARTS = {"node_modules", ".next", "dist", ".venv", "site-packages", "__pycache__", ".git", "volumes"}
TEXT_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".json", ".md", ".yml", ".yaml",
    ".sh", ".ps1", ".csv", ".sql", ".env",
}
# The one rule that cannot be TypeScript, so it needs no exception list.
CJK = "\u4e00-\u9fff"
SANDWICHED_QUESTION = re.compile(f"[{CJK}][?\\uFFFD]+[{CJK}]")


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    paths = []
    for relative in (rel for rel in result.stdout.split("\0") if rel.strip()):
        path = REPO / relative
        if path.suffix not in TEXT_SUFFIXES or not path.is_file():
            continue
        if SKIP_PARTS & set(path.parts):
            continue
        paths.append(path)
    return paths


def test_the_damage_detector_recognises_damage():
    """A detector that matches nothing would pass every file; build a damaged string and require a match."""
    # The character is assembled from its code point so this file holds no literal damage itself.
    damaged = "\u62a5\u4ef7" + "?" * 3 + "\u5355"
    assert SANDWICHED_QUESTION.search(damaged), "the rule must match a question run between two CJK characters"
    healthy = "\u62a5\u4ef7\u5355 ?? fallback"
    assert not SANDWICHED_QUESTION.search(healthy), "the rule must not match nullish coalescing beside Chinese"


def test_no_tracked_text_file_carries_encoding_damage():
    paths = _tracked_files()
    # A filter that found nothing would make every verdict below meaningless.
    assert len(paths) >= 200, f"only {len(paths)} text files were found, which is too few to be real"

    undecodable: list[str] = []
    replacement: list[str] = []
    sandwiched: list[str] = []
    for path in paths:
        relative = path.relative_to(REPO).as_posix()
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            undecodable.append(f"{relative}: {exc}")
            continue
        if "\ufffd" in text:
            replacement.append(relative)
        for match in SANDWICHED_QUESTION.finditer(text):
            line = text[: match.start()].count("\n") + 1
            sandwiched.append(f"{relative}:{line}")

    assert undecodable == [], "these files are not valid UTF-8, so their text is damaged:\n" + "\n".join(
        f"    {entry}" for entry in undecodable
    )
    assert replacement == [], "these files contain U+FFFD replacement characters:\n" + "\n".join(
        f"    {entry}" for entry in replacement
    )
    assert sandwiched == [], (
        "these files have a literal `?` between two CJK characters, which is encoding damage rather than code:\n"
        + "\n".join(f"    {entry}" for entry in sandwiched)
    )
