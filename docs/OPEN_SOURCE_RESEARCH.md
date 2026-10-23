# 开源 ERP 项目研究

> 研究方式：GitHub API + 官方 README/目录（只读，未克隆到本仓库）。  
> 日期：2026-10-23；**三次核对**同日 GitHub REST API（本会话 02:33 UTC+8 左右）。  
> **禁止**：将 GPL 代码直接并入本仓库；未审查脚本不得在生产运行。

### API 核对快照（2026-10-23 三次）

| 仓库 | stars | license | pushed_at | language | 备注 |
|---|---:|---|---|---|---|
| frappe/erpnext | 40464 | GPL-3.0 | 2026-10-23T02:15:10Z | Python | 活跃；GPL 不可移植源码 |
| asadullah48/textile-erp-platform | 0 | MIT | 2026-09-30T07:30:00Z | TypeScript | 栈最接近；规模小 |
| Narzullayev0306/seller-management-saas | 0 | MIT | 2026-09-01T11:49:59Z | Python | 幂等/outbox 思想 |
| makkyxa/erp-lite | 1 | NOASSERTION | 2026-07-23T11:56:00Z | TypeScript | 低活跃；仅结构参考 |

**本会话落地的借鉴**：核销路径采用行锁防并发超核销（对齐 Textile/Seller 并发思想，未复制其代码）。

---

## 1. ERPNext（frappe/erpnext）

| 维度 | 评分(1–5) | 依据 |
|---|---:|---|
| 业务完整度 | 5 | 4 万+ star，长期维护；制造/项目/财务/库存/CRM 齐全 📄 API |
| 前后端逻辑 | 4 | Frappe 框架 DocType 驱动；与本栈不同 |
| 数据库设计 | 5 | 成熟单据链、GL、库存账；需读 doctype 才细评 |
| 安全性 | 4 | 成熟产品；具体部署依赖配置 **未知** |
| 财务可靠性 | 5 | 行业标杆级 ERP 财务 **推断+声誉** |
| 代码规范 | 4 | 大规模 Python/JS，规范统一 |
| 自动化测试 | 3 | 有 CI；覆盖深度未逐文件统计 **未知** |
| UI/UX | 4 | Desk UI；偏传统后台 |
| 可维护性 | 3 | 全量架构迁移成本极高 |
| 可借鉴程度 | 4（思想） | 单据状态机、财务分录、权限模型；**不可**整体移植 |

- **许可证**：GPL-3.0 — 仅研究设计原则，不复制源码。  
- **维护**：2026-10-23 仍有 push。  
- **振航可取**：报价/销售订单→项目→采购→付款的单据链；金额以服务端过账为准；审批与权限绑定 DocType/Role。

---

## 2. Textile ERP Platform（asadullah48/textile-erp-platform）

| 维度 | 评分 | 依据 |
|---|---:|---|
| 业务完整度 | 3 | README 声明 Module 1 **Complete**；模块 2–5 未建 |
| 前后端逻辑 | 5 | FastAPI + Next 15，路由与权限清晰 📄 README |
| 数据库设计 | 5 | PostgreSQL **RLS FORCE** + 低权限 app 角色 |
| 安全性 | 5 | 租户隔离在 DB；CI 测 RLS/并发锁 |
| 财务可靠性 | 3 | 模块 1 偏库存/生产；完整财务未建 |
| 代码规范 | 4 | TS strict、分层 README |
| 自动化测试 | 4 | pytest 42 + 真 Postgres；Playwright smoke |
| UI/UX | 4 | shadcn/Tailwind 4，现代 SaaS |
| 可维护性 | 4 | 单模块边界清晰 |
| 可借鉴程度 | 5（工程） | **RLS 租户隔离**、least-privilege DB 角色、demo/browser adapter 思路 |

- **许可证**：MIT — 可借鉴架构模式，仍须自研业务。  
- **栈对齐度**：与本项目 **最高**（FastAPI + Next + Postgres + Alembic）。  
- **振航可取**：`require_permission` 全覆盖；迁移/应用分 DB 角色；并发库存（行锁）思想用于采购/核销防重。

---

## 3. Seller Management SaaS（Narzullayev0306/seller-management-saas）

| 维度 | 评分 | 依据 |
|---|---:|---|
| 业务完整度 | 3 | 电商卖家域，非工业 ERP；但多租户+订单+支付完整 📄 README 描述 |
| 前后端逻辑 | 4 | monorepo backend/frontend/deploy/e2e |
| 数据库设计 | 4 | Postgres RLS + Redis 📄 topics |
| 安全性 | 4 | RBAC、多租户；细节未读源码 **部分未知** |
| 财务可靠性 | 4 | 强调 idempotent checkout、outbox worker 📄 description |
| 代码规范 | 3 | 未深入 **未知** |
| 自动化测试 | 3 | 有 e2e 目录；覆盖率 **未知** |
| UI/UX | 3 | SaaS  storefront 导向 |
| 可维护性 | 4 | 清晰分层 |
| 可借鉴程度 | 4 | **幂等、Outbox、防重复提交**、CI/CD 模板 |

- **许可证**：MIT。  
- **振航可取**：关键写操作 Idempotency-Key；Worker 处理导出/通知；`.github` 工作流参考。

---

## 4. ERP Lite（makkyxa/erp-lite）

| 维度 | 评分 | 依据 |
|---|---:|---|
| 业务完整度 | 2 | 小型维修店 ERP；工单+仓库 📄 description |
| 前后端逻辑 | 3 | FastAPI + React TS |
| 数据库设计 | 3 | Postgres；规模小 |
| 安全性 | 3 | JWT+RBAC 声明 **未验** |
| 财务可靠性 | 2 | 轻量 |
| 代码规范 | 3 | **未知** |
| 自动化测试 | 2 | **未知** |
| UI/UX | 3 | 现代但简单 |
| 可维护性 | 4 | 体量小，易读 |
| 可借鉴程度 | 3 | **模块边界**、工单/客户/库存三件套简化 |

- **许可证**：Other/未断言 — 仅作结构参考，不复制代码。  
- **维护**：2026-07 后无 push，活跃度低。

---

## 5. 横向结论（服务振航）

| 主题 | 建议来源 | 振航动作 |
|---|---|---|
| 工业单据与财务链 | ERPNext 思想 | 强化 Quote→Project→Accounting 状态与过账规则文档化 |
| 租户/权限/DB 隔离 | Textile ERP | 评估是否引入 RLS（当前为应用层 data scope） |
| 幂等与异步任务 | Seller SaaS | 审查 quote export、核销、审批提交的幂等键 |
| 轻量模块划分 | ERP Lite | 合并重复入口（产品 vs 机型） |

研究已转入 `ARCHITECTURE_GAP_ANALYSIS.md` 与后续实施，不再扩大调研范围。
