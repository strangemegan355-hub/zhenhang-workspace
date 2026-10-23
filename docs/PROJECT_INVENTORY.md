# 振航工业数字生态系统 ERP — 项目盘点

> **文档状态**：第一阶段复核（2026-10-23，本会话实测）  
> **证据等级**：✅ 运行/测试验证 · 📄 代码/配置确认 · 📋 文档推断 · ❓ 暂未确认

---

## 1. 仓库与 Git 状态

| 项 | 结论 | 证据 |
|---|---|---|
| 仓库路径 | `D:\cursorxiangmu\shengtaixitong` | ✅ `git rev-parse` |
| 当前分支 | `master` @ `b3dfd2d`（feat auth login failure logging） | ✅ |
| 远程 | **无 `git remote`** | ✅ |
| 工作区 | 大量已修改未提交（后端财务/主数据、Web UI、query-hooks、docs 基线等）；**已保留，未回滚** | ✅ `git status -sb` |
| stash | 空 | ✅ |

**风险（K-002）**：未提交改动体量大，协作前需明确归属；本会话仅在其上增量修复，不做 reset/clean。

---

## 2. Monorepo 结构

| 区域 | 路径 | 技术 | 说明 |
|---|---|---|---|
| Web 管理端 | `apps/web-admin` | Next.js **16.2.6**、React **19**、Tailwind **4**、TanStack Query | **41** 个 `page.tsx` |
| 移动审批 | `apps/mobile-app` | Vite + React | 单页 `App.tsx` |
| 车间终端 | `apps/workshop-terminal` | Vite + React + realtime | `App.tsx` |
| 后端 API | `backend` | FastAPI、SQLAlchemy 2 async、Alembic、JWT/RBAC | 约 **45** 个 endpoint 模块 |
| 共享包 | `packages/*`（约 29 个 workspace） | api-sdk、query-hooks、ui、realtime、workflow、quote… | |
| 部署 | `docker-compose.yml` / `.prod.yml`、`deploy/nginx` | Postgres、Redis、MinIO、API、Worker | |

根脚本：`npm run dev:web` / `build:web` / `lint:web` / `sdk:generate`。

---

## 3. 后端架构

- **分层**：endpoints → schemas → services → repositories → models；另有 `domains/` DDD 迁移中
- **迁移**：`0001` … `0041` + `fb6c0904ae35`（**head**）
- **本机 DB 版本**：曾停在 `0035_installation_plans` → 本会话已安全 `alembic upgrade head` 至 `fb6c0904ae35` ✅（仅加列/表/索引，无删数据）
- **OpenAPI**：运行中约 **171** 条路径 ✅

主要域前缀：`/auth`、`/products`、`/quotes`、`/projects`、`/procurement-entries`、`/accounting`、`/approvals`、`/mes`、`/realtime` 等。

---

## 4. Web 管理端

- 菜单：`apps/web-admin/src/lib/menu.ts`（V2.1：侧栏隐藏机型/BOM/对客独立项；财务单入口）
- 壳：`app-shell.tsx`；主色 `#1677ff`（`globals.css`）📄
- 数据：`@zhenhang/query-hooks` + `@zhenhang/api-sdk`

---

## 5. 运行环境快照（本机）

| 检查项 | 结果 |
|---|---|
| Python | 3.14.2（系统）+ `backend/.venv` |
| Node / npm | v24.14.1 / 11.11.0 |
| Docker | 29.4.3；**postgres / redis / minio Up** ✅ |
| API | `scripts/run_local_api.py` → `:8000` |
| `GET /api/v1/health/live` | ✅ 200 |
| `GET /api/v1/health/ready` | ✅ 200（修复 Redis `localhost` 后；见 K-011） |
| Web `:3000` | ✅ `npm run dev:web` Ready；`/login` HTTP 200（首编慢） |
| `backend/.env` | 存在（SECRET_KEY 已设；未在文档暴露值） |

---

## 6. 测试与 CI

| 套件 | 结果 |
|---|---|
| `cd backend && pytest -q` | ✅ **265 passed**（本会话修复 reachability 记录后；先前 264+1 fail） |
| `integration_tests` | ❓ 未跑 |
| `npm run lint:web` / `build:web` | ❓ 未跑 |
| CI `.github/workflows` | 📄 存在 |

---

## 7. 业务能力（代码存在性，非全量验收）

产品库 / 售价成本模板、报价（版本·审批·导出）、项目与实际成本、采购与应付申请、应收收款核销、审批中心、审计、权限与数据范围、MES/车间、移动与车间端入口均有 API+页面痕迹。真实验收见 `FEATURE_ACCEPTANCE_MATRIX.md`。

---

## 8. 本会话已执行动作

1. 确认仓库为 `shengtaixitong`，保护未提交改动。  
2. 修复 Windows Redis `localhost`→`127.0.0.1`，客户端超时，ready 探针限时。  
3. DB 迁移 `0035`→`fb6c0904ae35`。  
4. 更新前端可达性测试记录（Dashboard 移除的卡片）。  
5. 同步更新 `KNOWN_ISSUES.md` 等基线文档。
