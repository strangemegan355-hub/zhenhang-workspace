"""Seed demo master data + draft quote for local DEMO_QUOTE walkthrough."""

from __future__ import annotations

import os
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Ensure backend package imports resolve when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from app.models.customer import Customer
from app.models.machine import Machine, MachineBom, MachineBomItem, MachineCategory
from app.models.permission import Permission
from app.models.product import Product
from app.models.quote import ApprovalNode, ApprovalTemplate, Quote, QuoteItem, QuoteVersion
from app.models.role import Role
from app.models.user import User

DEMO_CUSTOMER_CODE = "DEMO-CUST-001"
DEMO_MACHINE_CODE = "DEMO-MCH-001"
DEMO_PRODUCT_CODE = "DEMO-PRD-001"
DEMO_BOM_VERSION = "V1.0"
DEMO_QUOTE_NO = "DEMO-Q-001"
DEMO_TEMPLATE_CODE = "DEMO-APPROVAL"

DEMO_PERMISSIONS = [
    ("dashboard:view", "看板查看", "dashboard", "view"),
    ("platform:notification:read", "通知读取", "platform:notification", "read"),
    ("business:quote:read", "报价读取", "business:quote", "read"),
    ("business:quote:create", "报价创建", "business:quote", "create"),
    ("business:quote:update", "报价更新", "business:quote", "update"),
    ("business:quote:approve", "报价审批", "business:quote", "approve"),
    ("business:quote:export", "报价导出", "business:quote", "export"),
    ("master:customer:read", "客户读取", "master:customer", "read"),
    ("platform:config:read", "配置读取", "platform:config", "read"),
]

BOM_MODULES: list[tuple[str, str, int]] = [
    ("M01", "结构件", 8),
    ("M02", "电气件", 8),
    ("M03", "液压件", 8),
]


def _database_url() -> str:
    url = str(settings.database_url)
    return url.replace("localhost", "127.0.0.1")


def _bom_item_rows() -> list[dict]:
    rows: list[dict] = []
    sort_order = 0
    for module_code, module_name, count in BOM_MODULES:
        for idx in range(1, count + 1):
            sort_order += 1
            unit_cost = Decimal("100") + Decimal(sort_order * 17)
            qty = Decimal("1") + Decimal(idx % 3)
            rows.append(
                {
                    "item_code": f"{module_code}-{idx:03d}",
                    "item_name": f"{module_name}-物料{idx:02d}",
                    "spec": f"规格-{module_code}-{idx}",
                    "unit": "EA",
                    "quantity": qty,
                    "unit_cost": unit_cost,
                    "line_total": (qty * unit_cost).quantize(Decimal("0.0001")),
                    "sort_order": sort_order,
                }
            )
    return rows


def _ensure_permissions(db: Session, admin_role: Role) -> None:
    for code, name, resource, action in DEMO_PERMISSIONS:
        perm = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
        if perm is None:
            perm = Permission(name=name, code=code, resource=resource, action=action, description="Demo seed")
            db.add(perm)
            db.flush()
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)


