"""The README must state the data scope honestly — what is enforced, and what is only preparation.

Round 183 measured the README and found **no data-scope section at all**: its headings went from 集成测试 straight to
Windows 便捷脚本 and 生产环境注意. A reader therefore learned nothing about the one security property phase 3 built, and
the tenant dimension — which is **preparation, not isolation** — was described only inside
`docs/ENTERPRISE_DEPLOYMENT.md`'s 多租户准备 section and asserted only by `test_tenant_boundary.py`.

That measurement also established why the tenant wording needs its own guard: **nine of roughly eighty tables carry a
`tenant_id` column, only `sys_users` is stamped, every business row is NULL, and the realtime predicate is
`tenant_id = :tenant OR tenant_id IS NULL` — so with today's data it admits everything.** A sentence claiming isolation
would be false, and it is the kind of false sentence a later refactor can introduce without touching any code.

This pins the section in both directions: it must exist and name the enforced faces, and it must not claim isolation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
README = REPO / "README.md"
HEADING = "## 数据范围与租户"

# The four faces whose enforcement is proven by an integration test, plus the realtime channel.
REQUIRED_FACTS = (
    "test_data_scope_end_to_end.py",
    "test_realtime_acl.py",
    "404",
)

# Wording that would assert isolation the code does not provide. Round 170's rule applies here inversely: this is the
# place to catch an overclaim, because the phrase is what a reader acts on.
FORBIDDEN_CLAIMS = (
    "多租户已实现",
    "租户已隔离",
    "跨租户已隔离",
    "tenant isolation is implemented",
    "tenants are isolated",
)

# And the section must name the state plainly.
REQUIRED_STATEMENTS = ("未实现隔离", "准备", "NULL")


def _section() -> str:
    text = README.read_text(encoding="utf-8", errors="replace")
    assert HEADING in text, (
        f"the README has no {HEADING!r} section. Round 183 measured that it had none, and a reader then cannot tell that "
        "the department scope is enforced while the tenant dimension is only preparation"
    )
    start = text.index(HEADING)
    # The section runs to the next top-level heading.
    rest = text[start + len(HEADING) :]
    match = re.search(r"^## ", rest, re.MULTILINE)
    return rest[: match.start()] if match else rest


def test_the_readme_states_the_enforced_data_scope():
    section = _section()
    missing = [fact for fact in REQUIRED_FACTS if fact not in section]
    assert missing == [], (
        f"the data-scope section does not name {missing}. Each face it claims is enforced by a test file; naming them is "
        "what lets a reader check the claim rather than trust it"
    )


def test_the_readme_does_not_claim_tenant_isolation():
    section = _section()
    claimed = [phrase for phrase in FORBIDDEN_CLAIMS if phrase in section]
    assert claimed == [], (
        f"the README claims {claimed}, but the code does not provide it: only `sys_users` is stamped, every business row "
        "has a NULL tenant, and the realtime predicate admits NULL rows. Correct the sentence or implement the isolation"
    )
    missing = [phrase for phrase in REQUIRED_STATEMENTS if phrase not in section]
    assert missing == [], (
        f"the section no longer says {missing}; the tenant state has to be stated, not left to inference"
    )


def test_the_files_the_section_points_at_exist():
    section = _section()
    referenced = sorted(set(re.findall(r"(?:integration_tests|tests)/[\w./-]+\.py", section)))
    assert referenced, "the section points at no test file, so none of its claims is checkable"
    absent = [relative for relative in referenced if not (REPO / "backend" / relative).is_file()]
    assert absent == [], f"the section points at files that do not exist: {absent}"
