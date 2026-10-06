"""Every page must either read data or say why it does not.

The eight layers end at "页面", and phase 4 asks for mock pages to be **eliminated**. Measured on 2026-02-05
(rather than assumed): of the **41** `page.tsx` files under `apps/web-admin/src/app`, **36 call a hook**, **2 are pure
redirects**, one renders the login panel, one is the root landing page, and one is a deliberate "not available here"
page. **There is no mock page** — the last one renders an `EmptyState` that says 在线配置中心尚未开放 and points at the
deployment document, which is honest rather than fabricated.

The guard therefore pins the **rule**, not the count — a count in a test drifts, which round 154 proved twice over:

  * a page with **no hook call and no redirect** must appear in `REVIEWED_SILENT_PAGES` with the reason it is silent;
  * an entry in that list whose page **does** call a hook or redirect must be removed, because a stale exemption hides
    a page that has since changed;
  * the number of pages read comes from the filesystem, so a broken glob fails instead of passing vacuously.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APP_DIR = REPO / "apps" / "web-admin" / "src" / "app"

HOOK_CALL = re.compile(r"\buse[A-Z]\w*(?:Query|Mutation)\s*[(<]")
REDIRECT = re.compile(r"\bredirect\s*\(|\brouter\.(?:push|replace)\s*\(")

# Pages that neither read data nor redirect, each with the reason it is silent. Both directions are asserted: a page
# missing from this list fails, and an entry here whose page now reads data or redirects also fails.
REVIEWED_SILENT_PAGES: dict[str, str] = {
    "app/(admin)/(platform)/settings/page.tsx": (
        "renders an EmptyState saying the online configuration centre is not open, and points at "
        "docs/ENTERPRISE_DEPLOYMENT.md; the real configuration page is business-settings, which calls two hooks"
    ),
    "app/login/page.tsx": (
        "renders <LoginFormPanel>, which owns the login request; the page itself is composition"
    ),
    "app/page.tsx": (
        "the root landing page: navigation links only, no data of its own"
    ),
}


def _relative(path: Path) -> str:
    return path.relative_to(REPO / "apps" / "web-admin" / "src").as_posix()


def _pages() -> list[tuple[str, str]]:
    return [(_relative(path), path.read_text(encoding="utf-8", errors="replace")) for path in sorted(APP_DIR.rglob("page.tsx"))]


def test_a_page_reads_data_or_is_a_reviewed_exception():
    pages = _pages()

    # The floor is the filesystem's: the app directory must exist and hold pages, so a broken glob fails.
    assert APP_DIR.is_dir(), f"the admin app directory is not where this test expects it: {APP_DIR}"
    assert len(pages) > 20, f"only {len(pages)} pages were read, too few to mean anything"

    silent = {
        relative
        for relative, text in pages
        if not HOOK_CALL.search(text) and not REDIRECT.search(text)
    }
    unexpected = sorted(silent - set(REVIEWED_SILENT_PAGES))
    assert unexpected == [], (
        "these pages neither read data nor redirect. If a page is a mock or a placeholder, it should not ship; if it "
        "is deliberate, add it to REVIEWED_SILENT_PAGES with the reason:\n  " + "\n  ".join(unexpected)
    )

    stale = sorted(set(REVIEWED_SILENT_PAGES) - silent)
    assert stale == [], (
        "these entries are exempted as silent but their pages now read data or redirect, so the exemption is hiding a "
        "change; remove them:\n  " + "\n  ".join(stale)
    )


def test_every_reviewed_exception_still_exists():
    """A file renamed away must fail here, not silently shrink the exception list."""
    missing = sorted(name for name in REVIEWED_SILENT_PAGES if not (REPO / "apps" / "web-admin" / "src" / name).is_file())
    assert missing == [], f"REVIEWED_SILENT_PAGES names pages that no longer exist: {missing}"
