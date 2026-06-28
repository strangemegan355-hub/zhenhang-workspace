from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accounting_entry import AccountingEntry
from app.models.accounting_entry_line import AccountingEntryLine
from app.models.accounting_settlement import AccountingSettlement
from app.models.customer import Customer
from app.models.customer_ledger_account import CustomerLedgerAccount

_ENTRY_PREFIX = {
    "receivable": "AR",
    "payable": "AP",
    "receipt": "RC",
    "payment": "PY",
    "revenue": "IN",
    "expense": "EX",
}


async def count_entries(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(AccountingEntry).where(AccountingEntry.is_deleted.is_(False))
    )
    return int(result.scalar_one())


async def count_entry_no_prefix(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(AccountingEntry).where(
        AccountingEntry.entry_no.like(f"{prefix}%"),
        AccountingEntry.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())


async def generate_entry_no(db: AsyncSession, entry_kind: str) -> str:
    code = _ENTRY_PREFIX.get(entry_kind, "AE")
    prefix = f"{code}-{date.today().strftime('%Y%m%d')}-"
    count = await count_entry_no_prefix(db, prefix)
    return f"{prefix}{count + 1:03d}"


async def get_entry(db: AsyncSession, entry_id: UUID) -> AccountingEntry | None:
    result = await db.execute(
        select(AccountingEntry)
        .where(AccountingEntry.id == entry_id, AccountingEntry.is_deleted.is_(False))
        .options(selectinload(AccountingEntry.lines))
    )
    return result.scalar_one_or_none()


async def create_entry(db: AsyncSession, data: dict) -> AccountingEntry:
    obj = AccountingEntry(**data)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def add_entry(db: AsyncSession, data: dict) -> AccountingEntry:
    """Insert entry without committing (for multi-step writes)."""
    obj = AccountingEntry(**data)
    db.add(obj)
    await db.flush()
    return obj


async def create_entry_with_lines(
    db: AsyncSession,
    entry_data: dict,
    lines_data: list[dict],
) -> AccountingEntry:
    obj = AccountingEntry(**entry_data)
    db.add(obj)
    await db.flush()
    for idx, line in enumerate(lines_data):
        db.add(AccountingEntryLine(**line, entry_id=obj.id, sort_order=idx))
    await db.flush()
    await db.commit()
    return await get_entry(db, obj.id) or obj


async def get_entry_by_quote_source(db: AsyncSession, quote_id: UUID) -> AccountingEntry | None:
    result = await db.execute(
        select(AccountingEntry)
        .where(
            AccountingEntry.quote_id == quote_id,
            AccountingEntry.source_type == "customer_quote",
            AccountingEntry.is_deleted.is_(False),
            AccountingEntry.status != "void",
        )
        .order_by(AccountingEntry.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_entry_by_source(
    db: AsyncSession,
    source_type: str,
    source_id: UUID,
) -> AccountingEntry | None:
    result = await db.execute(
        select(AccountingEntry)
        .where(
            AccountingEntry.source_type == source_type,
            AccountingEntry.source_id == source_id,
            AccountingEntry.is_deleted.is_(False),
            AccountingEntry.status != "void",
        )
        .order_by(AccountingEntry.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def save_entry(db: AsyncSession, obj: AccountingEntry) -> AccountingEntry:
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_entries(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    customer_id: UUID | None = None,
    supplier_id: UUID | None = None,
    entry_kind: str | None = None,
    include_void: bool = False,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[int, list[AccountingEntry]]:
    filters = [AccountingEntry.is_deleted.is_(False)]
    if not include_void:
        filters.append(AccountingEntry.status != "void")
    if customer_id is not None:
        filters.append(AccountingEntry.customer_id == customer_id)
    if supplier_id is not None:
        filters.append(AccountingEntry.supplier_id == supplier_id)
    if entry_kind:
        filters.append(AccountingEntry.entry_kind == entry_kind)
    if date_from is not None:
        filters.append(AccountingEntry.occurred_on >= date_from)
    if date_to is not None:
        filters.append(AccountingEntry.occurred_on <= date_to)

    total = int(
        (
            await db.execute(select(func.count()).select_from(AccountingEntry).where(*filters))
        ).scalar_one()
    )
    rows = (
        await db.execute(
            select(AccountingEntry)
            .where(*filters)
            .options(selectinload(AccountingEntry.lines))
            .order_by(AccountingEntry.occurred_on.desc(), AccountingEntry.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return total, list(rows)


async def list_confirmed_customer_receivables(
    db: AsyncSession,
    customer_id: UUID,
) -> list[AccountingEntry]:
    rows = (
        await db.execute(
            select(AccountingEntry)
            .where(
                AccountingEntry.is_deleted.is_(False),
                AccountingEntry.status == "confirmed",
                AccountingEntry.entry_kind == "receivable",
                AccountingEntry.customer_id == customer_id,
            )
            .order_by(AccountingEntry.occurred_on.desc(), AccountingEntry.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def list_customer_receipts(
    db: AsyncSession,
    customer_id: UUID,
) -> list[AccountingEntry]:
    rows = (
        await db.execute(
            select(AccountingEntry)
            .where(
                AccountingEntry.is_deleted.is_(False),
                AccountingEntry.status == "confirmed",
                AccountingEntry.entry_kind == "receipt",
                AccountingEntry.customer_id == customer_id,
            )
            .order_by(AccountingEntry.occurred_on.desc(), AccountingEntry.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


async def list_settlements_by_receipt(db: AsyncSession, receipt_entry_id: UUID) -> list[AccountingSettlement]:
    rows = (
        await db.execute(
            select(AccountingSettlement)
            .where(
                AccountingSettlement.receipt_entry_id == receipt_entry_id,
                AccountingSettlement.is_deleted.is_(False),
            )
            .options(selectinload(AccountingSettlement.receivable_entry))
        )
    ).scalars().all()
    return list(rows)


async def list_settlements_by_receipts(db: AsyncSession, receipt_ids: list[UUID]) -> list[AccountingSettlement]:
    if not receipt_ids:
        return []
    rows = (
        await db.execute(
            select(AccountingSettlement)
            .where(
                AccountingSettlement.receipt_entry_id.in_(receipt_ids),
                AccountingSettlement.is_deleted.is_(False),
            )
            .options(selectinload(AccountingSettlement.receivable_entry))
        )
    ).scalars().all()
    return list(rows)


async def create_settlement(db: AsyncSession, data: dict) -> AccountingSettlement:
    obj = AccountingSettlement(**data)
    db.add(obj)
    await db.flush()
    return obj


async def customer_ledger_rows(db: AsyncSession) -> list[tuple[Customer, list[AccountingEntry], bool]]:
    """Customers in ledger registry or with confirmed receivable/receipt."""
    registered_ids = list(
        (
            await db.execute(
                select(CustomerLedgerAccount.customer_id).where(
                    CustomerLedgerAccount.is_deleted.is_(False),
                )
            )
        ).scalars().all()
    )

    entry_customer_ids = list(
        (
            await db.execute(
                select(AccountingEntry.customer_id)
                .where(
                    AccountingEntry.is_deleted.is_(False),
                    AccountingEntry.status == "confirmed",
                    AccountingEntry.entry_kind.in_(("receivable", "receipt")),
                    AccountingEntry.customer_id.is_not(None),
                )
                .distinct()
            )
        ).scalars().all()
    )

    registered_set = {cid for cid in registered_ids if cid is not None}
    customer_ids = list(registered_set | {cid for cid in entry_customer_ids if cid is not None})
    if not customer_ids:
        return []

    customers = list(
        (await db.execute(select(Customer).where(Customer.id.in_(customer_ids), Customer.is_deleted.is_(False)))).scalars().all()
    )
    customer_map = {c.id: c for c in customers}

    receivables = (
        await db.execute(
            select(AccountingEntry).where(
                AccountingEntry.is_deleted.is_(False),
                AccountingEntry.status == "confirmed",
                AccountingEntry.entry_kind == "receivable",
                AccountingEntry.customer_id.in_(customer_ids),
            )
        )
    ).scalars().all()

    by_customer: dict[UUID, list[AccountingEntry]] = {cid: [] for cid in customer_ids}
    for r in receivables:
        if r.customer_id:
            by_customer.setdefault(r.customer_id, []).append(r)

    return [
        (customer_map[cid], by_customer.get(cid, []), cid in registered_set)
        for cid in customer_ids
        if cid in customer_map
    ]


async def get_ledger_account(db: AsyncSession, customer_id: UUID) -> CustomerLedgerAccount | None:
    result = await db.execute(
        select(CustomerLedgerAccount).where(
            CustomerLedgerAccount.customer_id == customer_id,
            CustomerLedgerAccount.is_deleted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def register_ledger_account(db: AsyncSession, customer_id: UUID, created_by: UUID | None) -> CustomerLedgerAccount:
    existing = await get_ledger_account(db, customer_id)
    if existing is not None:
        return existing
    obj = CustomerLedgerAccount(customer_id=customer_id, created_by=created_by)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj
