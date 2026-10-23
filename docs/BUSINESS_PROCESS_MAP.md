# 核心业务流程与数据流向

> 基于代码与模型梳理（2026-10-23）。箭头表示主数据流；财务 Posting 以 accounting_entries 为中心。

---

## 1. 销售与报价

```mermaid
flowchart LR
  Customer[客户 Customer]
  Product[产品库 Product]
  Machine[机型 Machine / BOM]
  Quote[报价 Quote]
  QV[报价版本 QuoteVersion]
  QI[报价行 QuoteItem]
  Project[项目 Project]

  Customer --> Quote
  Product --> Quote
  Machine --> Quote
  Quote --> QV
  QV --> QI
  Quote --> Project
  Project --> Quote
```

**要点（📄 模型）**：

- 报价必填 `customer_id`；可选 `project_id`、`product_id`、`machine_id`、`bom_id`、成本/售价模板。  
- 项目可设 `primary_quote_id` 指向主报价。  
- 审批流：`workflow_state`、quote_approvals / 模板表；导出：quote_export_tasks + Worker。

**员工路径（目标态）**：选客户 →（可选选项目）→ 选产品/机型 → 自动带出价格模板 → 填数量 → 服务端算价 → 保存/提交审批。

**现状风险**：产品与机型双入口（见 `UX_AND_BUSINESS_SIMPLIFICATION.md` UX-001）。

---

## 2. 项目执行与成本

```mermaid
flowchart LR
  Project --> CostEst[成本核算 CostEstimate]
  Project --> Actual[实际成本 ProjectActualCost]
  Project --> WO[工单 WorkOrder]
  CostEst --> Profit[订单利润快照服务]
  Actual --> Profit
```

- 成本核算支持物料/工艺/机型行（`CostEstimate*` lines）。  
- 实际成本手工录入面板：`project-actual-costs-panel.tsx`。

---

## 3. 采购与应付

```mermaid
flowchart LR
  Supplier[供应商 Supplier]
  PE[采购单 ProcurementEntry]
  PPR[应付申请 ProcurementPayableRequest]
  AE[账目 AccountingEntry]

  Supplier --> PE
  PE --> PPR
  PPR --> AE
```

**原则**：采购单、应付、付款/核销为不同对象；金额不得简单合并重复计算（任务书 §6.4）。

---

## 4. 应收、收款与核销

```mermaid
flowchart LR
  Quote --> QRR[报价应收申请 QuoteReceivableRequest]
  Field[现场作业 FieldworkRecord]
  QRR --> AE[AccountingEntry 应收]
  Field --> AE
  AE --> Settle[AccountingSettlement 核销]
  CLA[客户台账 CustomerLedgerAccount]
  AE --> CLA
  Settle --> CLA
```

- 现场维修费用：`fieldwork_repair_billing` 迁移与 `fieldwork_receivable_service` 📄。  
- 业务开关：`quote_receivable_enabled`、`accounting_enabled`（`business_settings`）。

---

## 5. 审批与通知

```mermaid
flowchart LR
  Quote --> WF[Workflow / ApprovalTemplate]
  PE --> WF
  QRR --> WF
  PPR --> WF
  WF --> Hub[Approval Hub API]
  Hub --> Notif[Notification]
  Hub --> Audit[AuditLog]
```

移动审批端消费同一 `/approvals` 与 quote/workflow 状态（待运行验证）。

---

## 6. 产品与制造数据（并行域）

- **产品库**：分类树、成本/售价模板、标准产品报价来源。  
- **机型/BOM**：历史工业路径，选项组 option_groups、设备序列号 equipment_units、验收/安装计划（侧栏已隐藏，路由保留）。  
- **MES**：`/mes/equipment-signals`、OEE 快照 — 与 ERP 核心 loosely coupled。

---

## 7. 权限与数据范围

- JWT access/refresh 分离；realtime 短票证 📄 `security.py`。  
- 角色数据范围：迁移 `0004_role_data_scope` + 大量 `test_data_scope_*` / repository predicate 测试。  
- **服务端** `require_permissions` 为权威；前端菜单仅隐藏入口。

---

## 8. 待验证断点（第二批）

| 断点 | 说明 |
|---|---|
| 报价前端算价 vs 后端 | 必须以服务端为准做验收用例 |
| 采购→应付 Web 是否一步可见 | 需手工走单 |
| 财务核销 UI 与并发 | 需 integration_tests + 手工 |
| 演示数据 DEMO-Q-001 | `docs/DEMO_QUOTE.md` 流程 |
