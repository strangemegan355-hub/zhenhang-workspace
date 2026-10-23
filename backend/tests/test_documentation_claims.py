"""Every component the documentation names must exist and be used by something.

Round 121 found `QuoteWorkbench` — named twice in `packages/GOVERNANCE.md` as the shipped quote UX — exported and
rendered nowhere: the "mock page" class, where a document promises a feature that is wired to nothing. This makes
that check standing, in the two directions it can fail:

* a name the docs use that **no file defines** — the documentation describes something that does not exist;
* a name that **is defined and used by nothing** — the round-121 case.

Names come from backticked PascalCase identifiers, which is how these documents name components. Comments are
stripped before matching, and **that is the point round 122 had to learn**: the note round 121 added — "nothing
renders `QuoteWorkbench`" — is itself a mention of the name, so a naive "is it used anywhere" check counted **the
explanation** as a user and reported nothing wrong.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKIP_PARTS = {"node_modules", ".next", "dist", ".venv", "site-packages", "__pycache__", ".git", "volumes", ".pytest_cache"}
CODE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs"}
# The documents that describe **what ships**. Round 170 widened this to every Markdown file and measured why that is
# wrong for *this* guard: eighteen names then reported as undefined came from six planning documents
# (`UI-Refactor-Plan.md`, `UI-Refactor-Backlog.md`, two UI baseline reviews, `UI-Component-Mapping.md` and the refactor
# brief), where a backticked PascalCase name is a **proposal**, not a claim that a component exists — `ChevronLeft` is a
# lucide icon, `PARTIAL` a status word, and `Dashboard`/`Customer`/`Project` are pages a plan intends to build.
# **The rule is sound for shipping documents and unsound for prospective ones, so the scope stays and the reason is
# recorded here rather than in a twenty-three entry exemption list.** The numeric-claims guard scans every document
# because its question — "when was this measured?" — applies to all of them.
DOC_GLOBS = (
    "packages/GOVERNANCE.md",
    "docs/*.md",
    "README.md",
    "apps/web-admin/README.md",
    "backend/README.md",
)
NAME = re.compile(r"`([A-Z][A-Za-z0-9]{3,})`")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT = re.compile(r"//[^\n]*")

# Backticked PascalCase names in the docs that are not code symbols. Each needs the reason it is not.
NOT_A_CODE_SYMBOL = {
    # the request of a migration step in the deployment document, not a component
    "Upgrade",
    # Round 183's README data-scope section names the SQL keyword and the HTTP verb it is describing, in backticks
    # because that is how this document quotes code. Neither is a component.
    "NULL",
    "DELETE",
    # KNOWN_ISSUES K-026: Pydantic schema in backend/app/schemas/quote.py — not a frontend export.
    "QuoteCreate",
}

# Components the docs name that exist and that nothing renders. Reviewed, with the consequence recorded.
DEFINED_BUT_UNRENDERED = {
    # quote-workbench.tsx (530 lines, measured in round 167), plus its only consumer use-undo-redo.ts; see packages/GOVERNANCE.md
    # for the correction and the choice between wiring and deleting it
    "QuoteWorkbench",
}
# Components the docs name that exist and that nothing renders. Reviewed, with the consequence recorded.
DEFINED_BUT_UNRENDERED = {
    # quote-workbench.tsx (530 lines, measured in round 167), plus its only consumer use-undo-redo.ts; see packages/GOVERNANCE.md
    # for the correction and the choice between wiring and deleting it
    "QuoteWorkbench",
    # Defined in packages/api-sdk and imported by nothing: that package's README is the only place these appear, and the
    # package is the one named in the pending deletion proposal. Round 170 found them when the scan reached that README.
    "LoginRequest",
    "LoginResponse",
    # UX-006 (2026-10-23): dashboard stopped rendering these; files kept pending a deletion pass.
    # Also recorded in test_frontend_reachability.REFERENCED_NOWHERE.
    "RecentFilesCard",
    "WorkflowProgressCard",
}


def _docs() -> list[Path]:
    found: list[Path] = []
    for pattern in DOC_GLOBS:
        found.extend(
            path
            for path in sorted(REPO.glob(pattern))
            # `SKIP_PARTS` matters now that the glob is `**/*.md`: a tool's own README is not a document of this
            # repository, and `.pytest_cache` writes one.
            if path.is_file() and not (SKIP_PARTS & set(path.relative_to(REPO).parts))
        )
    return found


def _code() -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or path.suffix not in CODE_SUFFIXES:
            continue
        if SKIP_PARTS & set(path.parts):
            continue
        texts[path.relative_to(REPO).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return texts


def _strip_comments(text: str) -> str:
    return LINE_COMMENT.sub("", BLOCK_COMMENT.sub("", text))


def _named_in_docs() -> set[str]:
    names: set[str] = set()
    for path in _docs():
        names.update(NAME.findall(path.read_text(encoding="utf-8", errors="replace")))
    return names


def test_the_scan_finds_the_documents_and_the_names():
    docs = _docs()
    names = _named_in_docs()
    # The floor is the filesystem's, not a constant: a first version asserted `len(docs) >= 5`, which the five
    # hand-listed documents satisfied on their own — so the check could not notice that twenty-two were missing.
    relative = {path.relative_to(REPO).as_posix() for path in docs}
    for required in ("README.md", "packages/GOVERNANCE.md", "backend/README.md", "apps/web-admin/README.md"):
        assert required in relative, f"{required} is not being scanned"
    assert any(name.startswith("docs/") for name in relative), "the documents under docs/ are not scanned"
    assert len(names) >= 5, f"only {len(names)} PascalCase names were found, which is too few to be real"
    assert "QuoteWorkbench" in names, "the name round 121 found must be among those the docs use"


def test_every_component_the_docs_name_exists_and_is_used():
    code = _code()
    stripped = {relative: _strip_comments(text) for relative, text in code.items()}
    assert len(code) >= 100, f"only {len(code)} code files were read, which is too few to be real"

    undefined: list[str] = []
    unrendered: list[str] = []
    for name in sorted(_named_in_docs()):
        if name in NOT_A_CODE_SYMBOL:
            continue
        definition = [
            relative
            for relative, text in code.items()
            if re.search(rf"export (?:function|const|type|class|interface) {re.escape(name)}\b", text)
        ]
        if not definition:
            undefined.append(name)
            continue
        users = [
            relative
            for relative, text in stripped.items()
            if relative not in definition
            and re.search(rf"(import[^\n]*\b{re.escape(name)}\b)|(<{re.escape(name)}[\s/>])", text)
        ]
        if not users and name not in DEFINED_BUT_UNRENDERED:
            unrendered.append(name)

    assert undefined == [], (
        "the documentation names these as components and no file defines them, so it describes something that "
        "does not exist. Fix the document, or record the name in NOT_A_CODE_SYMBOL with the reason:\n"
        + "\n".join(f"    {name}" for name in undefined)
    )
    assert unrendered == [], (
        "the documentation names these components, they exist, and nothing imports or renders them — the "
        "documentation promises a feature wired to nothing. Wire it, delete it, or record it in "
        "DEFINED_BUT_UNRENDERED with the consequence:\n" + "\n".join(f"    {name}" for name in unrendered)
    )
