"""Every policy number in the settings surface must carry a bound.

Round 167's rule — *"a number either says when it was measured, or it is not a number"* — had been applied to this record's
own claims for sixty rounds and **never to the constants in the code.** Round 226 measured them:

* **`app/` contains exactly one module-level numeric constant**, `ABORT_INCOMPLETE_MULTIPART_DAYS = 7` — and a test names
  it. **The numbers live in `settings.py` instead, which is the right place.**
* Of its **ten** numeric fields, **eight carried an explicit bound** — including `realtime_ticket_expire_seconds`
  (`ge=30, le=3600`).
* **The two that did not were `access_token_expire_minutes` and `refresh_token_expire_minutes`** — **the token lifetimes
  themselves.** An operator could set the access-token lifetime to ten years or to zero and **nothing would fail either
  way**, while `le=1440` is the point past which re-login stops being a revocation path.

The bound is the whole reason a policy number is trustworthy: **it says which values are wrong, not merely which value was
chosen.** This test requires one on every numeric field, with an explicit exemption list for anything that genuinely needs
none.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SETTINGS = BACKEND / "app" / "config" / "settings.py"

# A numeric setting that deliberately has no bound must say why here. **An unbound policy number cannot be answered with
# "why is it that value?"** — so the default is to bound it.
EXEMPT: dict[str, str] = {}

BOUND_KEYWORDS = {"ge", "gt", "le", "lt"}
NUMERIC = ("int", "float")


def _numeric_fields() -> list[tuple[str, int, bool]]:
    """(name, line, has_a_bound) for every `int`/`float` field on `Settings`."""
    tree = ast.parse(SETTINGS.read_text(encoding="utf-8", errors="replace"))
    found: list[tuple[str, int, bool]] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)):
            continue
        annotation = ast.unparse(node.annotation)
        if annotation not in NUMERIC:
            continue
        bounded = isinstance(node.value, ast.Call) and any(kw.arg in BOUND_KEYWORDS for kw in node.value.keywords)
        found.append((node.target.id, node.lineno, bounded))
    return found


def test_every_numeric_setting_carries_a_bound():
    fields = _numeric_fields()
    # A floor from the file's side: a scan that found nothing would mean the walk broke, not that the policy numbers
    # stopped existing.
    assert len(fields) >= 8, f"only {len(fields)} numeric settings were found, so this guard is not seeing the file"

    offenders = [
        f"{name} (line {line})"
        for name, line, bounded in fields
        if not bounded and name not in EXEMPT
    ]
    assert offenders == [], (
        "**these policy numbers accept any value at all**, so nothing fails when one is set to zero or to ten years, and "
        "no reader can say which values are wrong. Give each a `ge`/`le` bound in its `Field` — or add it to `EXEMPT` "
        "with the reason it needs none:\n  " + "\n  ".join(offenders)
    )


def test_the_token_lifetimes_are_bounded_to_something_sane():
    """The two that were unbounded are the ones whose value decides how long a stolen token works."""
    fields = {name: bounded for name, _, bounded in _numeric_fields()}
    for name in ("access_token_expire_minutes", "refresh_token_expire_minutes"):
        assert name in fields, f"{name} is gone, so this guard has lost its subject"
        assert fields[name], (
            f"{name} is unbounded again. **This is the number that decides how long a stolen token works** — an "
            "operator setting it to ten years, or to zero, must meet a validation error rather than silence."
        )


def test_the_exemptions_say_why():
    """The same convention as round 209: an entry in a reviewed list carries its reason."""
    offenders = [name for name, reason in EXEMPT.items() if len(reason.strip()) < 20]
    assert offenders == [], (
        "these exemptions do not say why the field needs no bound, which is how a reviewed list becomes a list of "
        f"names: {offenders}"
    )
