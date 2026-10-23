"""The copilot's "similar quotes" panels must respect the caller's data scope.

Round 196 found that `build_industrial_copilot_analysis` applies no scope when it looks up the quotes the copilot
displays as *similar*: `_similar_projects` and `_similar_quotes` select up to five other quotes by machine or customer and
return their **quote number, title and total amount**. The endpoint that reaches them requires only
`business:quote:read`, which the department-scoped trial account holds, so a scoped caller could read other departments'
commercial figures through the panel.

**The outer lookup is scoped, and that is worth stating precisely** — `summarize_quote_for_copilot` calls
`repo.get_quote(db, quote_id, predicate=scope_predicate(Quote, current_user))` and answers 404 when the row is out of
scope. So the hole is narrower than "the copilot is unscoped": **the panels hanging off an authorised quote were the
unscoped part.** This test pins the corrected behaviour at that boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

pytestmark = pytest.mark.asyncio

MARKER = "it-copilot-scope"


async def _seed_two_departments_with_quotes():
    """Two departments, each with a quote on the SAME machine — the condition the panel selects on."""
    from app.db.session import AsyncSessionLocal
    from app.models.customer import Customer
    from app.models.department import Department
    from app.models.machine import Machine
    from app.models.quote import Quote
    from app.models.user import User
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # `customer_id` is NOT NULL on quotes; any existing customer serves, since the panel under test selects by
        # machine and the customer is only carried along.
        customer_id = (await session.execute(select(Customer.id).limit(1))).scalar_one()
        machine = Machine(code=f"{MARKER}-M", machine_code=f"{MARKER}-M", name="shared machine", is_deleted=False)
        mine = Department(code=f"{MARKER}-A", name="copilot A")
        theirs = Department(code=f"{MARKER}-B", name="copilot B")
        session.add_all([machine, mine, theirs])
        await session.flush()

        owner = User(username=f"{MARKER}-owner", email=f"{MARKER}@example.invalid", hashed_password="x", department_id=mine.id)
        rival = User(username=f"{MARKER}-rival", email=f"{MARKER}-r@example.invalid", hashed_password="x", department_id=theirs.id)
        session.add_all([owner, rival])
        await session.flush()

        my_quote = Quote(quote_no=f"{MARKER}-MINE", title="mine", customer_id=customer_id, machine_id=machine.id, created_by=owner.id, is_deleted=False)
        rival_quote = Quote(quote_no=f"{MARKER}-THEIRS", title="theirs", customer_id=customer_id, machine_id=machine.id, created_by=rival.id, is_deleted=False)
        session.add_all([my_quote, rival_quote])
        await session.commit()
        return my_quote.id, rival_quote.id, owner.id, mine.id, theirs.id


async def _teardown():
    from app.db.session import AsyncSessionLocal
    from app.models.department import Department
    from app.models.machine import Machine
    from app.models.quote import Quote
    from app.models.user import User
    from sqlalchemy import delete

    async with AsyncSessionLocal() as session:
        await session.execute(delete(Quote).where(Quote.quote_no.like(f"{MARKER}%")))
        await session.execute(delete(User).where(User.username.like(f"{MARKER}%")))
        await session.execute(delete(Machine).where(Machine.code.like(f"{MARKER}%")))
        await session.execute(delete(Department).where(Department.code.like(f"{MARKER}%")))
        await session.commit()


async def test_similar_panels_exclude_quotes_outside_the_callers_scope():
    from app.db.session import AsyncSessionLocal
    from app.domains.quote.application.industrial_copilot import build_industrial_copilot_analysis
    from app.models.user import User
    from sqlalchemy import select

    _, rival_quote_id, owner_id, mine_id, _ = await _seed_two_departments_with_quotes()
    try:
        async with AsyncSessionLocal() as session:
            owner = (await session.execute(select(User).where(User.id == owner_id))).scalar_one()
            analysis = await build_industrial_copilot_analysis(
                session,
                (await _my_quote_id()),
                compare_fn=lambda *_: {},
                current_user=owner,
            )
    finally:
        await _teardown()

    rendered = repr(analysis)
    assert f"{MARKER}-THEIRS" not in rendered, (
        "the copilot listed another department's quote as similar. The panel returns quote number, title and total "
        "amount, so this discloses commercial figures the caller's data scope excludes"
    )
    assert str(rival_quote_id) not in rendered, "the copilot exposed another department's quote id"
    assert mine_id is not None


async def _my_quote_id():
    from app.db.session import AsyncSessionLocal
    from app.models.quote import Quote
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        return (await session.execute(select(Quote.id).where(Quote.quote_no == f"{MARKER}-MINE"))).scalar_one()
