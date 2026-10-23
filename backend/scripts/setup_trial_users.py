"""
Create trial roles and default accounts for internal pilot.

Run after: bootstrap_admin.py, seed_tenant.py (optional)

  python scripts/setup_trial_users.py
  python scripts/setup_trial_users.py --dry-run
  python scripts/setup_trial_users.py --reset-passwords   # update passwords for existing trial users
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from _script_utils import BACKEND_ROOT, database_url  # noqa: F401
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

# (code, name, data_scope, permissions[(code, name, resource, action)])
TRIAL_ROLE_DEFS: list[tuple[str, str, str, list[tuple[str, str, str, str]]]] = [
    (
        "trial_boss",
        "老板",
        "all",
        [
            ("dashboard:view", "看板", "dashboard", "view"),
            ("business:quote:read", "报价读取", "business:quote", "read"),
            ("business:quote:approve", "报价审批", "business:quote", "approve"),
            ("business:quote:export", "报价导出", "business:quote", "export"),
            ("business:cost_estimate:read", "成本核算读取", "business:cost_estimate", "read"),
            ("business:project:read", "项目读取", "business:project", "read"),
            ("business:actual_cost:read", "实际成本读取", "business:actual_cost", "read"),
            ("business:procurement:read", "采购读取", "business:procurement", "read"),
            ("business:procurement:transfer", "采购转入", "business:procurement", "transfer"),
            ("business:work_order:read", "工单读取", "business:work_order", "read"),
            ("business:fieldwork:read", "现场作业读取", "business:fieldwork", "read"),
            ("master:machine:read", "机型读取", "master:machine", "read"),
            ("master:bom:read", "BOM读取", "master:bom", "read"),
            ("master:material:read", "材料读取", "master:material", "read"),
            ("master:supplier:read", "供应商读取", "master:supplier", "read"),
            ("master:product:read", "产品读取", "master:product", "read"),
            ("master:product_cost_template:read", "成本模板读取", "master:product_cost_template", "read"),
            ("master:product_price_template:read", "售价模板读取", "master:product_price_template", "read"),
            ("master:standard:read", "基础标准读取", "master:standard", "read"),
            ("platform:notification:read", "通知读取", "platform:notification", "read"),
            ("business:accounting:read", "记账读取", "business:accounting", "read"),
            ("business:accounting:backfill", "记账补录", "business:accounting", "backfill"),
            ("business:accounting:create", "记账创建", "business:accounting", "create"),
            ("business:accounting:confirm", "记账确认", "business:accounting", "confirm"),
            ("business:accounting:confirm_receivable", "确认应收", "business:accounting", "confirm_receivable"),
            ("business:accounting:approve_quote_receivable", "应收优惠审批", "business:accounting", "approve_quote_receivable"),
            ("business:accounting:approve_procurement_payable", "采购应付审批", "business:accounting", "approve_procurement_payable"),
            ("business:approval:read", "审批中心", "business:approval", "read"),
            ("business:accounting:post_payable", "应付过账", "business:accounting", "post_payable"),
            ("business:aftersales:read", "售后服务读取", "business:aftersales", "read"),
            ("business:workshop:read", "车间看板读取", "business:workshop", "read"),
        ],
    ),
    (
        "trial_sales",
        "销售",
        "department",
        [
            ("dashboard:view", "看板", "dashboard", "view"),
            ("business:quote:read", "报价读取", "business:quote", "read"),
            ("business:quote:create", "报价创建", "business:quote", "create"),
            ("business:quote:update", "报价更新", "business:quote", "update"),
            ("business:quote:export", "报价导出", "business:quote", "export"),
            ("business:cost_estimate:read", "成本核算读取", "business:cost_estimate", "read"),
            ("business:cost_estimate:create", "成本核算创建", "business:cost_estimate", "create"),
            ("business:cost_estimate:update", "成本核算更新", "business:cost_estimate", "update"),
            ("business:project:read", "项目读取", "business:project", "read"),
            ("business:actual_cost:read", "实际成本读取", "business:actual_cost", "read"),
            ("business:actual_cost:create", "实际成本创建", "business:actual_cost", "create"),
            ("business:procurement:read", "采购读取", "business:procurement", "read"),
            ("business:procurement:create", "采购创建", "business:procurement", "create"),
            ("business:procurement:update", "采购更新", "business:procurement", "update"),
            ("business:accounting:post_payable", "应付过账", "business:accounting", "post_payable"),
            ("business:work_order:read", "工单读取", "business:work_order", "read"),
            ("business:fieldwork:read", "现场作业读取", "business:fieldwork", "read"),
            ("business:fieldwork:create", "现场作业创建", "business:fieldwork", "create"),
            ("business:project:create", "项目创建", "business:project", "create"),
            ("business:project:update", "项目更新", "business:project", "update"),
            ("master:customer:read", "客户读取", "master:customer", "read"),
            ("master:customer:update", "客户更新", "master:customer", "update"),
            ("master:machine:read", "机型读取", "master:machine", "read"),
            ("master:bom:read", "BOM读取", "master:bom", "read"),
            ("master:bom_item:read", "BOM明细读取", "master:bom_item", "read"),
            ("master:material:read", "材料读取", "master:material", "read"),
            ("master:supplier:read", "供应商读取", "master:supplier", "read"),
            ("master:supplier:create", "供应商创建", "master:supplier", "create"),
            ("master:product:read", "产品读取", "master:product", "read"),
            ("master:product_cost_template:read", "成本模板读取", "master:product_cost_template", "read"),
            ("master:product_price_template:read", "售价模板读取", "master:product_price_template", "read"),
            ("platform:notification:read", "通知读取", "platform:notification", "read"),
            ("platform:file:read", "文件读取", "platform:file", "read"),
            ("platform:file:upload", "文件上传", "platform:file", "upload"),
            ("business:accounting:read", "记账读取", "business:accounting", "read"),
            ("business:accounting:post_quote", "报价生成应收", "business:accounting", "post_quote"),
            ("business:accounting:confirm_receivable", "确认应收", "business:accounting", "confirm_receivable"),
            ("master:customer:create", "客户创建", "master:customer", "create"),
            ("master:customer_contact:read", "客户联系人读取", "master:customer_contact", "read"),
            ("master:customer_contact:create", "客户联系人创建", "master:customer_contact", "create"),
            ("master:customer_contact:update", "客户联系人更新", "master:customer_contact", "update"),
            ("master:customer_followup:read", "客户跟进读取", "master:customer_followup", "read"),
            ("master:customer_followup:create", "客户跟进创建", "master:customer_followup", "create"),
            ("master:customer_followup:update", "客户跟进更新", "master:customer_followup", "update"),
            ("business:aftersales:read", "售后服务读取", "business:aftersales", "read"),
            ("business:aftersales:create", "售后服务创建", "business:aftersales", "create"),
            ("business:aftersales:update", "售后服务更新", "business:aftersales", "update"),
            ("platform:file:bind", "文件关联", "platform:file", "bind"),
        ],
    ),
    (
        "trial_tech",
        "技术",
        "all",
        [
            ("dashboard:view", "看板", "dashboard", "view"),
            ("master:machine:read", "机型读取", "master:machine", "read"),
            ("master:machine:create", "机型创建", "master:machine", "create"),
            ("master:machine:update", "机型更新", "master:machine", "update"),
            ("master:machine:delete", "机型删除", "master:machine", "delete"),
            ("master:machine_category:read", "机型分类读取", "master:machine_category", "read"),
            ("master:machine_category:create", "机型分类创建", "master:machine_category", "create"),
            ("master:machine_category:update", "机型分类更新", "master:machine_category", "update"),
            ("master:machine_category:delete", "机型分类删除", "master:machine_category", "delete"),
            ("master:machine_parameter:read", "机型参数读取", "master:machine_parameter", "read"),
            ("master:machine_parameter:create", "机型参数创建", "master:machine_parameter", "create"),
            ("master:machine_parameter:update", "机型参数更新", "master:machine_parameter", "update"),
            ("master:machine_parameter:delete", "机型参数删除", "master:machine_parameter", "delete"),
            ("master:machine_image:read", "机型图片读取", "master:machine_image", "read"),
            ("master:machine_image:create", "机型图片创建", "master:machine_image", "create"),
            ("master:machine_image:update", "机型图片更新", "master:machine_image", "update"),
            ("master:machine_image:delete", "机型图片删除", "master:machine_image", "delete"),
            ("master:bom:read", "BOM读取", "master:bom", "read"),
            ("master:bom:create", "BOM创建", "master:bom", "create"),
            ("master:bom:update", "BOM更新", "master:bom", "update"),
            ("master:bom_item:read", "BOM明细读取", "master:bom_item", "read"),
            ("master:bom_item:create", "BOM明细创建", "master:bom_item", "create"),
            ("master:bom_item:update", "BOM明细更新", "master:bom_item", "update"),
            ("master:bom_item:delete", "BOM明细删除", "master:bom_item", "delete"),
            ("master:material:read", "材料读取", "master:material", "read"),
            ("master:material:create", "材料创建", "master:material", "create"),
            ("master:material:update", "材料更新", "master:material", "update"),
            ("master:supplier:read", "供应商读取", "master:supplier", "read"),
            ("master:supplier:create", "供应商创建", "master:supplier", "create"),
            ("master:supplier:update", "供应商更新", "master:supplier", "update"),
            ("master:standard:read", "基础标准读取", "master:standard", "read"),
            ("master:standard:create", "基础标准创建", "master:standard", "create"),
            ("master:standard:update", "基础标准更新", "master:standard", "update"),
            ("master:standard:delete", "基础标准删除", "master:standard", "delete"),
            ("master:product_category:read", "产品分类读取", "master:product_category", "read"),
            ("master:product_category:create", "产品分类创建", "master:product_category", "create"),
            ("master:product_category:update", "产品分类更新", "master:product_category", "update"),
            ("master:product_category:delete", "产品分类删除", "master:product_category", "delete"),
            ("master:product:read", "产品读取", "master:product", "read"),
            ("master:product:create", "产品创建", "master:product", "create"),
            ("master:product:update", "产品更新", "master:product", "update"),
            ("master:product:delete", "产品删除", "master:product", "delete"),
            ("master:product_cost_template:read", "成本模板读取", "master:product_cost_template", "read"),
            ("master:product_cost_template:create", "成本模板创建", "master:product_cost_template", "create"),
            ("master:product_cost_template:update", "成本模板更新", "master:product_cost_template", "update"),
            ("master:product_cost_template:delete", "成本模板删除", "master:product_cost_template", "delete"),
            ("master:product_price_template:read", "售价模板读取", "master:product_price_template", "read"),
            ("master:product_price_template:create", "售价模板创建", "master:product_price_template", "create"),
            ("master:product_price_template:update", "售价模板更新", "master:product_price_template", "update"),
            ("master:product_price_template:delete", "售价模板删除", "master:product_price_template", "delete"),
            ("business:cost_estimate:read", "成本核算读取", "business:cost_estimate", "read"),
            ("business:cost_estimate:create", "成本核算创建", "business:cost_estimate", "create"),
            ("business:cost_estimate:update", "成本核算更新", "business:cost_estimate", "update"),
            ("business:cost_estimate:delete", "成本核算删除", "business:cost_estimate", "delete"),
            ("business:project:read", "项目读取", "business:project", "read"),
            ("business:project:create", "项目创建", "business:project", "create"),
            ("business:project:update", "项目更新", "business:project", "update"),
            ("business:project:delete", "项目删除", "business:project", "delete"),
            ("business:actual_cost:read", "实际成本读取", "business:actual_cost", "read"),
            ("business:actual_cost:create", "实际成本创建", "business:actual_cost", "create"),
            ("business:actual_cost:delete", "实际成本删除", "business:actual_cost", "delete"),
            ("business:procurement:read", "采购读取", "business:procurement", "read"),
            ("business:procurement:create", "采购创建", "business:procurement", "create"),
            ("business:procurement:update", "采购更新", "business:procurement", "update"),
            ("business:procurement:delete", "采购删除", "business:procurement", "delete"),
            ("business:procurement:transfer", "采购转入", "business:procurement", "transfer"),
            ("business:accounting:post_payable", "应付过账", "business:accounting", "post_payable"),
            ("business:work_order:read", "工单读取", "business:work_order", "read"),
            ("business:work_order:create", "工单创建", "business:work_order", "create"),
            ("business:work_order:update", "工单更新", "business:work_order", "update"),
            ("business:work_order:delete", "工单删除", "business:work_order", "delete"),
            ("business:fieldwork:read", "现场作业读取", "business:fieldwork", "read"),
            ("business:fieldwork:create", "现场作业创建", "business:fieldwork", "create"),
            ("business:fieldwork:update", "现场作业更新", "business:fieldwork", "update"),
            ("business:fieldwork:delete", "现场作业删除", "business:fieldwork", "delete"),
            ("platform:notification:read", "通知读取", "platform:notification", "read"),
            ("master:equipment_unit:read", "设备单元读取", "master:equipment_unit", "read"),
            ("master:equipment_unit:create", "设备单元创建", "master:equipment_unit", "create"),
            ("master:equipment_unit:update", "设备单元更新", "master:equipment_unit", "update"),
            ("business:aftersales:read", "售后服务读取", "business:aftersales", "read"),
            ("business:aftersales:update", "售后服务更新", "business:aftersales", "update"),
        ],
    ),
    (
        "workshop",
        "车间",
        "department",
        [
            ("dashboard:view", "看板", "dashboard", "view"),
            ("business:quote:read", "报价读取", "business:quote", "read"),
            ("business:work_order:read", "工单读取", "business:work_order", "read"),
            ("business:work_order:create", "工单创建", "business:work_order", "create"),
            ("business:work_order:update", "工单更新", "business:work_order", "update"),
            ("business:fieldwork:read", "现场作业读取", "business:fieldwork", "read"),
            ("business:fieldwork:create", "现场作业创建", "business:fieldwork", "create"),
            ("business:fieldwork:update", "现场作业更新", "business:fieldwork", "update"),
            ("platform:notification:read", "通知读取", "platform:notification", "read"),
            ("master:equipment_unit:read", "设备单元读取", "master:equipment_unit", "read"),
            ("business:workshop:read", "车间看板读取", "business:workshop", "read"),
            ("business:mes:read", "MES 信号读取", "business:mes", "read"),
            ("business:mes:write", "MES 信号写入", "business:mes", "write"),
        ],
    ),
    (
        "trial_finance",
        "财务",
        "all",
        [
            ("dashboard:view", "看板", "dashboard", "view"),
            ("business:quote:read", "报价读取", "business:quote", "read"),
            ("business:quote:export", "报价导出", "business:quote", "export"),
            ("business:cost_estimate:read", "成本核算读取", "business:cost_estimate", "read"),
            ("business:project:read", "项目读取", "business:project", "read"),
            ("business:actual_cost:read", "实际成本读取", "business:actual_cost", "read"),
            ("business:procurement:read", "采购读取", "business:procurement", "read"),
            ("business:procurement:transfer", "采购转入", "business:procurement", "transfer"),
            ("business:work_order:read", "工单读取", "business:work_order", "read"),
            ("business:fieldwork:read", "现场作业读取", "business:fieldwork", "read"),
            ("platform:notification:read", "通知读取", "platform:notification", "read"),
            ("platform:file:read", "文件读取", "platform:file", "read"),
            ("business:aftersales:read", "售后服务读取", "business:aftersales", "read"),
            # 财务中心主路径（读 + 日常收付核销；不含平台配置）
            ("business:accounting:read", "记账读取", "business:accounting", "read"),
            ("business:accounting:create", "记账创建", "business:accounting", "create"),
            ("business:accounting:confirm", "记账确认", "business:accounting", "confirm"),
            ("business:accounting:confirm_receivable", "确认应收", "business:accounting", "confirm_receivable"),
            ("business:accounting:post_payable", "应付过账", "business:accounting", "post_payable"),
            ("business:approval:read", "审批中心", "business:approval", "read"),
        ],
    ),
    (
        "trial_approver",
        "审批人",
        "all",
        [
            ("dashboard:view", "看板", "dashboard", "view"),
            ("business:quote:read", "报价读取", "business:quote", "read"),
            ("business:quote:approve", "报价审批", "business:quote", "approve"),
            ("business:approval:read", "审批中心", "business:approval", "read"),
            ("platform:notification:read", "通知读取", "platform:notification", "read"),
        ],
    ),
    (
        "trial_admin",
        "试运行管理员",
        "all",
        [
            ("dashboard:view", "看板", "dashboard", "view"),
            ("business:quote:read", "报价读取", "business:quote", "read"),
            ("business:quote:create", "报价创建", "business:quote", "create"),
            ("business:quote:update", "报价更新", "business:quote", "update"),
            ("business:quote:approve", "报价审批", "business:quote", "approve"),
            ("business:quote:export", "报价导出", "business:quote", "export"),
            ("master:customer:read", "客户读取", "master:customer", "read"),
            ("master:machine:read", "机型读取", "master:machine", "read"),
            ("master:bom:read", "BOM读取", "master:bom", "read"),
            ("platform:notification:read", "通知读取", "platform:notification", "read"),
            ("platform:file:read", "文件读取", "platform:file", "read"),
            ("platform:file:upload", "文件上传", "platform:file", "upload"),
            # Destructive master-data writes stay with the admin role (least privilege).
            ("master:customer:delete", "客户删除", "master:customer", "delete"),
            ("master:customer_contact:delete", "客户联系人删除", "master:customer_contact", "delete"),
            ("master:customer_followup:delete", "客户跟进删除", "master:customer_followup", "delete"),
            ("master:bom:delete", "BOM删除", "master:bom", "delete"),
            ("master:material:delete", "材料删除", "master:material", "delete"),
            ("master:supplier:delete", "供应商删除", "master:supplier", "delete"),
            ("business:aftersales:delete", "售后服务删除", "business:aftersales", "delete"),
            ("master:workflow_state:read", "工作流状态读取", "master:workflow_state", "read"),
            ("master:workflow_state:create", "工作流状态创建", "master:workflow_state", "create"),
            ("master:workflow_transition:read", "工作流流转读取", "master:workflow_transition", "read"),
            ("master:workflow_transition:create", "工作流流转创建", "master:workflow_transition", "create"),
            ("platform:file:bind", "文件关联", "platform:file", "bind"),
            ("system:department:read", "部门读取", "system:department", "read"),
            ("system:tenant:read", "租户读取", "system:tenant", "read"),
            ("business:workshop:read", "车间看板读取", "business:workshop", "read"),
            ("business:mes:read", "MES 信号读取", "business:mes", "read"),
            ("business:mes:write", "MES 信号写入", "business:mes", "write"),
            # K-018: 业务开关（非 platform:config，避免试用账号进平台配置面）
            ("business:settings:read", "业务设置读取", "business:settings", "read"),
            ("business:settings:update", "业务设置更新", "business:settings", "update"),
        ],
    ),
]

# username, password, full_name, email, role_code
# username, environment variable holding that account's password, full name, email, role code.
# The password itself never appears here: an operator supplies TRIAL_*_PASSWORD, or this script
# generates one and prints it once.
TRIAL_USERS: list[tuple[str, str, str, str, str]] = [
    ("boss", "TRIAL_BOSS_PASSWORD", "张总（老板）", "boss@example.com", "trial_boss"),
    ("trialadmin", "TRIAL_ADMIN_PASSWORD", "试运行管理员", "trialadmin@example.com", "trial_admin"),
    ("sales01", "TRIAL_SALES_PASSWORD", "销售小王", "sales01@example.com", "trial_sales"),
    ("tech01", "TRIAL_TECH_PASSWORD", "技术李工", "tech01@example.com", "trial_tech"),
    ("workshop01", "TRIAL_WORKSHOP_PASSWORD", "车间班长", "workshop01@example.com", "workshop"),
    ("finance01", "TRIAL_FINANCE_PASSWORD", "财务陈会计", "finance01@example.com", "trial_finance"),
    ("approver01", "TRIAL_APPROVER_PASSWORD", "审批刘经理", "approver01@example.com", "trial_approver"),
]

MIN_PASSWORD_LENGTH = 12


def _resolve_password(env_var: str) -> tuple[str, bool]:
    """Return (password, generated); no default password ships with this script.

    An operator either supplies the password through the environment, or this run generates a
    strong one and prints it exactly once. A re-run does not reveal a generated password again.
    """
    supplied = os.getenv(env_var, "").strip()
    if supplied:
        if len(supplied) < MIN_PASSWORD_LENGTH:
            raise SystemExit(f"{env_var} must be at least {MIN_PASSWORD_LENGTH} characters")
        return supplied, False
    return secrets.token_urlsafe(15), True


def _account_guide(resolved: dict[str, tuple[str | None, bool]]) -> str:
    """Describe only what this run actually did.

    A password is generated solely for an account that is being created or reset, so every entry here
    corresponds to something that happened; an existing account whose password was left alone says so.
    """
    lines = [
        "=" * 80,
        "  内部试运行账号（口令不再有默认值）",
        "=" * 80,
        "  用户名        角色            口令来源",
    ]
    generated_any = False
    for username, env_var, _full_name, _email, role_code in TRIAL_USERS:
        password, generated = resolved.get(username, (None, False))
        if password is None:
            source = "口令未更改（账号已存在）"
        elif generated:
            source = f"本次生成: {password}"
            generated_any = True
        else:
            source = f"环境变量 {env_var}"
        lines.append(f"  {username:<14}{role_code:<16}{source}")
    lines.append("=" * 80)
    if generated_any:
        lines.append("  标注“本次生成”的账号使用本次生成的口令，只显示这一次。")
    else:
        lines.append("  本次没有创建账号，也没有重置口令。")
    lines.extend(
        [
            "  首次登录后必须修改口令；详见 docs/INTERNAL_TRIAL_GUIDE.md。",
            "=" * 80,
        ]
    )
    return "\n".join(lines)


def _ensure_permission(db: Session, code: str, name: str, resource: str, action: str) -> Permission:
    perm = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
    if perm is None:
        perm = Permission(name=name, code=code, resource=resource, action=action, description="trial seed")
        db.add(perm)
        db.flush()
    return perm


def setup(*, dry_run: bool, reset_passwords: bool) -> None:
    engine = create_engine(database_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with SessionLocal() as db:
        dept = db.execute(select(Department).where(Department.code == "ROOT")).scalar_one_or_none()
        if dept is None:
            # A missing ROOT department is a hard error, not a warning: printing it and returning
            # exited 0, so any automation would seed a half-configured system and carry on.
            raise SystemExit("ERROR: department ROOT missing - run bootstrap_admin.py first")

        roles_by_code: dict[str, Role] = {}
        for role_code, role_name, data_scope, perm_defs in TRIAL_ROLE_DEFS:
            role = (
                db.execute(
                    select(Role).where(Role.code == role_code).options(selectinload(Role.permissions))
                )
            ).scalar_one_or_none()
            if role is None:
                role = Role(name=role_name, code=role_code, description="Internal trial role", is_system=False)
                role.data_scope = data_scope
                db.add(role)
                db.flush()
                print(f"+ role {role_code} ({role_name})")
            else:
                role.data_scope = data_scope
                print(f"~ role exists {role_code}")
            # Exact sync: trial roles must match the declared set. Earlier versions only
            # appended, so forbidden codes (e.g. platform:config:*) could linger forever.
            desired: list[Permission] = []
            desired_ids: set = set()
            for pcode, pname, resource, action in perm_defs:
                perm = _ensure_permission(db, pcode, pname, resource, action)
                if perm.id not in desired_ids:
                    desired.append(perm)
                    desired_ids.add(perm.id)
            current_ids = {p.id for p in role.permissions}
            added = desired_ids - current_ids
            removed = current_ids - desired_ids
            if added or removed:
                role.permissions = desired
                print(
                    f"  sync perms {role_code}: +{len(added)} -{len(removed)} "
                    f"(now {len(desired)})"
                )
            roles_by_code[role_code] = role

        # Generated lazily, per account, and only where a password will actually be written: resolving all
        # of them up front is what let a re-run print passwords it never applied.
        resolved_passwords: dict[str, tuple[str | None, bool]] = {}
        for username, password_env, full_name, email, role_code in TRIAL_USERS:
            user = (
                db.execute(
                    select(User).where(User.username == username).options(selectinload(User.roles))
                )
            ).scalar_one_or_none()
            role = roles_by_code.get(role_code)
            if user is None:
                if dry_run:
                    print(f"[dry-run] would create user {username} -> {role_code}")
                    continue
                password, generated = _resolve_password(password_env)
                resolved_passwords[username] = (password, generated)
                user = User(
                    username=username,
                    email=email,
                    hashed_password=get_password_hash(password),
                    full_name=full_name,
                    is_active=True,
                    is_superuser=False,
                    department_id=dept.id,
                )
                if role:
                    user.roles.append(role)
                db.add(user)
                print(f"+ user {username} ({full_name})")
            else:
                if reset_passwords and not dry_run:
                    password, generated = _resolve_password(password_env)
                    resolved_passwords[username] = (password, generated)
                    user.hashed_password = get_password_hash(password)
                    print(f"~ reset password {username}")
                else:
                    resolved_passwords[username] = (None, False)
                    print(f"~ user exists {username}")
                if not dry_run:
                    user.email = email
                if role and role not in user.roles:
                    user.roles.append(role)
                    print(f"  attached role {role_code}")

        if dry_run:
            db.rollback()
            print("\n[DRY-RUN] rolled back")
        else:
            db.commit()
            print(_account_guide(resolved_passwords))


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup internal trial users and roles")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--reset-passwords",
        action="store_true",
        help="give existing trial accounts the password from TRIAL_*_PASSWORD, or a fresh generated one",
    )
    args = parser.parse_args()
    setup(dry_run=args.dry_run, reset_passwords=args.reset_passwords)


if __name__ == "__main__":
    main()
