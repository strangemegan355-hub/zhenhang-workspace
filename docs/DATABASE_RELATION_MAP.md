# 核心数据表与关联关系

> 来源：`backend/app/models/` + Alembic 迁移（2026-10-23 代码审阅）。  
> 完整表清单 >40；下文仅列 **核心业务链**。

---

## 1. 主数据

| 表 | 主键 | 重要外键/约束 | 说明 |
|---|---|---|---|
| `customers` | UUID | — | 客户 |
| `suppliers` | UUID | — | 供应商 |
| `materials` | UUID | `material_category_id` | 材料 |
| `material_categories` | UUID | 自关联树 | 材料分类 |
| `units` | UUID | — | 计量单位 |
| `products` | UUID | `category_id` | 产品库 |
| `product_categories` | UUID | 树 | 产品分类 |
| `product_cost_templates` / `_lines` | UUID | product | 成本模板 |
| `product_price_templates` / `_lines` | UUID | product | 售价模板 |
| `machines` | UUID | category | 机型 |
| `machine_boms` / `machine_bom_items` | UUID | machine | BOM |
| `option_groups` / `option_items` | UUID | machine 相关 | 选型加价 |

---

## 2. 报价与项目

| 表 | 关联 |
|---|---|
| `quotes` | FK → `customers`, optional `projects`, `machines`, `products`, `machine_boms`, templates |
| `quote_versions` | FK → `quotes` |
| `quote_items` | FK → `quote_versions`；行级金额 Numeric |
| `quote_approvals` / `approval_*` | 审批链 |
| `quote_export_tasks` | 异步导出 |
| `quote_receivable_requests` | 报价转应收申请 |
| `projects` | FK → `customers`, optional `quotes` (`primary_quote_id`) |
| `cost_estimates` + line 表 | FK → `projects` 等 |
| `project_actual_costs` | FK → `projects` |

**金额字段**：广泛使用 `Numeric(18, 4)` / `Numeric(7, 4)`（税率）📄 — 符合 DECIMAL 存储要求；服务层仍需验证舍入规则。

---

## 3. 供应链

| 表 | 关联 |
|---|---|
| `procurement_entries` | supplier, project, material 等 |
| `procurement_payable_requests` | 采购→应付桥梁 |
| `work_orders` | project |
| `fieldwork_records` | 现场/维修 |
| `aftersales_service_requests` | 售后 |

---

## 4. 财务

| 表 | 关联 |
|---|---|
| `accounting_entries` | party: customer/supplier; optional project, quote |
| `accounting_entry_lines` | FK → entries |
| `accounting_settlements` | 核销记录 |
| `customer_ledger_accounts` | 客户往来 |
| `supplier_ledger_accounts` | 供应商往来 |

---

## 5. 平台

| 表 | 用途 |
|---|---|
| `users`, `roles`, `permissions`, 关联表 | RBAC |
| `departments`, `tenants` | 组织与多租户 |
| `audit_logs` | 审计 |
| `notifications` | 通知 |
| `file_objects`, `file_relations` | 文件中心 |
| `workflow_states`, `workflow_transitions` | 工作流 |
| `system_configs` / business settings | 业务开关 |
| `realtime_events` (+ archive) | 实时事件 |
| `domain_events`, `job_executions` | 事件与任务队列 |

---

## 6. 索引与迁移治理

- 分页列表普遍按 `created_at` 排序；迁移 `fb6c0904ae35_index_created_at...` 添加索引 📄。  
- `0040_add_missing_audit_indexes_and_foreign_keys` — 审计与外键补强 📄。  
- 测试：`test_models_match_the_migration_chain`、`integration_tests/test_migration_*` — 迁移可复现性 📄。

---

## 7. 软删除与审计

- 多数业务表混入 audit soft-delete mixin（`deleted_at` / 创建人字段）📄 `base.py`。  
- Repository 层有 soft-delete 过滤覆盖测试 📄 `test_soft_delete_filter_coverage`。

---

## 8. 开放问题

| 问题 | 说明 |
|---|---|
| Quote 同时挂 product 与 machine | 历史兼容还是双主数据？需业务确认 |
| 项目与报价循环 FK | `projects.primary_quote_id` ↔ `quotes.project_id`，创建顺序需在 UI 明确 |
