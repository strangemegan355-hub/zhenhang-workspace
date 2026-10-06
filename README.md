# 振航智能制造 ERP（后端阶段一）

本仓库当前阶段交付：**标准化后端业务平台（FastAPI + PostgreSQL + Redis + JWT + RBAC + Workflow + Audit + Docker）**。

## 技术栈

- FastAPI / Uvicorn
- SQLAlchemy 2.x（Async + psycopg v3 / `postgresql+psycopg://`）
- Alembic
- PostgreSQL / Redis
- JWT（`python-jose`）+ 密码哈希（`passlib[bcrypt]`）
- Docker / Docker Compose

## 目录结构（后端）

```
backend/
  alembic/                 # 数据库迁移
  app/
    api/v1/endpoints/      # REST 路由（薄层）
    config/                # 配置（pydantic-settings）
    core/                  # 安全、依赖、RBAC 工具
    db/                    # Engine / Session
    integrations/ai/       # AI 扩展占位与约定（无业务耦合）
    models/                # SQLAlchemy ORM
    repositories/          # 数据访问层
    schemas/               # Pydantic DTO
    services/              # 领域服务/用例编排（兼容层）
    domains/               # DDD 领域入口（逐步迁移）
    main.py
  scripts/                 # 运维脚本（初始化管理员）
  tests/
  integration_tests/       # Docker PostgreSQL/Redis 集成测试
  Dockerfile
  requirements.txt
```

## 本地开发（Windows / Linux / macOS）

1. 准备 PostgreSQL + Redis（或直接用下方 Docker Compose）。
2. 复制环境变量：

```bash
cd backend
copy .env.example .env   # Windows
# cp .env.example .env     # Unix
```

3. 安装依赖并迁移：

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python scripts/bootstrap_admin.py
python scripts/seed_workflows.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

默认管理员（可被环境变量覆盖）：

- `BOOTSTRAP_ADMIN_USERNAME`（默认 `admin`）
- `BOOTSTRAP_ADMIN_PASSWORD`（**必填，无默认值**）

> **⚠️ 安全警告**
>
> 上述默认密码**仅用于本地开发与首次 bootstrap**。生产或内部试运行部署完成后，**必须立即修改 admin 密码**，并同步更换：
>
> - `SECRET_KEY`（`backend/.env.prod`）
> - `POSTGRES_PASSWORD`
> - `MINIO_ROOT_PASSWORD`
> - `METRICS_API_KEY`（生产 metrics 访问密钥）
>
> 交付验收清单见 [`docs/DELIVERY_ACCEPTANCE.md`](docs/DELIVERY_ACCEPTANCE.md)。自动化基础检查：`.\scripts\verify_delivery.ps1`

## Docker Compose（推荐）

在仓库根目录：

```bash
docker compose up --build
```

服务：

- API：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

Compose 会执行：`alembic upgrade head` → `bootstrap_admin.py` → `seed_workflows.py` → `uvicorn`。

## 本地完整启动（后端 + Web 管理端）

推荐按以下顺序启动，确保 Dashboard 可正常加载。

### 1. 启动后端

**方式 A（推荐，需可访问 Docker Hub 拉取 `python:3.11-slim`）**

在仓库根目录：

```bash
docker compose up --build
```

**方式 B（Windows 本地混合模式：基础设施用 Docker，API 用本机 Python）**

当 `docker compose build api` 因网络无法拉取基础镜像时：

```bash
# 1) 仅启动基础设施
docker compose up -d postgres redis minio

# 2) 配置后端环境（复制 backend/.env.example → backend/.env，SECRET_KEY 需 ≥32 字符）
cd backend
copy .env.example .env

# 3) 迁移与初始化（Windows 需 Python 3.11+；若 bcrypt 报错可执行 pip install bcrypt==4.0.1）
python -m alembic upgrade head
python scripts/bootstrap_admin.py
python scripts/seed_workflows.py
python scripts/seed_tenant.py
python scripts/seed_demo_quote.py

# 4) 启动 API（Windows 下使用专用入口，避免 asyncio 事件循环问题）
python scripts/run_local_api.py
```

**演示数据（DEMO_QUOTE）：** 完成上述初始化后，在 `backend` 目录执行 `python scripts/seed_demo_quote.py`，将创建 1 个客户、1 个机型、24 行 BOM 物料、1 张 draft 报价（单号 `DEMO-Q-001`）。Windows 本地请确保 `backend/.env` 中 `DATABASE_URL` 使用 `127.0.0.1` 而非 `localhost`。

**异步 Worker（导出 PDF/Excel、事件重试）：** 另开终端，在 `backend` 目录执行：

```bash
python -m workers.event_worker
```

等待 API 就绪后验证：

```bash
curl http://localhost:8000/api/v1/health/live
```

应返回 `{"code":"SUCCESS",...}` 或等价 JSON。

默认管理员（可被环境变量覆盖）：

- 用户名：`admin`（`BOOTSTRAP_ADMIN_USERNAME`）
- 密码：由 `BOOTSTRAP_ADMIN_PASSWORD` 提供（无默认值，需自行设置强口令）

