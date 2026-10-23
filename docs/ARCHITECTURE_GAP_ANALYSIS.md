# 架构差距分析与改进方向

> 对比对象：振航现状 vs 开源研究结论（2026-10-23）

---

## 1. 当前架构优势

| 能力 | 说明 |
|---|---|
| 清晰分层 | API → Service → Repository → Model，已覆盖主业务 |
| 契约测试 | route↔frontend、hook↔route、layer parity、schema↔model 等 as of 2026-10-23：**265** 单测 |
| 领域扩展 | `domains/quote` 等 DDD 入口，可渐进迁移 |
| 共享前端包 | query-hooks + api-sdk 减少重复 fetch |
| 实时与 MES | realtime 协议、ACL、retention 测试存在 |
| 部署 | compose prod + nginx WS/SSE 文档 |

---

## 2. 差距矩阵

| 领域 | 现状 | 标杆实践 | 差距 | 建议优先级 |
|---|---|---|---|---|
| 租户隔离 | 应用层 data scope + tenant 模型 | Textile：Postgres RLS FORCE | 深度防御不足 | P2 评估 |
| 财务过账 | AccountingEntry + Settlement 服务 | ERPNext GL 分录 | 需验证书据不可篡改与冲正规则 | P1 |
| 幂等/防重 | 收款/付款核销 `FOR UPDATE`；应收/应付申请防重；审批仅 pending；confirm/void 不可捷径 | Seller：显式 idempotency key | 服务层拒绝已钉住（`test_finance_idempotency_guards`）；全链路统一 Idempotency-Key 仍可选 | P2 |
| API 类型 | 生成 SDK + hooks | OpenAPI diff CI | 已有 generate；需纳入 PR 门禁 | P2 |
| UI 系统 | 主色/侧栏已换；列表页仍分散 | 统一 Design Token + PageHeader | 部分落地 | P2 继续统一组件 |
| 测试 | 单测强；集成已跑 | Textile 有 integration + Playwright | 集成 **已绿**（lifecycle 对齐后无 xfail）；浏览器 E2E 仍以 API+关键 UI 为主 | P2 |
| 代码静态 | ruff/mypy 配置 + 非阻塞脚本 | 标杆 CI lint/typecheck | **非阻塞**基线已建（K-007）；未进 CI fail | P3 |
| 产品数据双轨 | Product + Machine 并存 | 单一 sellable item 主数据 | 侧栏产品优先；后端 `quote_track_helpers` 默认填充；字段兼容保留 | P1 余：是否禁止新建 machine-only（DECISION） |

---

## 3. 不建议的改动

- **整体替换**为 Frappe/ERPNext 或重写 Next→其他框架。  
- **大爆炸**合并 backend/services 与 domains。  
- 为追 RLS **立即**改全表策略（需 DBA 级迁移与性能评估）。

---

## 4. 分阶段架构动作（与任务书批次对齐）

### 第二批（P0/P1）— 2026-10-23 状态

1. ~~跑通 `integration_tests`~~ → 曾 **44 passed / 3 xfailed**（AbortIncomplete）；lifecycle 对齐 no-op 后该文件 **5 passed / 0 xfailed**（`logs/minio-lifecycle-align.txt`）。  
2. ~~财务重复核销~~ → `FOR UPDATE` + 超额拒绝；单元钉 `test_finance_idempotency_guards`（`logs/idempotency-audit.txt`）。  
3. ~~报价服务端算价权威~~ → `strip_client_quote_totals` + 版本行合计重算；`test_quote_track_and_totals` 回归钉住。

### 第三批（业务简化）

1. 定义「默认报价路径」：优先 Product + PriceTemplate；Machine 作为高级/历史入口。  
2. Approval Hub 统一待办模型（减少各页重复审批 UI）。

### 第四批（UI）

1. 落地 `UI_DESIGN_SYSTEM.md` token（主色 `#1677ff`）。  
2. 按 `UI-Refactor-Backlog.md` 执行 T001–T007。

### 第五批（质量门禁）

1. CI：`pytest` + `pytest integration_tests` + `build:web` + `verify-web-standalone.ps1`。  
2. 可选：引入 ruff check（仅 backend）作为非阻塞报告 → 再 blocking。

---

## 5. 前后端一致性机制（加强）

已有：

- `test_route_frontend_alignment.py`  
- `test_hook_route_alignment.py`  

建议：

- PR 模板要求：改 API 必须 `sdk:generate` + 改 hook。  
- 关键 DTO 字段变更时更新 `FEATURE_ACCEPTANCE_MATRIX` 一行。
