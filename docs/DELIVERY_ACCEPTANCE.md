# 交付验收清单（P5）

内部试运行交付前，按本清单逐项勾选。自动化基础项可运行 `scripts/verify_delivery.ps1`。

> 勾选更新：2026-10-23（任务书严格执行批次）— 本机证据见 `logs/` 与 `TEST_AND_ACCEPTANCE_REPORT.md`。

---

## 1. 本地开发验收

| # | 项目 | 验证方式 | 通过 |
|---|------|----------|------|
| 1.1 | API health | `GET http://127.0.0.1:8000/api/v1/health/live` 返回 200 | ✅ |
| 1.2 | API ready | `GET http://127.0.0.1:8000/api/v1/health/ready` DB+Redis 正常 | ✅ |
| 1.3 | Web 登录 | http://127.0.0.1:3000/login 页 200；试用账号 API 登录 PASS | ✅ API；浏览器表单自动化不稳定 |
| 1.4 | Dashboard | `/dashboard` 壳层可开；`GET /api/v1/dashboard/overview` SUCCESS | ✅ |
| 1.5 | Quotes | `/quotes` 壳层可开；`GET /api/v1/quotes` SUCCESS；wizard 建单 `Q20261023-0002` | ✅ API；UI 列表加载需人工硬刷新确认 |
| 1.6 | Notifications | 角标 unread-count SUCCESS；列表曾 500（`page_response` 缺 schema）**已修** → SUCCESS total=0 | ✅ |
| 1.7 | Mobile | http://localhost:5174/ 200（Vite ready） | ✅ 页可达；登录+待审列表 ✅（修 K-025 后） |
| 1.8 | Workshop | http://localhost:5175/ 200（Vite ready） | ✅ 页可达；登录看板 ✅（修 K-025 后） |

**本地启动参考：** `README.md` · `docs/DEMO_QUOTE.md`

---

## 2. 生产部署验收

| # | 项目 | 验证方式 | 通过 |
|---|------|----------|------|
| 2.1 | Compose 配置 | `docker compose -f docker-compose.prod.yml --env-file backend/.env.prod config` | ✅ |
| 2.2 | 栈启动 | `docker compose ... up -d --build` 全部 healthy | ✅ 2026-10-23：DaoCloud 预拉基础镜像后 web/api/worker 建成；postgres/redis/minio/api/web/nginx/worker/maintenance 均 Up（worker healthcheck 已改无 pgrep） |
| 2.3 | Nginx → Web | http://localhost 返回管理端 HTML | ✅ `/` `/login` 200 + DOCTYPE HTML（`curl`；Invoke-WebRequest 对本机 :80 易超时） |
| 2.4 | Nginx → API | http://localhost/api/v1/health/live 返回 200 | ✅ `{"status":"ok"...}` |
| 2.5 | WebSocket | 登录后 WS 连接 `/api/v1/realtime/ws` 无持续报错 | ✅ ticket → WS 收到 `subscribe_ack` |
| 2.6 | SSE | `/api/v1/realtime/stream` 可建立长连接（或 WS 回退正常） | ✅ `ticket` 后收到 `: connected` |
| 2.7 | Worker | `docker compose logs worker` 进程存活、导出任务可完成 | ✅ worker **healthy**；prod 库导出任务未再跑（本机导出已证） |
| 2.8 | MinIO | 导出 PDF 可下载；`volumes/minio` 有数据 | ⚠️ 服务 healthy；prod 卷已挂载；导出文件以本机证据为准 |
| 2.9 | PostgreSQL | `volumes/postgres` 持久化；迁移与 seed 成功 | ✅ `volumes/postgres/data` + alembic head + bootstrap/seed_workflows |

**部署参考：** `docs/ENTERPRISE_DEPLOYMENT.md`

本机替代：`scripts/verify_delivery.ps1 -BaseUrl http://127.0.0.1:8000` → **4 PASS / 1 SKIP**（metrics）。

---

## 3. 业务闭环验收

演示数据：`python scripts/seed_demo_quote.py` → **DEMO-Q-001**

