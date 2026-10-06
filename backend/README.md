# 振航 ERP 后端

FastAPI + SQLAlchemy 2（async）+ Alembic + PostgreSQL 16 + Redis 7 + MinIO 的服务端。
`requires-python = ">=3.11"`（CI 用 3.11 验证，本地开发机亦在更高版本上通过）。

本文件同时满足 `pyproject.toml` 中 `readme = "README.md"` 的声明——此前该文件不存在，PEP 621 元数据指向了
一个缺失的文件，只是没有任何流程把后端当分发包构建，所以一直没暴露。完整说明见仓库根
[README.md](../README.md) 与 [docs/](../docs/)。

## 目录

| 路径 | 内容 |
| --- | --- |
| `app/api/v1/endpoints/` | HTTP 端点（薄层，业务在 service/domain） |
| `app/models/` `app/schemas/` | ORM 模型与 Pydantic 模型 |
| `app/services/` `app/repositories/` | 第一代分层（legacy） |
| `app/domains/` | 第二代 DDD 分层；两者并存关系由 `tests/test_layer_parity.py` 的 7 道闸门钉住 |
| `alembic/versions/` | 39 个迁移，`upgrade head` 与 `downgrade base` **双向**可用 |
| `scripts/` | 运维脚本（引导、种子、导入、校验） |
| `workers/` | 事件 worker 与维护 worker |
| `tests/` | 单元测试（111 个） |
| `integration_tests/` | 真实 PostgreSQL + Redis + MinIO 的集成测试 |
| `requirements.txt` | 运行依赖；镜像与 CI 都用它，不走 `pip install .` |

## 本地运行

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python scripts/run_local_api.py
```

`run_local_api.py` 会先设置 Windows 的 Selector 事件循环策略再导入应用。**直接 `uvicorn app.main:app`
会失败**（`Psycopg cannot use the 'ProactorEventLoop'`），因为 uvicorn 在导入应用之前就已建好事件循环，
`app/main.py` 里的设置来不及生效——根 README 的排障表记录的也是这一点。

## 初始化数据

按此顺序执行；调换顺序会失败并给出提示：

```bash
python scripts/bootstrap_admin.py          # 需要 BOOTSTRAP_ADMIN_PASSWORD（无默认值，至少 12 位）
python scripts/setup_trial_users.py        # 试运行账号与角色；admin 用户须已存在
python scripts/seed_demo_quote.py          # 可选：DEMO-Q-001 演示报价
python scripts/import_initial_master_data.py --dir data/import_samples --dry-run
python scripts/import_initial_master_data.py --dir data/import_samples
```

用户导入依赖 `setup_trial_users.py` 建的角色（`trial_sales`、`trial_tech`）；缺少时脚本会逐行报
`role not found`，并且**整批回滚**、退出码为 1。导入本身是幂等的：第二次运行报告
`created=0 skipped_duplicates=12 errors=0` 且行数不变。

## 测试

```bash
pytest                      # 仅单元测试
pytest integration_tests    # 需要真实 PostgreSQL / Redis / MinIO
```

`pyproject.toml` 的 `testpaths = ["tests"]` 是有意为之：集成测试需要真实服务，因此裸跑 `pytest` 只收集单元
测试，**它的通过不代表集成套件也通过**。集成套件由 `.github/workflows/ci.yml` 显式运行。

Python 侧目前**没有 linter 或类型检查器**：`[tool.ruff]` 已配置但无人执行（ruff 不在依赖中），`mypy` 与
`pytest-cov` 也未安装。类型与 lint 门禁都在 TypeScript 一侧（4 个 `tsc` 与 ESLint）。