### 2. 配置 Web 前端

```bash
cd apps/web-admin
copy .env.local.example .env.local   # Windows
# cp .env.local.example .env.local     # Unix
```

`.env.local` 中需包含：

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> `docker-compose.yml` 中 `CORS_ORIGINS` 已包含 `http://localhost:3000` 与 `http://127.0.0.1:3000`，供 Next.js 开发服务器跨域访问 API。

两个 Vite 应用（`apps/workshop-terminal`、`apps/mobile-app`）另用 `VITE_API_BASE_URL`，示例见各自的
`apps/<应用>/.env.example`（默认 `http://localhost:8000`）。三点容易踩：

- 该变量在 **构建时** 被写进产物（`npm run build -w workshop-terminal`）。构建后再改 `.env` 不会生效，必须重新构建。
- 它由 **运行浏览器的那台机器** 解析。车间平板或手机上的 `localhost` 指的是平板自己，因此车间终端/移动端要填
  **服务器的局域网地址**（如 `http://192.168.1.20:8000`），而不是 `localhost`。这也是 `CORS_ORIGINS` 需要包含该地址的原因。
- `vite` 的开发端口是车间终端 `5175`、移动端 `5174`，但 `npm run preview`（预览构建产物）**默认是 4173**，
  两个应用同时预览会撞端口，需显式传 `--port`，例如 `npm run preview -w workshop-terminal -- --port 4175`。

### 3. 安装依赖并启动 Web 开发服务器

在仓库根目录（monorepo）：

```bash
npm install
npm run dev -w web-admin
```

