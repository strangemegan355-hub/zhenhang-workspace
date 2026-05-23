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
- `BOOTSTRAP_ADMIN_PASSWORD`（默认 `Admin@123456`）

## Docker Compose（推荐）

在仓库根目录：

```bash
docker compose up --build
```

服务：

- API：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

Compose 会执行：`alembic upgrade head` → `bootstrap_admin.py` → `seed_workflows.py` → `uvicorn`。

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

## 集成测试（真实 PostgreSQL + Redis）

```bash
cd backend
docker compose -f integration_tests/docker-compose.integration.yml up -d
pytest integration_tests -q
```

## 生产环境注意

- **必须**设置强随机 `SECRET_KEY`（建议 32+ 字节）。
- CORS 通过 `CORS_ORIGINS` 逗号分隔配置；不要随意使用 `*` 搭配 credentials。
- 数据库迁移以 Alembic 为准；不要在生产环境依赖 `create_all`。