def seed() -> None:
    engine = create_engine(_database_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with SessionLocal() as db:
        admin = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
        if admin is None:
            # Exit 1 rather than printing and returning: a seed that did nothing must not report success to the
            # shell, a CI job or an operator's wrapper script.
            raise SystemExit("ERROR: admin user not found. Run bootstrap_admin.py first.")

        admin_role = db.execute(select(Role).where(Role.code == "admin")).scalar_one_or_none()
        if admin_role is not None:
            _ensure_permissions(db, admin_role)

        existing_quote = db.execute(select(Quote).where(Quote.quote_no == DEMO_QUOTE_NO)).scalar_one_or_none()
        if existing_quote is not None:
            db.commit()
            print(f"Demo quote already exists: {DEMO_QUOTE_NO} ({existing_quote.id})")
            return

        customer = Customer(
            code=DEMO_CUSTOMER_CODE,
            name="演示客户 · 华东精工",
            short_name="华东精工",
            industry="装备制造",
            level="A",
            status="active",
            phone="021-88886666",
            email="demo@huadong.com",
            address="上海市浦东新区演示路 100 号",
            remarks="DEMO_QUOTE 演示客户",
            created_by=admin.id,
        )
        db.add(customer)
        db.flush()

        category = MachineCategory(
            code="DEMO-CAT",
            name="演示机型分类",
            description="本地演示",
            created_by=admin.id,
        )
        db.add(category)
        db.flush()

        machine = Machine(
            category_id=category.id,
            code=DEMO_MACHINE_CODE,
            machine_code=DEMO_MACHINE_CODE,
            name="ZH-500 加工中心",
            model_no="ZH-500",
            status="active",
            description="演示机型 · 五轴加工中心",
            created_by=admin.id,
        )
        db.add(machine)
        db.flush()

        bom_rows = _bom_item_rows()
        bom_total = sum((row["line_total"] for row in bom_rows), Decimal("0"))
        bom = MachineBom(
            machine_id=machine.id,
            version=DEMO_BOM_VERSION,
            is_active=True,
            effective_date=date.today(),
            total_cost=bom_total,
            status="active",
            remark="演示 BOM · 24 行物料",
            created_by=admin.id,
        )
        db.add(bom)
        db.flush()

        for row in bom_rows:
            db.add(
                MachineBomItem(
                    bom_id=bom.id,
                    item_code=row["item_code"],
                    item_name=row["item_name"],
                    spec=row["spec"],
                    unit=row["unit"],
                    quantity=row["quantity"],
                    unit_cost=row["unit_cost"],
                    line_total=row["line_total"],
                    sort_order=row["sort_order"],
                    created_by=admin.id,
                )
            )

        # K-005: seed quote carries product_id (API create path also requires it).
        product = Product(
            code=DEMO_PRODUCT_CODE,
            name="演示产品 · ZH-500",
            spec="ZH-500",
            unit="EA",
            status="active",
            reference_cost=bom_total,
            reference_price=(bom_total * Decimal("1.25")).quantize(Decimal("0.0001")),
            machine_id=machine.id,
            default_bom_id=bom.id,
            remark="由 seed_demo_quote.py 生成",
            created_by=admin.id,
        )
        db.add(product)
        db.flush()

        template = ApprovalTemplate(
            code=DEMO_TEMPLATE_CODE,
            name="演示报价审批",
            biz_type="quote",
            description="DEMO 单节点审批",
            is_active=True,
            created_by=admin.id,
        )
        db.add(template)
        db.flush()
        db.add(
            ApprovalNode(
                template_id=template.id,
                node_order=1,
                node_name="部门经理审批",
                approver_role_code="admin",
                sign_mode="orsign",
                min_amount=Decimal("0"),
                created_by=admin.id,
            )
        )

        quote = Quote(
            quote_no=DEMO_QUOTE_NO,
            title="演示报价 · ZH-500 加工中心",
            customer_id=customer.id,
            product_id=product.id,
            machine_id=machine.id,
            bom_id=bom.id,
            approval_template_id=template.id,
            workflow_state="draft",
            currency="CNY",
            total_amount=Decimal("0"),
            valid_until=date.today() + timedelta(days=30),
            remark="由 seed_demo_quote.py 生成，用于 DEMO_QUOTE 演示",
            created_by=admin.id,
        )
        db.add(quote)
        db.flush()

        version = QuoteVersion(
            quote_id=quote.id,
            version_no=1,
            bom_snapshot={"bom_id": str(bom.id), "bom_version": DEMO_BOM_VERSION, "item_count": len(bom_rows)},
            cost_snapshot={"bom_total_cost": str(bom_total), "captured_at": datetime.now(UTC).isoformat()},
            analysis_snapshot={},
            total_amount=Decimal("0"),
            total_cost=bom_total,
            profit_amount=Decimal("0"),
            profit_rate=Decimal("0"),
            is_current=True,
            changed_at=datetime.now(UTC),
            created_by=admin.id,
        )
        db.add(version)
        db.flush()

        total_amount = Decimal("0")
        for row in bom_rows:
            unit_price = (row["unit_cost"] * Decimal("1.25")).quantize(Decimal("0.01"))
            line_total = (row["quantity"] * unit_price).quantize(Decimal("0.0001"))
            total_amount += line_total
            db.add(
                QuoteItem(
                    quote_version_id=version.id,
                    item_code=row["item_code"],
                    item_name=row["item_name"],
                    spec=row["spec"],
                    unit=row["unit"],
                    quantity=row["quantity"],
                    unit_price=unit_price,
                    line_total=line_total,
                    source_type="bom",
                    created_by=admin.id,
                )
            )

        profit = total_amount - bom_total
        version.total_amount = total_amount
        version.profit_amount = profit
        version.profit_rate = Decimal("0") if total_amount == 0 else (profit / total_amount).quantize(Decimal("0.0001"))
        quote.total_amount = total_amount

        db.commit()
        print("Demo seed complete:")
        print(f"  customer: {customer.code} ({customer.id})")
        print(f"  machine:  {machine.code} ({machine.id})")
        print(f"  bom:      {DEMO_BOM_VERSION} · {len(bom_rows)} items ({bom.id})")
        print(f"  quote:    {quote.quote_no} · draft · V1 ({quote.id})")
        print(f"  amount:   {total_amount} CNY")
        print("Open http://localhost:3000/quotes and select the demo quote.")

    engine.dispose()


def main() -> None:
    seed()


if __name__ == "__main__":
    main()