浏览器打开 [http://localhost:3000](http://localhost:3000)，使用默认管理员登录，进入 `/dashboard` 验证页面可渲染、控制台无关键 CORS/401 报错。

### 4. 常见问题

| 现象 | 排查 |
|------|------|
| 登录失败 / 401 | 确认 API 已启动、`NEXT_PUBLIC_API_BASE_URL` 指向 `http://localhost:8000` |
| CORS 报错 | 确认 `docker-compose.yml` 中 `CORS_ORIGINS` 含当前前端 origin |
| Dashboard 白屏 | 打开浏览器控制台，检查 `/api/v1/dashboard/overview` 等接口是否 200 |
| `docker compose build` 超时 | 使用上文 **方式 B** 混合启动 |
| Windows 登录 500 / asyncio | 使用 `python scripts/run_local_api.py` 而非直接 `uvicorn` |
| 端口占用 | API 默认 8000，Web 默认 3000；修改端口时需同步更新 CORS 与 `.env.local` |

## REST 入口（阶段二收口）

- `POST /api/v1/auth/login`：JWT 登录（JSON：`username` / `password`）
- `GET /api/v1/users/me`：当前用户（Bearer）
- `GET /api/v1/users/rbac-demo`：示例权限点 `system:user:read`
- `GET /api/v1/health/live`：存活探针
- `GET /api/v1/health/ready`：就绪探针（DB + Redis）
- `GET /api/v1/audits`：审计日志查询（分页/搜索/筛选）
- `POST /api/v1/workflows/seed`：初始化默认工作流种子
- `POST /api/v1/boms/items/batch`：BOM 明细批量新增（事务）
- `POST /api/v1/boms/{bom_id}/actions/transition`：BOM 状态流动作
- `POST /api/v1/configs` / `GET /api/v1/configs`：配置中心
- `POST /api/v1/files/upload` / `GET /api/v1/files`：文件中心（MinIO）
- `POST /api/v1/quotes` / `POST /api/v1/quotes/versions`：报价基础

## 阶段三（DDD 化）新增

- 领域分层：`domains/*/{application,domain,infrastructure,policies,events,repositories}`
- 领域事件：`domain_events` + `event_bus` + `event_handlers`
- 文件中心：`file_objects` / `file_relations`（支持分类、关联、预览 URL）
- 配置中心：`system_configs`
- 报价系统：`quotes` / `quote_versions` / `quote_items` / `quote_approvals`
- 报价版本自动快照 BOM 与成本，关键动作触发 domain events + audit

## 阶段三第二阶段（深化）

- 报价审批流模板：`approval_templates` / `approval_nodes` / `approval_records`
- 报价版本对比：BOM 差异、成本变化、利润变化（API diff）
- 报价导出异步任务：`quote_export_tasks`（PDF/Excel 请求与状态查询）
- 事件总线增强：`retry_count`、`dead_letter`、`process_pending`、`replay_dead_letters`
- 文件中心增强：MinIO signed url、缩略图、预览缓存、生命周期策略
- CQRS 基础目录：`app/commands`、`app/queries`

## 阶段三第二阶段收口（工业级异步）

- Worker异步架构：`task_queue` + `workers/event_worker.py`
- 事件平台：retry / dead-letter / replay / pending process
- 导出引擎：PDF（ReportLab）/Excel（OpenPyXL）异步任务化
- 报价审批策略：会签/或签、金额条件、动态审批人表达式预留
- 通知中心：`notifications`、`notification_providers`
- AI准备层：`ai_contexts`、`ai_documents`、`ai_embeddings`、`embedding_tasks`
- 文件向量化预留：上传后自动创建 AI document + embedding task

运行 worker（本地）：

```bash
cd backend
python -m workers.event_worker
```

所有 `/api/v1/**` 接口统一响应结构：

```json
{"code":"SUCCESS","message":"OK","data":{...}}
```

## 集成测试（真实 PostgreSQL + Redis + MinIO）

```bash
cd backend
docker compose -f integration_tests/docker-compose.integration.yml up -d
python -m alembic upgrade head
python scripts/bootstrap_admin.py
python scripts/seed_tenant.py
python scripts/setup_trial_users.py
pytest integration_tests -q
```

The four steps between the stack and the suite are not optional: several tests sign in as the trial accounts, and
`setup_trial_users.py`'s own docstring gives that order (`bootstrap_admin.py` first, then `seed_tenant.py`). They read
their passwords from the environment, so set throwaway values before running them — `BOOTSTRAP_ADMIN_PASSWORD` and the
`TRIAL_*_PASSWORD` variables, exactly as `.github/workflows/ci.yml` does. A failing test prints the same instructions as
`NEEDS_SEED`, so this is what its message points at.

MinIO is part of the stack because the storage lifecycle is a real dependency the suite now checks
against a live server; `INTEGRATION_MINIO_ENDPOINT` overrides its address (default `127.0.0.1:59000`).

## 数据范围与租户（现状，非目标状态）

**说清楚这一节，是因为"隔离"这两个字最容易被读成比实际更强的东西。**

**部门范围：已实现，四个面都有实测。** 范围谓词建在 service 层（`scope_predicate`、`owner_scope_user_id`），由 repository 施加；**越界一律 404 而不是 403**（403 会确认该行存在）。覆盖面：

| 面 | 证据 |
|---|---|
| 列表 | `integration_tests/test_data_scope_end_to_end.py`：两部门对比，且分页 `total` 同样带范围 |
| 单对象读 | 同上：自己的 **200**、别部门的 **404** |
| 改（`PUT`） | 同上：自己的 **200**、别部门的 **404** |
| 删（`DELETE`） | 同上：四条断言 —— 别部门的 **404**、自己的 **200**、被删的行确实消失、**被拒的行完好无损** |
| 实时通道 | `backend/tests/test_realtime_acl.py`（单元测试，按通道权限与数据范围过滤） |

**租户：未实现隔离，是"准备"。** 约八十张表中**九张带 `tenant_id` 列**，而**只有 `sys_users` 被真正写入租户**——所有业务行的 `tenant_id` 仍为 `NULL`，而实时存储的谓词是
`tenant_id = :tenant OR tenant_id IS NULL`，因此在当前数据下**它放行一切**。**所以现在跨租户并不隔离，不要按已隔离来部署。** 相关事实来源与守卫：

- `docs/ENTERPRISE_DEPLOYMENT.md` 的「多租户准备」一节；
- `backend/integration_tests/test_tenant_boundary.py`：**按行**核对上表结论，并断言九张表的集合未变——**若某业务表开始打标，它会在同一次改动里失败，并提示该表的每条读路径必须同时过滤**。

## Windows 便捷脚本

```powershell
# 启动整套（Docker 基础设施 + 本地 API、event worker、web-admin），见脚本文首注释
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-erp.ps1

# 注册开机自启（在当前用户的启动文件夹创建快捷方式，无需管理员）
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\register-erp-autostart.ps1

# 停止 start-erp.ps1 启动的三个进程（API、event worker、web admin），默认不动 Docker 基础设施
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-erp.ps1

# 先看会停什么而不真的停，或连基础设施一起停
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-erp.ps1 -DryRun
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-erp.ps1 -IncludeInfrastructure

# 验收生产前端：用构建产物启动 standalone 服务器，检查页面与它引用的每个静态资源，然后自行停掉
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-web-standalone.ps1
```

三个脚本都从自身所在位置推导仓库根目录，因此可以在任意检出路径使用。`stop-erp.ps1` 只停止命令行位于本仓库下的进程，不会碰端口上属于别人的服务。

## 生产环境注意

- **必须**设置强随机 `SECRET_KEY`（建议 32+ 字节）。
- **必须**在首次部署后修改 admin 默认密码及所有数据库/MinIO 凭证。
- **必须**在生产环境配置 `METRICS_API_KEY`；未配置时 `/api/v1/health/metrics` 返回 403。
- CORS 通过 `CORS_ORIGINS` 逗号分隔配置；不要随意使用 `*` 搭配 credentials。
- 数据库迁移以 Alembic 为准；不要在生产环境依赖 `create_all`。
- 交付验收：[`docs/DELIVERY_ACCEPTANCE.md`](docs/DELIVERY_ACCEPTANCE.md)
- **内部试运行**：[`docs/INTERNAL_TRIAL_GUIDE.md`](docs/INTERNAL_TRIAL_GUIDE.md) · `python scripts/setup_trial_users.py` · `python scripts/import_initial_master_data.py`
