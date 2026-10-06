"""Single-quote lookups must pass the data-scope predicate.

`repo.get_quote(db, quote_id, predicate=None)` is the seam, and its docstring explains why it works this way:
an out-of-scope row is simply absent, so the caller answers 404 instead of 403 and never confirms that the quote
exists. Three callers passed it; two did not.

* `summarize_quote_for_copilot`, behind `GET /ai/copilot/quote-summary` and (a second route found only by
  sweeping the call sites) `GET /quotes/{quote_id}/copilot-summary`. Both routes discarded the user before
  calling it, and the analysis helper references no user or scope at all, so any holder of
  `business:quote:read` could read any quote's cost and profit analysis.
* `transition_quote_state`, behind `POST /quotes/{id}/actions/transition`. It receives `current_user` and
  records them as `approver_id`, but fetched the quote unscoped.

This pins the predicate being passed, without a database: the repository function is replaced by a recorder and
a transient `User` supplies the scope. A transient ORM object's `roles` collection is a plain empty list, which
is the detail round 75 learned the hard way — touching an unloaded collection on a *persistent* object raises.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-32-characters")

from app.domains.quote.application import quote_application_service as svc  # noqa: E402
from app.models.user import User  # noqa: E402


class _Recorder:
    """Stands in for the quote repository and remembers the predicate it was given."""

    def __init__(self) -> None:
        self.predicates: list[object] = []

    async def get_quote(self, db, quote_id, predicate=None):
        self.predicates.append(predicate)
        return None  # the 404 path, so nothing past the lookup runs


def _user() -> User:
    # Transient, never added to a session: `roles` is then an ordinary empty list, which resolves to SELF
    # scope. The primary key must be a real UUID — a transient row's id is None, and the scope predicate builds
    # a UUID from it, so leaving it unset fails inside uuid.py rather than in the assertion below.
    return User(id=uuid4(), username="scope-probe", hashed_password="not-used")


@pytest.mark.asyncio
async def test_copilot_summary_applies_the_callers_scope(monkeypatch):
    recorder = _Recorder()
    monkeypatch.setattr(svc.repo, "get_quote", recorder.get_quote)

    with pytest.raises(HTTPException) as raised:
        await svc.summarize_quote_for_copilot(None, uuid4(), _user())

    assert raised.value.status_code == 404, "an absent (or out-of-scope) quote must answer 404"
    assert len(recorder.predicates) == 1, "the lookup must run exactly once"
    assert recorder.predicates[0] is not None, (
        "summarize_quote_for_copilot fetched the quote without the data-scope predicate, so any holder of "
        "business:quote:read could read any quote's cost and profit analysis"
    )


@pytest.mark.asyncio
async def test_transition_applies_the_callers_scope(monkeypatch):
    recorder = _Recorder()
    monkeypatch.setattr(svc.repo, "get_quote", recorder.get_quote)

    with pytest.raises(HTTPException) as raised:
        await svc.transition_quote_state(None, uuid4(), "approve", None, _user())

    assert raised.value.status_code == 404
    assert len(recorder.predicates) == 1, "the lookup must run exactly once"
    assert recorder.predicates[0] is not None, (
        "transition_quote_state fetched the quote without the data-scope predicate, so any holder of "
        "business:quote:approve could transition any quote"
    )


# Every remaining entry point that loads a quote by id, so the sweep in round 86 stays closed. Each is called
# with a recorder in place of the repository and must pass a predicate; an absent quote then answers 404.
ENTRY_POINTS = [
    ("create_quote_version", lambda s, q, u: s.create_quote_version(None, q, [], u)),
    ("list_quote_versions", lambda s, q, u: s.list_quote_versions(None, q, u)),
    ("list_quote_approvals", lambda s, q, u: s.list_quote_approvals(None, q, u)),
    ("create_export_task", lambda s, q, u: s.create_export_task(None, q, "xlsx", u)),
    ("update_customer_quote", lambda s, q, u: s.update_customer_quote(None, q, {}, u)),
]


@pytest.mark.parametrize(("name", "call"), ENTRY_POINTS, ids=[name for name, _ in ENTRY_POINTS])
@pytest.mark.asyncio
async def test_every_quote_entry_point_applies_the_scope(monkeypatch, name, call):
    recorder = _Recorder()
    monkeypatch.setattr(svc.repo, "get_quote", recorder.get_quote)

    with pytest.raises(HTTPException) as raised:
        await call(svc, uuid4(), _user())

    assert raised.value.status_code == 404
    assert len(recorder.predicates) == 1, f"{name} must look the quote up exactly once"
    assert recorder.predicates[0] is not None, (
        f"{name} fetched the quote without the data-scope predicate, so it read or wrote a quote outside the "
        "caller's scope"
    )


@pytest.mark.asyncio
async def test_option_update_applies_the_scope(monkeypatch):
    from app.domains.quote.application import quote_option_service as opt

    recorder = _Recorder()
    monkeypatch.setattr(opt.repo, "get_quote", recorder.get_quote)

    with pytest.raises(ValueError):
        await opt.update_quote_item_options(None, uuid4(), uuid4(), [], _user())

    assert len(recorder.predicates) == 1
    assert recorder.predicates[0] is not None, (
        "update_quote_item_options fetched the quote without the data-scope predicate"
    )