| # | 环节 | 操作 | 预期 | 通过 |
|---|------|------|------|------|
| 3.1 | 新建报价 | wizard / API | 列表出现新单 | ✅ `DEMO-Q-001` seed + 此前 wizard 单 |
| 3.2 | 保存版本 | 修改报价行 →「保存版本」 | 版本号递增 | ✅ `verify_p2_flow` → V2/V3（`logs/verify-p2-flow.txt`） |
| 3.3 | 版本对比 | 选择 V1→V2 对比 | 差异行展示 | ✅ API diff V1→V3 amount_change |
| 3.4 | 审批 | 提交审核 → 通过/驳回 | 状态流转正确 | ✅ submit→reviewing→approve→approved |
| 3.5 | 导出 PDF | 选择模板 → 导出 → 下载 | Worker 完成，文件可开 | ✅ export task completed + file_id（修复 object_name 冲突后） |
| 3.6 | 通知 | 审批/导出后 | 角标与 `/notifications` 更新 | ✅ unread 增加 + list + mark-read |
| 3.7 | 移动审批 | Mobile 待审 → 通过 | Web/看板同步 | ✅ UI：登录→选 Q20261023-0002→通过→「暂无待审批」；API：`verify_mobile_workshop_flow.py` |
| 3.8 | 车间看板 | Workshop 打开报价 | BOM 树与 KPI 刷新 | ✅ UI：登录看板→KPI 待审/已通过/OEE→点 DEMO-Q-001→BOM M01/M02；API 同脚本 |

**演示脚本：** `docs/DEMO_QUOTE.md`「正式演示顺序」

可选 API 自动化：`python backend/scripts/verify_p2_flow.py`

任务书场景 A–F（API）见 `FEATURE_ACCEPTANCE_MATRIX.md` — **已全部 ✅**。

---

## 4. 安全验收

| # | 项目 | 验证方式 | 通过 |
|---|------|----------|------|
| 4.1 | 默认密钥 | `backend/.env.prod.example` 中 SECRET_KEY / POSTGRES_PASSWORD / MINIO_ROOT_PASSWORD 为空 | ✅ |
| 4.2 | 无弱密钥入库 | `backend/.env.example` 无 `change-me`；MinIO 本地密钥已清空示例 | ✅（2026-10-23 清空 minioadmin 示例） |
| 4.3 | `.env.prod` 不入库 | `.gitignore` 含 `backend/.env.prod` | ✅ |
| 4.4 | API docs 生产关闭 | `ENVIRONMENT=production` 时 `/docs`、`/redoc` 404 | ✅ 代码：`main.py` docs_url=None if production |
| 4.5 | Metrics 保护 | 生产未配置 `METRICS_API_KEY` 时返回 403 | ✅ 代码路径存在；本机非 prod 为 200（预期） |
| 4.6 | Metrics 密钥访问 | 配置 `METRICS_API_KEY` 后需 `X-Metrics-Api-Key` | ✅ 代码路径存在 |
| 4.7 | 管理员密码 | **首次部署后已修改** admin 默认密码 | ✅ 2026-10-23 已轮换 prod DB 中 admin 哈希；新口令写入本机 `backend/.env.prod`（不入库）；脚本 `rotate_admin_password.py` |
| 4.8 | Metrics 网络隔离 | Nginx 内网/IP 白名单 | ✅ `deploy/nginx/nginx.conf`：`/api/v1/health/metrics` allow 私网+本机、deny all；API 层无 `METRICS_API_KEY` 仍 403 |

---

## 5. 构建与治理验收

```bash
npm run build:web          # ✅ 前期
npm run build:mobile       # ✅ 前期
npm run build:workshop     # ✅ 前期
npm run lint:web           # ✅ 前期
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod config  # ✅
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-web-standalone.ps1
```

| 项 | 结果 |
|---|---|
| verify-web-standalone.ps1 | ✅ `/login` 200 + 14 静态资源 OK（`logs/verify-web-standalone.txt`） |
| verify-backup-restore.ps1 | ✅ 82 表行数一致 + alembic `fb6c0904ae35`（`logs/backup-restore-drill.txt`） |
| integration_tests | ✅ 44 passed / 3 xfailed |
| unit pytest | ✅ 265 passed |

全部通过后方可签字交付。

---

## 6. 签字栏（内部试运行）

| 角色 | 姓名 | 日期 | 签字 |
|------|------|------|------|
| 开发 | | | |
| 运维 | | | |
| 业务验收 | | | |
