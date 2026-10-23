# 代码质量与维护性计划

> 2026-10-23 基线

---

## 1. 现状

| 项 | 状态 |
|---|---|
| 后端单测 | 265 passed（架构/权限/路由对齐占比高） |
| 集成测 | 独立目录，CI 显式运行 📄 |
| 前端 lint | `npm run lint:web` 存在 |
| Python lint/format | ruff 配置存在，**未安装/未 CI 强制** 📄 |
| 类型 | TS strict（web）；Python 无 mypy |
| 重复代码 | `test_duplicate_code` 有门禁 📄 |
| OpenAPI SDK | `npm run sdk:generate` |

---

## 2. 问题

1. **双轨架构**：`services/*` 与 `domains/*` 并存，新人不知改哪。  
2. **页面级重复**：列表壳、筛选栏在多页复制（见 UI Backlog）。  
3. **globals.css 与组件内硬编码色** 并存。  
4. **README 标题滞后**于全栈现实。

---

## 3. 目标（3 个月内可达成）

| 优先级 | 动作 | 完成定义 |
|---|---|---|
| P1 | 任何 API 变更 → SDK + query-hooks 同 PR | CI 或 checklist |
| P1 | 集成测试在 Docker 上绿 | `pytest integration_tests -q` |
| P2 | 核心 service 函数 < 80 行或拆分（财务/报价优先） | review |
| P2 | Web 列表页多数走 master-list-page / data-grid | UI-T004/T005 |
| P3 | backend ruff check 非阻塞 → 警告清零后 blocking | CI job |

---

## 4. 命名与分层约定（沿用）

- 新业务能力：**model → schema → repository → service → endpoint → test → hook**。  
- 跨模块只通过 service 或明确 domain application service。  
- 金额：**Numeric/Decimal**，禁止 float 持久化（已 largely 满足，继续审查计算链）。

---

## 5. 禁止项

- 为覆盖率数字写无断言测试。  
- 大规模「仅搬家」refactor 无行为测试。  
- 前端 mock 数据进生产路径（已有 `test_page_data_use` 监测 📄）。

---

## 6. 与交付的关系

质量门禁对齐 `docs/DELIVERY_ACCEPTANCE.md` §5 与 `TEST_AND_ACCEPTANCE_REPORT.md`。
