# 已知问题与风险清单

> 更新时间：2026-10-23（NON-UI batch：MinIO lifecycle 对齐、K-005 helpers、K-007 非阻塞 lint）  
> 优先级：**P0** 严重 · **P1** 核心业务 · **P2** 体验/维护 · **P3** 一般优化

| ID | 级别 | 问题 | 影响 | 状态 | 证据 |
|---|---|---|---|---|---|
| K-001 | P2 | Windows 下 `pytest` 未设置 `pythonpath` 时 `test_admin_plane.py` 收集失败 | 本地误报测试不可用 | **已修复** | `backend/pyproject.toml` 增加 `pythonpath = ["."]` |
| K-002 | P2 | 工作区大量未提交修改，来源不明 | 协作/回滚困难 | **已缓解**：交付检查点 `a60c81c`（2026-10-23） | `git log -1` |
| K-003 | P2 | UI 主色与任务书目标不一致（曾用 Frappe 黑灰 `#171717`，目标 `#1677ff`） | 品牌与现代化方向偏差 | **已修复**（2026-10-23） | `globals.css` + `app-shell` 深蓝侧栏 |
| K-004 | P2 | `menu.ts` 注释称部分菜单「隐藏」，但 BOM/机型等仍在侧栏展示 | 信息架构文档与 UI 不一致 | **已修复**（2026-10-23） | 机型/BOM/选项组/验收/安装标 `hidden` |
| K-005 | P1 | **产品库 vs 机型管理** 双轨：报价可关联 product_id 或 machine_id | 员工不知选哪条路径、数据重复维护风险 | **后端部分修复**：`quote_track_helpers` 产品优先默认填充；schema 偏好 product；字段兼容保留。是否禁止新建 machine-only → **DECISION-NEEDED** | `quote_track_helpers.py`；UX-001 |
| K-006 | P2 | 首页 Dashboard 多卡片/图表，是否均接真实 API 未在本轮点击验证 | 可能展示空数据或低价值指标 | **门禁已验**：财务/审批/工单卡按权限显隐；静态矩阵 + 四角色 headless `RESULT=PASS`（trialadmin/finance/sales/workshop）。「按角色换整套布局」仍 ☐ | UX-006；`logs/dashboard-role-cards-out.txt`；`run-dashboard-role-cards.mjs` |
| K-007 | P3 | 后端无 enforced ruff/mypy（pyproject 自述） | 风格与类型漂移 | **非阻塞已落地**：ruff+mypy 配置 + `scripts/check_backend_lint.py`；基线 `logs/ruff-backend-baseline.txt`；未进 CI fail | K-007；`check_backend_lint.ps1` |
| K-008 | P1 | 集成测试与 E2E 未在本轮执行 | 财务/权限/事务回归风险 | **已跑**：MinIO AbortIncomplete（#16120）对齐 lifecycle no-op；integration xfails 消除；浏览器 E2E 仍以 API+局部 UI 为主 | `logs/nonui-smoke-*.txt`；`logs/minio-lifecycle-align.txt` |
| K-009 | P2 | 本机 API / ready 不可用 | 无法试运行验收 | **已缓解**：API 已起；ready 已通 | live/ready 200 |
| K-010 | P2 | README 仍以「后端阶段一」为主标题，与全栈现状不完全匹配 | 新人误解范围 | **已修复**（2026-10-23） | README 改为全栈标题与目录摘要 |
| K-011 | P0 | Windows 上 `REDIS_URL=redis://localhost` 连不上（IPv6），`/health/ready` 挂死；依赖 Redis 的请求风险 | 就绪探针失败、业务可能卡住 | **已修复**（2026-10-23） | `.env`→`127.0.0.1`；`redis_client` 超时；ready `wait_for`；单测 setdefault 同步 |
| K-012 | P1 | 本机 Alembic 停在 `0035`，落后 head（缺 supplier_ledger、due_date、售后表、审计索引等） | 财务/售后与代码不一致 | **已修复**：`alembic upgrade head` → `fb6c0904ae35` | 迁移日志；无删业务行 |
| K-013 | P2 | Dashboard 移除 `RecentFilesCard`/`WorkflowProgressCard` 后前端可达性测试失败 | CI/本地 pytest 红 | **已修复**：记入 `REFERENCED_NOWHERE` | `test_frontend_reachability.py` |
| K-014 | P2 | 无 git remote | 无法推送备份到远端 | 已知 | `git remote -v` 空 |
| K-015 | P1 | 收款/付款核销读改写无行锁，并发可能超核销 | 财务余额不准 | **已修复**（2026-10-23） | `get_entry(for_update=True)` + 核销金额 >0 校验 |
| K-016 | P1 | 试用角色权限漂移：只增不减；workshop 缺 mes/workshop；finance/boss 残留 `platform:config`；finance 无记账权限 | 越权或无法做财务 | **已修复**（2026-10-23） | `setup_trial_users` 精确同步；`verify_permissions` All checks passed |
| K-017 | P0 | 收款/付款核销 `FOR UPDATE` 与 entry 的 `lazy=joined` 外键冲突，Postgres 报错 500 | 财务收款不可用 | **已修复**（2026-10-23） | `get_entry(for_update)` 使用 `noload(*)` + `of=AccountingEntry` |
| K-018 | P2 | 试用角色无 `platform:config:*`，无法经 API 改业务开关 | 试点无法开功能 | **已修复** | `business:settings:read/update` 给 trialadmin；端点 `require_any_permission`；finance 仍 403 |
| K-019 | P1 | 项目 summary 对 ORM Quote 校验失败（缺 `from_attributes`）→ 500 | 项目盈亏面板不可用 | **已修复** | `ProjectLinkedQuote/CostEstimate` 增加 `from_attributes` |
| K-020 | P1 | 登录 `<form>` 未强制 `method="post"` / `preventDefault` 时，原生提交会把用户名口令打进 URL query | 凭据进历史/代理日志；自动化工具易踩中 | **已修复**（2026-10-23） | `login-form-panel.tsx`：`method="post"` + 显式 `e.preventDefault()` |
| K-021 | P2 | 报价中心左侧列表 `loading` 依赖 `machinesQuery.isLoading`，机型为隐藏旧路径时仍会拖住产品首路径列表 | 列表长期「加载报价列表…」，客户/产品下拉空 | **已修复**（2026-10-23） | `quotes/page.tsx`：`masterLoading` 仅客户+产品 |
| K-022 | P1 | `apiClient` / token store 曾在 `useEffect` 注册，首屏 React Query 可能在注册前发起请求（相对 URL 打到 Next 源） | 列表挂起 loading、下拉无数据 | **已修复**（2026-10-23） | `providers.tsx` 模块顶层设置 `baseURL` + `registerTokenStore`；IDE Browser 自动化下仍偶发无 XHR，需人工刷新确认 |
| K-023 | P1 | 报价导出 `object_name=quoteId-taskId` 重试时撞 `ix_file_objects_object_name`；且 `push_quote_export_status` 引用未定义 `quote` | 导出 500 | **已修复**（2026-10-23） | `quote_export_handlers.py`：object_name 加 uuid 后缀；owner_id 取自 payload |
| K-024 | P2 | 本机 `docker compose.prod up --build` 无法拉 Docker Hub 镜像（IPv6 连 registry-1.docker.io 超时） | §2 prod 全栈验收阻塞 | **已缓解**：DaoCloud 预拉 `python:3.11-slim`/`node:20-alpine` 后栈已起 | `logs/prod-compose-up*.txt` |
| K-025 | P1 | `@zhenhang/http-client` 顶层读 `process.env`，Vite 浏览器无 `process` → Mobile/Workshop 白屏 | §3.7/§3.8 无法登录 | **已修复**（2026-10-23） | `packages/http-client`：`resolveDefaultApiBaseUrl` 守卫 `typeof process` |
| K-026 | P2 | prod web 构建：lightningcss musl / 缺根 tsconfig / Field `type` 拓宽；postgres 挂 `.gitkeep` 导致 initdb 失败；CORS 需 JSON；`QuoteCreate` 自引用注解；maintenance 缺 MINIO_SECRET_KEY；worker healthcheck 依赖 pgrep | §2 启动连环失败 | **已修复**（2026-10-23） | Dockerfile/compose/quote.py/acceptance+installation；栈 healthy |
| K-027 | P1 | prod Web 构建时 `NEXT_PUBLIC_API_BASE_URL` 为空仍回退到 `http://127.0.0.1:8000`，登录打到本机开发库 →「密码不正确」 | 用 prod 口令无法登录管理端 | **已修复**（2026-10-23） | `providers`/`http-client`：空串=同源；web 镜像重建 |
| K-028 | P2 | 核心列表页（报价/采购/财务）曾各自手写页头与筛选，金额列对齐不一致 | 操作路径跳变、金额难扫读 | **已修复 + 视口 PASS**（2026-10-23） | DataGrid 列级 `align`；`logs/viewport-core-lists-out.txt` → `RESULT=PASS`：报价/采购/财务/审批金额右齐；审批曾缺待办样本，已用 TRIAL-PR-0002 补齐后 `right=4/4`（`logs/approvals-money-align-*.txt`） |
| K-029 | P2 | Playwright/headless 登录无 `/auth/login`；报价列表长期「加载报价列表…」 | 纯 UI E2E 不可用；视口金额扫读失败 | **已修复**（2026-10-23） | **根因 1：** Next 16 默认拦截 `127.0.0.1` 访问 `/_next/*` → 客户端不 hydration（`allowedDevOrigins`）。**根因 2：** 报价 `loading` 误绑 `customersQuery`（boss 无 `master:customer:read` 时 403 重试拖死列表）。**根因 3：** admin layout 在 zustand persist 水合前误跳登录。修复：`next.config.ts` `allowedDevOrigins`；登录 FormData+hydration 门闩；报价 `loading` 仅 `listQuery`；layout 等 `persist.hasHydrated`。视口仍保留 API+localStorage 注入兜底；`playwright-core` 已装，**未**装 `@playwright/test`（脚本不依赖它） |
| K-030 | P1 | `GET /procurement-entries` `response_model` 误为 `PageResponse[AccountingEntryRead]`；空列表时无校验、有行则 FastAPI 500 | 采购页无法展示试用/真实请购金额；视口采购金额不可验 | **已修复**（2026-10-23） | 改为 `PageResponse[ProcurementEntryRead]`；静态单测 `test_procurement_list_response_model`；试用种子 `seed_trial_money_viewport.py` 开记账 + TRIAL 材料/请购/draft 账；视口 `RESULT=PASS` 采购 `right=9/9`、财务 `right=3/3` |

