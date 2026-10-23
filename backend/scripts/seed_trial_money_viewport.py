"""
Seed trial material/supplier/procurement + enable accounting flags for viewport money checks.

Policy (2026-10-23, owner): for **local trial DB only**, this seed **always** turns on
accounting_enabled / quote_receivable_enabled / procurement_approval_enabled.
It is NOT an optional viewport switch. Never blind-run against production.

Idempotent: re-run skips existing TRIAL-* codes / request_nos / entry_nos.
Does NOT weaken permissions or confirm/void finance entries — only draft sample rows + business.settings flags.
Optional ``--with-pending-approval`` (OFF by default) may add one pending procurement-payable
request for approvals money viewport; still local-only; never auto-approves.

Usage (backend venv; local trial often 55432):
  $env:DATABASE_URL="postgresql+psycopg://erp:erp@127.0.0.1:55432/erp_db"
  python -u scripts/seed_trial_money_viewport.py
  python -u scripts/seed_trial_money_viewport.py --dry-run
  python -u scripts/seed_trial_money_viewport.py --with-pending-approval
  # non-local URL refused unless:
  python -u scripts/seed_trial_money_viewport.py --allow-non-local
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime
from decimal import Decimal

from app.models.accounting_entry import AccountingEntry
from app.models.customer import Customer
from app.models.material import Material
from app.models.procurement_entry import ProcurementEntry
from app.models.procurement_payable_request import ProcurementPayableRequest
from app.models.supplier import Supplier
from app.models.system_config import SystemConfig
from app.models.user import User
from app.services.business_settings_service import (
    CONFIG_GROUP,
    CONFIG_KEY,
    default_business_settings,
)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from _script_utils import print_db_target

TRIAL_MATERIAL_CODE = "TRIAL-MAT-001"
TRIAL_SUPPLIER_CODE = "TRIAL-SUP-001"
TRIAL_PROC_NOS = ("TRIAL-PR-0001", "TRIAL-PR-0002")
TRIAL_PROC_PENDING_NO = "TRIAL-PR-0003"
TRIAL_AR_NO = "TRIAL-AR-0001"
TRIAL_AP_NO = "TRIAL-AP-0001"


def _ensure_settings(db: Session, *, dry_run: bool) -> dict:
    row = db.execute(select(SystemConfig).where(SystemConfig.key == CONFIG_KEY, SystemConfig.is_deleted.is_(False))).scalar_one_or_none()
    current = default_business_settings()
    if row is not None:
        try:
            stored = json.loads(row.value)
            if isinstance(stored, dict):
                current.update({k: v for k, v in stored.items() if v is not None})
        except json.JSONDecodeError:
            pass
    before = {
        "accounting_enabled": bool(current.get("accounting_enabled")),
        "quote_receivable_enabled": bool(current.get("quote_receivable_enabled")),
        "procurement_approval_enabled": bool(current.get("procurement_approval_enabled")),
    }
    current["accounting_enabled"] = True
    current["quote_receivable_enabled"] = True
    current["procurement_approval_enabled"] = True
    after = {
        "accounting_enabled": True,
        "quote_receivable_enabled": True,
        "procurement_approval_enabled": True,
    }
    print(f"  settings flags: {before} -> {after}")
    if dry_run:
        return after
    value = json.dumps(current, ensure_ascii=False)
    if row is None:
        admin = db.execute(select(User).where(User.username == "trialadmin")).scalar_one_or_none()
        db.add(
            SystemConfig(
                key=CONFIG_KEY,
                value=value,
                value_type="json",
                group=CONFIG_GROUP,
                description="业务设置：公司资料与默认报价参数（试用视口种子开启记账）",
                is_public=False,
                created_by=admin.id if admin else None,
            )
        )
    else:
        row.value = value
        row.value_type = "json"
    return after


def _ensure_material(db: Session, *, dry_run: bool) -> Material | None:
    obj = db.execute(select(Material).where(Material.code == TRIAL_MATERIAL_CODE, Material.is_deleted.is_(False))).scalar_one_or_none()
    if obj:
        print(f"  ~ material exists {TRIAL_MATERIAL_CODE}")
        return obj
    print(f"  + material {TRIAL_MATERIAL_CODE}")
    if dry_run:
        return None
    obj = Material(
        code=TRIAL_MATERIAL_CODE,
        name="试用钢板 Q235",
        spec="δ=8mm",
        unit="kg",
        reference_price=Decimal("12.5000"),
        category="试用",
        status="active",
        remark="viewport money seed",
    )
    db.add(obj)
    db.flush()
    return obj


def _ensure_supplier(db: Session, *, dry_run: bool) -> Supplier | None:
    obj = db.execute(select(Supplier).where(Supplier.code == TRIAL_SUPPLIER_CODE, Supplier.is_deleted.is_(False))).scalar_one_or_none()
    if obj:
        print(f"  ~ supplier exists {TRIAL_SUPPLIER_CODE}")
        return obj
    print(f"  + supplier {TRIAL_SUPPLIER_CODE}")
    if dry_run:
        return None
    obj = Supplier(
        code=TRIAL_SUPPLIER_CODE,
        name="试用钢材供应商",
        contact_name="李工",
        phone="13800000001",
        status="active",
        remark="viewport money seed",
    )
    db.add(obj)
    db.flush()
    return obj


def _ensure_procurement(db: Session, material: Material | None, supplier: Supplier | None, *, dry_run: bool) -> int:
    created = 0
    samples = [
        (TRIAL_PROC_NOS[0], Decimal("10"), Decimal("12.50"), "planned"),
        (TRIAL_PROC_NOS[1], Decimal("4"), Decimal("88.00"), "ordered"),
    ]
    for request_no, qty, unit_price, status in samples:
        exists = db.execute(
            select(ProcurementEntry).where(ProcurementEntry.request_no == request_no, ProcurementEntry.is_deleted.is_(False))
        ).scalar_one_or_none()
        if exists:
            print(f"  ~ procurement exists {request_no}")
            continue
        print(f"  + procurement {request_no} amount={qty * unit_price}")
        created += 1
        if dry_run or material is None or supplier is None:
            continue
        db.add(
            ProcurementEntry(
                request_no=request_no,
                material_id=material.id,
                supplier_id=supplier.id,
                qty=qty,
                unit_price=unit_price,
                lead_days=7,
                need_date=date.today(),
                status=status,
                transferred_to_actual=False,
                payable_status="none",
                remark="viewport money seed",
            )
        )
    return created


def _pick_customer(db: Session) -> Customer | None:
    return db.execute(select(Customer).where(Customer.is_deleted.is_(False)).order_by(Customer.created_at.asc()).limit(1)).scalar_one_or_none()


def _ensure_accounting(
    db: Session,
    *,
    customer: Customer | None,
    supplier: Supplier | None,
    dry_run: bool,
) -> int:
    created = 0
    today = date.today()
    samples: list[tuple[str, str, Decimal, str]] = [
        (TRIAL_AR_NO, "receivable", Decimal("1600.00"), "试用视口应收样例"),
        (TRIAL_AP_NO, "payable", Decimal("125.00"), "试用视口应付样例"),
    ]
    for entry_no, kind, amount, title in samples:
        exists = db.execute(
            select(AccountingEntry).where(AccountingEntry.entry_no == entry_no, AccountingEntry.is_deleted.is_(False))
        ).scalar_one_or_none()
        if exists:
            print(f"  ~ accounting exists {entry_no}")
            continue
        if kind == "receivable" and customer is None:
            print(f"  ! skip {entry_no}: no customer in DB — create a customer first")
            continue
        if kind == "payable" and supplier is None:
            print(f"  ! skip {entry_no}: no supplier")
            continue
        print(f"  + accounting {entry_no} {kind} amount={amount}")
        created += 1
        if dry_run:
            continue
        db.add(
            AccountingEntry(
                entry_no=entry_no,
                entry_kind=kind,
                status="draft",
                party_type="customer" if kind == "receivable" else "supplier",
                customer_id=customer.id if kind == "receivable" else None,
                supplier_id=supplier.id if kind == "payable" else None,
                amount=amount,
                settled_amount=Decimal("0"),
                currency="CNY",
                occurred_on=today,
                booked_on=today,
                is_backfill=False,
                source_type="manual",
                source_no=entry_no,
                approval_status="none",
                title=title,
                remark="viewport money seed — draft only",
            )
        )
    return created


def _is_local_db_url(url: str) -> bool:
    hostpart = url.split("@")[-1].lower()
    return (
        "127.0.0.1" in hostpart
        or "localhost" in hostpart
        or hostpart.startswith("/")
        or "@localhost" in url.lower()
    )


def _pick_requester(db: Session) -> User | None:
    for username in ("finance01", "trialadmin", "boss"):
        user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if user is not None:
            return user
    return db.execute(select(User).order_by(User.created_at.asc()).limit(1)).scalar_one_or_none()


def _ensure_pending_approval(
    db: Session,
    material: Material | None,
    supplier: Supplier | None,
    *,
    dry_run: bool,
) -> None:
    """Optional: one pending procurement-payable for approvals money viewport (no approve)."""
    pending = db.execute(
        select(ProcurementPayableRequest)
        .join(ProcurementEntry, ProcurementPayableRequest.procurement_entry_id == ProcurementEntry.id)
        .where(
            ProcurementPayableRequest.is_deleted.is_(False),
            ProcurementPayableRequest.approval_status == "pending",
            ProcurementEntry.request_no.like("TRIAL-PR-%"),
            ProcurementEntry.is_deleted.is_(False),
        )
        .limit(1)
    ).scalar_one_or_none()
    if pending is not None:
        print(f"  ~ pending approval exists id={pending.id} (skip)")
        return

    entry = db.execute(
        select(ProcurementEntry).where(
            ProcurementEntry.request_no == TRIAL_PROC_PENDING_NO,
            ProcurementEntry.is_deleted.is_(False),
        )
    ).scalar_one_or_none()
    if entry is None:
        qty, unit_price = Decimal("2"), Decimal("50.00")
        print(f"  + procurement {TRIAL_PROC_PENDING_NO} amount={qty * unit_price} (pending-approval sample)")
        if dry_run:
            print("  ~ dry-run — pending approval not created")
            return
        if material is None or supplier is None:
            print("  ! skip pending: missing material/supplier")
            return
        entry = ProcurementEntry(
            request_no=TRIAL_PROC_PENDING_NO,
            material_id=material.id,
            supplier_id=supplier.id,
            qty=qty,
            unit_price=unit_price,
            lead_days=7,
            need_date=date.today(),
            status="ordered",
            transferred_to_actual=False,
            payable_status="none",
            remark="viewport money seed — pending approval sample",
        )
        db.add(entry)
        db.flush()
    elif entry.payable_status in ("posted", "pending") or entry.status == "planned":
        # Already used or not eligible — do not mutate approved finance path.
        print(
            f"  ~ {TRIAL_PROC_PENDING_NO} status={entry.status} payable={entry.payable_status} "
            "(not eligible for new pending; skip)"
        )
        return

    amount = (Decimal(str(entry.qty)) * Decimal(str(entry.unit_price))).quantize(Decimal("0.01"))
    if amount <= 0:
        print(f"  ! skip pending: invalid amount on {TRIAL_PROC_PENDING_NO}")
        return
    requester = _pick_requester(db)
    if requester is None:
        print("  ! skip pending: no user for requested_by")
        return
    print(f"  + pending payable request {TRIAL_PROC_PENDING_NO} amount={amount} by={requester.username}")
    if dry_run:
        return
    db.add(
        ProcurementPayableRequest(
            procurement_entry_id=entry.id,
            requested_by=requester.id,
            requested_amount=amount,
            approval_status="pending",
            created_by=requester.id,
        )
    )
    entry.payable_status = "pending"
    entry.status = "ordered"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--with-pending-approval",
        action="store_true",
        help="Also seed one pending TRIAL procurement-payable (default OFF; local-only; no auto-approve).",
    )
    parser.add_argument(
        "--allow-non-local",
        action="store_true",
        help="Override local-only guard (never use on production without explicit intent).",
    )
    args = parser.parse_args()

    url = print_db_target()
    if not _is_local_db_url(url) and not args.allow_non_local:
        print(
            "REFUSED: seed_trial_money_viewport is local-trial only "
            "(always enables accounting flags). Pass --allow-non-local to override.",
            file=sys.stderr,
        )
        return 2
    print(
        f"seed_trial_money_viewport db={url.split('@')[-1]} dry_run={args.dry_run} "
        f"with_pending_approval={args.with_pending_approval}"
    )
    engine = create_engine(url, connect_args={"connect_timeout": 8})
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        _ensure_settings(db, dry_run=args.dry_run)
        material = _ensure_material(db, dry_run=args.dry_run)
        supplier = _ensure_supplier(db, dry_run=args.dry_run)
        if not args.dry_run:
            db.flush()
            if material is None:
                material = db.execute(
                    select(Material).where(Material.code == TRIAL_MATERIAL_CODE, Material.is_deleted.is_(False))
                ).scalar_one()
            if supplier is None:
                supplier = db.execute(
                    select(Supplier).where(Supplier.code == TRIAL_SUPPLIER_CODE, Supplier.is_deleted.is_(False))
                ).scalar_one()
        _ensure_procurement(db, material, supplier, dry_run=args.dry_run)
        customer = _pick_customer(db)
        if customer:
            print(f"  customer for AR: {customer.code} {customer.name}")
        else:
            print("  ! no customer — receivable sample skipped")
        _ensure_accounting(db, customer=customer, supplier=supplier, dry_run=args.dry_run)
        if args.with_pending_approval:
            _ensure_pending_approval(db, material, supplier, dry_run=args.dry_run)
        else:
            print("  ~ pending approval skipped (pass --with-pending-approval to enable)")
        if args.dry_run:
            print("DRY_RUN done (no commit)")
            return 0
        db.commit()
        print(f"COMMIT ok at {datetime.now(UTC).isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
