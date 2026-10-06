# 交付验收清单（P5）

内部试运行交付前，按本清单逐项勾选。自动化基础项可运行 `scripts/verify_delivery.ps1`。

---

## 1. 本地开发验收

| # | 项目 | 验证方式 | 通过 |
|---|------|----------|------|
| 1.1 | API health | `GET http://localhost:8000/api/v1/health/live` 返回 200 | ☐ |
| 1.2 | API ready | `GET http://localhost:8000/api/v1/health/ready` DB+Redis 正常 | ☐ |
| 1.3 | Web 登录 | http://localhost:3000 登录 admin，进入看板 | ☐ |
| 1.4 | Dashboard | `/dashboard` KPI、面板渲染，无关键 401/CORS | ☐ |
| 1.5 | Quotes | `/quotes` 列表与 DEMO-Q-001 工作台可打开 | ☐ |
| 1.6 | Notifications | 顶栏角标、`/notifications` 列表可访问 | ☐ |
| 1.7 | Mobile | http://localhost:5174 登录、待审列表 | ☐ |
| 1.8 | Workshop | http://localhost:5175 登录、看板与 BOM 树 | ☐ |

**本地启动参考：** `README.md` · `docs/DEMO_QUOTE.md`

---

## 2. 生产部署验收

| # | 项目 | 验证方式 | 通过 |
|---|------|----------|------|
| 2.1 | Compose 配置 | `docker compose -f docker-compose.prod.yml --env-file backend/.env.prod config` | ☐ |
| 2.2 | 栈启动 | `docker compose ... up -d --build` 全部 healthy | ☐ |
| 2.3 | Nginx → Web | http://localhost 返回管理端 HTML | ☐ |
| 2.4 | Nginx → API | http://localhost/api/v1/health/live 返回 200 | ☐ |
| 2.5 | WebSocket | 登录后 WS 连接 `/api/v1/realtime/ws` 无持续报错 | ☐ |
| 2.6 | SSE | `/api/v1/realtime/stream` 可建立长连接（或 WS 回退正常） | ☐ |
| 2.7 | Worker | `docker compose logs worker` 进程存活、导出任务可完成 | ☐ |
| 2.8 | MinIO | 导出 PDF 可下载；`volumes/minio` 有数据 | ☐ |
| 2.9 | PostgreSQL | `volumes/postgres` 持久化；迁移与 seed 成功 | ☐ |

**部署参考：** `docs/ENTERPRISE_DEPLOYMENT.md`

---

## 3. 业务闭环验收

演示数据：`python scripts/seed_demo_quote.py` → **DEMO-Q-001**

| # | 环节 | 操作 | 预期 | 通过 |
|---|------|------|------|------|
| 3.1 | 新建报价 | `/quotes/new` 向导创建 | 列表出现新单 | ☐ |
| 3.2 | 保存版本 | 修改报价行 →「保存版本」 | 版本号递增 | ☐ |
| 3.3 | 版本对比 | 选择 V1→V2 对比 | 差异行展示 | ☐ |
| 3.4 | 审批 | 提交审核 → 通过/驳回 | 状态流转正确 | ☐ |
| 3.5 | 导出 PDF | 选择模板 → 导出 → 下载 | Worker 完成，文件可开 | ☐ |
| 3.6 | 通知 | 审批/导出后 | 角标与 `/notifications` 更新 | ☐ |
| 3.7 | 移动审批 | Mobile 待审 → 通过 | Web/看板同步 | ☐ |
| 3.8 | 车间看板 | Workshop 打开报价 | BOM 树与 KPI 刷新 | ☐ |

**演示脚本：** `docs/DEMO_QUOTE.md`「正式演示顺序」

可选 API 自动化：`python backend/scripts/verify_p2_flow.py`

---

## 4. 安全验收

| # | 项目 | 验证方式 | 通过 |
|---|------|----------|------|
| 4.1 | 默认密钥 | `backend/.env.prod.example` 中 SECRET_KEY / POSTGRES_PASSWORD / MINIO_ROOT_PASSWORD 为空 | ☐ |
| 4.2 | 无弱密钥入库 | `backend/.env.example` 无 `change-me` 等弱默认值 | ☐ |
| 4.3 | `.env.prod` 不入库 | `.gitignore` 含 `backend/.env.prod` | ☐ |
| 4.4 | API docs 生产关闭 | `ENVIRONMENT=production` 时 `/docs`、`/redoc` 404 | ☐ |
| 4.5 | Metrics 保护 | 生产未配置 `METRICS_API_KEY` 时 `/api/v1/health/metrics` 返回 403 | ☐ |
| 4.6 | Metrics 密钥访问 | 配置 `METRICS_API_KEY` 后需 `X-Metrics-Api-Key` 请求头 | ☐ |
| 4.7 | 管理员密码 | **首次部署后已修改** admin 默认密码 | ☐ |
| 4.8 | Metrics 网络隔离 | 建议 Nginx 内网/IP 白名单限制 metrics 路径（见 ENTERPRISE_DEPLOYMENT） | ☐ |

---

## 5. 构建与治理验收

```bash
npm run build:web
npm run build:mobile
npm run build:workshop
npm run lint:web
npm run governance:check
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod config
```

`build:web` 成功只说明构建通过，不说明构建产物**能被服务**。生产前端由 `.next/standalone` 下的
`server.js` 提供（Web 镜像与 `start-erp.ps1` 走的就是它），并且需要把 `.next/static` 与 `public` 复制进
standalone 目录。漏掉这一步时页面仍返回 200，但每个样式表与 chunk 都会 404，所以用下面的命令验收：
它会自行启动服务器、检查页面**以及页面引用的每一个静态资源**，然后总是把服务器停掉。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-web-standalone.ps1
```

全部通过后方可签字交付。

---

## 6. 签字栏（内部试运行）

| 角色 | 姓名 | 日期 | 签字 |
|------|------|------|------|
| 开发 | | | |
| 运维 | | | |
| 业务验收 | | | |