> 试用种子策略（2026-10-23 负责人确认 / `43896d6`）：`seed_trial_money_viewport.py` **固定**开启记账相关三开关，仅本地试用库；默认拒绝非本机 URL，生产禁盲跑（`--allow-non-local` 才可覆盖）。可选 `--with-pending-approval`（**默认关**）额外种一条 TRIAL 采购应付 pending，供审批金额视口；不审批、不 confirm/void。  
> **端口脚枪**：`backend/.env` 默认常为 **5432**（compose），本机试用/API 常连集成栈 **55432**；种子/视口/审批证据必须以与 API 同一 `DATABASE_URL` 为准（见 README）。  
> **无 git remote**（K-014）：无法 push 远端备份。

### 安全类（详见 `SECURITY_REVIEW.md`）

| ID | 级别 | 问题 | 状态 |
|---|---|---|---|
| S-001 | P0 监控项 | 生产必须轮换 bootstrap 密码与 `SECRET_KEY` 等 | **已轮换** prod admin（§4.7）；`SECRET_KEY`/MinIO 为本机 `.env.prod` 非默认值 |
| S-002 | — | 单元测试覆盖：无默认弱密码、token 类型分离、登录枚举防护、审计脱敏等 | ✅ as of 2026-10-23：265 tests 通过（架构/安全向测试占比较高） |

---

## 处理原则

- P0：阻塞交付，先修再扩功能。  
- P1：核心闭环（报价→项目→采购→财务）优先于 UI 美化。  
- 所有「已修复」须附命令输出或手工步骤，禁止仅改文档宣称通过。
