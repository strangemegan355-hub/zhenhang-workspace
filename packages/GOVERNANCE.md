# Package Governance

## Production UX Refinement (current phase)

QuoteWorkbench 工业操作体验：BOM 虚拟树、拖拽排序、行内公式、撤销重做、快速审批快捷键、导出区块预览、AI 分析面板、演示指南 `docs/DEMO_QUOTE.md`。

## Vertical Slice Industrialization

**Goal:** Quote → BOM → Workflow → Export → Approval → Notification → AI 全链路可演示、可交付。

| Priority | Deliverable | Status |
|----------|-------------|--------|
| Quote Builder | 列表/详情/版本对比/构建器壳 | web-admin `/quotes` |
| Approval Workflow | 后端 transition + 可用 actions API + 时间线 | 已接通 |
| Export Engine | 异步导出 + process-pending + 下载 | 已接通 |
| Notification | 未读数 + PATCH 已读 + 实时铃铛 | 已接通 |
| AI Copilot | `/ai/copilot/quote-summary` + 报价页 AI 面板 | 已接通 |
| Quote Builder | `QuoteWorkbench` — BOM 树、行编辑、公式 LIVE、成本图、审批 UX、导出模板 |
| BOM Tree Editor | `BomTreeEditor` + `useBomItemsQuery` |
| Formula Live | `FormulaLivePanel` + `formula-engine` |
| Cost Visualization | `CostVisualization` KPI + 结构条 |
| Approval UX | `ApprovalUxPanel` 步骤条 + 意见 + 操作 |
| Export Templates | `GET /quotes/export-templates` + `ExportTemplatePicker` |
| AI Copilot | 报价页 AI 面板 + `/ai/copilot/quote-summary` |
| Mobile App | 待审报价审批 + 通知 (`apps/mobile-app`) |
| Workshop Terminal | 产线看板 + BOM 树 (`apps/workshop-terminal`) |

**Constraints:** 不新增 `runtime-*` / `distributed-*` 包；业务闭环优先于 Runtime OS 扩张。

## Distributed Runtime Correctness

| Package | Role |
|---------|------|
| `runtime-transaction` | 2PC, event commit state, snapshot/recovery tx, transactional replay |
| `consensus-coordination` | Term/lease, quorum, fencing token, leader failover |
| `runtime-event-store` | Append-only log, partitions, snapshot merge, compaction, replay cursor |
| `agent-policy-engine` | Risk scoring, execution constraints, approval escalation, policy registry |
| `runtime-fault-tolerance` | Retry, circuit breaker, fallback, node isolation, degraded mode |

## Runtime Distributed Systems

| Package | Role |
|---------|------|
| `runtime-consistency` | Event ordering, idempotency, replay, snapshot versioning |
| `distributed-coordination` | Leader election, locks, membership, health |
| `runtime-storage` | Snapshot / event / graph stores + indexing |
| `agent-governance` | Quota, budget, tool policy, approval, boundaries |
| `runtime-security` | ACL, sandbox, audit, tool access graph |

## Runtime Systems Engineering

| Package | Role |
|---------|------|
| `runtime-scheduler` | Priority queue, backpressure |
| `distributed-runtime` | Pub/sub bridge, worker mesh |
| `runtime-persistence` | Checkpoint, replay, recovery |
| `formula-dag` | DAG compile, incremental recompute |
| `agent-os` | Multi-agent orchestration |

## Principles

- Protocol-first / Runtime-first / Telemetry-first / Governance-first
- core → platform → business → apps
- No business page expansion in platform phases

## CI

```bash
npm run governance:check
```
