"""Every realtime channel a publisher names must be one of the four that exist.

`build_event_envelope` silently rewrites an unknown channel to `"notification"` (`envelope.py:17-18`), and round 190's
`test_realtime_fanout.py` records that as **"asserted as documented rather than blessed"** — the same honest framing round
194 used for the ACL's fail-open branches, **and round 224 showed where that framing can hide a real defect.**

So round 225 asked the round-224 question of it: *what reaches it?* **Nothing does.** All twelve
`push_realtime_event(channel=…)` call sites in `app/` pass a literal drawn from `CHANNELS`, so the rewrite is a fallback
rather than a behaviour — **and this test is what keeps it that way.**

**It also records a slip of mine while measuring it.** Grepping `channel=` for candidates also matched
`Notification(channel="inapp")` at `notification_service.py:41` and I read it as a typo. **It is the notifications table's
own delivery-channel column — a different vocabulary entirely, and a correct line.** A guard written against the wrong
vocabulary would have "fixed" it.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

APP = BACKEND / "app"
PUBLISHER = "push_realtime_event"


def _channel_arguments() -> list[tuple[str, int, str | None]]:
    """(file, line, literal-or-None) for every `channel=` keyword on a publisher call under `app/`."""
    found: list[tuple[str, int, str | None]] = []
    for path in sorted(p for p in APP.rglob("*.py") if "__pycache__" not in p.parts):
        source = path.read_text(encoding="utf-8", errors="replace")
        for node in ast.walk(ast.parse(source)):
            if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == PUBLISHER):
                continue
            for keyword in node.keywords:
                if keyword.arg != "channel":
                    continue
                value = keyword.value
                literal = value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else None
                found.append((path.relative_to(BACKEND).as_posix(), node.lineno, literal))
    return found


def test_every_published_channel_is_a_real_one():
    from app.realtime.envelope import CHANNELS

    calls = _channel_arguments()
    # A floor from the codebase's side: a scan that found almost nothing would mean the walk broke, not that the
    # publishers stopped naming channels.
    assert len(calls) >= 8, f"only {len(calls)} publisher call sites were found, so this guard is not seeing the code"

    offenders: list[str] = []
    for relative, line, literal in calls:
        if literal is None:
            offenders.append(f"{relative}:{line} passes a computed channel, which can silently become 'notification'")
        elif literal not in CHANNELS:
            offenders.append(f"{relative}:{line} passes {literal!r}, which is not one of {sorted(CHANNELS)}")

    assert offenders == [], (
        "**`build_event_envelope` rewrites an unknown channel to `notification` rather than failing**, so a channel that "
        "does not exist would be delivered to notification subscribers instead of raising. Name one of the four:\n  "
        + "\n  ".join(offenders)
    )


def test_the_silent_rewrite_is_still_there():
    """The fallback is deliberate defence; this test exists so that removing it is a decision, not an oversight."""
    from app.realtime import envelope

    source = (BACKEND / "app" / "realtime" / "envelope.py").read_text(encoding="utf-8")
    assert 'channel = "notification"' in source, (
        "`build_event_envelope` no longer rewrites an unknown channel. **If it now raises instead, that is a better "
        "behaviour and round 190's `test_realtime_fanout.py` must change with it** — do not let the two disagree"
    )
    assert "inapp" not in envelope.CHANNELS, (
        "**`inapp` is the notifications table's delivery channel, not a realtime channel.** If it was added here, one of "
        "the two vocabularies is being used for the other"
    )
