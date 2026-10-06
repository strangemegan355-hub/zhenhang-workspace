# Package Governance

## Production UX Refinement (current phase)

QuoteWorkbench 工业操作体验：BOM 虚拟树、拖拽排序、行内公式、撤销重做、快速审批快捷键、导出区块预览、AI 分析面板、演示指南 `docs/DEMO_QUOTE.md`。

> **实测更正：上述 `QuoteWorkbench` 目前没有任何地方渲染。** 全仓库对 `QuoteWorkbench` 的引用只有它自身的定义、桶导出（`quote-builder/src/index.tsx`）、本文件的两处描述，以及一处指向它的 `@deprecated` 注释；`apps/**` 与其他包中为 0。`useUndoRedo` 的唯一消费方就是这个未渲染的组件。因此报价页实际使用的是 `BomTreeEditor`、`FormulaLivePanel`、`CostVisualization`、`ExportTemplatePicker` 等已被引用的模块，而不是这个工作台；要么接线，要么删除（530 行的 `quote-workbench.tsx` 与 68 行的 `use-undo-redo.ts`，后者同时占用 packages lint 的 1 个 error 与 1 个 warning）。

## Vertical Slice Industrialization

**Goal:** Quote → BOM → Workflow → Export → Approval → Notification → AI 全链路可演示、可交付。

| Priority | Deliverable | Status |
|----------|-------------|--------|
| Quote Builder | 列表/详情/版本对比/构建器壳 | web-admin `/quotes` |
| Approval Workflow | 后端 transition + 可用 actions API + 时间线 | 已接通 |
| Export Engine | 异步导出 + process-pending + 下载 | 已接通 |
| Notification | 未读数 + PATCH 已读 + 实时铃铛 | 已接通 |
| AI Copilot | `/ai/copilot/quote-summary` + 报价页 AI 面板 | 已接通 |
| Quote Builder | `QuoteWorkbench` — **已导出但无任何渲染方**（见顶部实测更正）；实际接通的是下方各模块 |
| BOM Tree Editor | `BomTreeEditor` + `useBomItemsQuery` |
| Formula Live | `FormulaLivePanel` + `formula-engine` |
| Cost Visualization | `CostVisualization` KPI + 结构条 |
| Approval UX | `ApprovalUxPanel` 步骤条 + 意见 + 操作 |
| Export Templates | `GET /quotes/export-templates` + `ExportTemplatePicker` |
| AI Copilot | 报价页 AI 面板 + `/ai/copilot/quote-summary` |
| Mobile App | 待审报价审批 + 通知 (`apps/mobile-app`) |
| Workshop Terminal | 产线看板 + BOM 树 (`apps/workshop-terminal`) |

**Constraints:** 不新增 `runtime-*` / `distributed-*` 包；业务闭环优先于 Runtime OS 扩张。

> **以下三张表描述的是已从本仓库移除的 Runtime OS 方向，不是当前结构。**
>
> 表中 15 个包名里只有 `formula-dag` 仍存在于 `packages/`，其余 14 个
> （`runtime-*`、`distributed-*`、`agent-*`、`consensus-*`）均已删除——删除依据正是上一节那条约束
> "不新增 `runtime-*` / `distributed-*` 包"。这些名字仍以 **20 个断裂的符号链接** 形式留在本机
> `node_modules/@zhenhang/` 下（`npm install` 会清理；它们会打断递归文件遍历）。
> 保留表格是为了记住这个被否决的方向，请勿据此认为这些包存在。

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
