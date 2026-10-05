# Enterprise Stabilization — 部署与运维

## 事件生命周期（realtime_events）

| 阶段 | 默认策略 | 环境变量 |
|------|----------|----------|
| 热数据（在线 replay） | 7 天 | `REALTIME_HOT_RETENTION_DAYS` |
| Replay API 可查范围 | 3 天 | `REALTIME_REPLAY_RETENTION_DAYS` |
| 归档表保留 | 90 天 | `REALTIME_ARCHIVE_RETENTION_DAYS` |

流程：超过热保留期 → 批量迁入 `realtime_events_archive` → 超过归档保留期物理删除。

维护任务：`python -m workers.maintenance_worker`（`docker-compose.prod.yml` 中 `maintenance` 服务）。

## 监控指标

`GET /api/v1/health/metrics` — **生产环境受 `METRICS_API_KEY` 保护**（见下文）。

| 环境 | 行为 |
|------|------|
| 开发（`ENVIRONMENT=development`） | 未设置密钥时可匿名访问 |
| 生产（`ENVIRONMENT=production`） | **未设置 `METRICS_API_KEY` → 403 禁用** |
| 生产 + 已设置密钥 | 请求头 `X-Metrics-Api-Key: <METRICS_API_KEY>` 方可访问 |

在 `backend/.env.prod` 中配置：

```bash
METRICS_API_KEY=<openssl rand -hex 24>
```

抓取示例：

```bash
curl -H "X-Metrics-Api-Key: $METRICS_API_KEY" http://localhost/api/v1/health/metrics
```

**建议：** 在 Nginx 层对 `/api/v1/health/metrics` 增加内网 IP 白名单，与 API Key 双重限制。

| 分类 | 指标 |
|------|------|
| API | `request_total`, `error_total`, `avg_request_ms`, `last_request_ms` |
| Realtime | `ws_connections_active`, `sse_connections_active`, `reconnect_total`, `replay_*`, `events_hot/archive_count` |
| Export | `export_total`, `export_duration_ms_last`, `export_failures_total` |
| Worker | `queue_backlog_pending`, `queue_backlog_dead_letter`, `worker_failures_total` |
| Retention | `archived_last_run`, `purged_last_run` |

探针：`/api/v1/health/live`、`/api/v1/health/ready`。

---

## 生产启动步骤

### 1. 准备环境变量

```bash
cp backend/.env.prod.example backend/.env.prod
```

编辑 `backend/.env.prod`，**必须**填写（不允许留空）：

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | 强密码 |
| `MINIO_ROOT_PASSWORD` | 强密码 |
| `MINIO_ACCESS_KEY` | MinIO 用户名（非默认 `minioadmin`） |

`ENVIRONMENT=production` 已预置；此模式下 API 自动关闭 `/docs`、`/redoc`、`/openapi.json`。

`NEXT_PUBLIC_API_BASE_URL` 留空表示与 Nginx 同源（推荐）。修改后需 **重新 build web 镜像**。

> **⚠️ 安全警告 — 首次部署后必须立即修改**
>
> 1. **admin 默认密码**（bootstrap 脚本创建，默认 `Admin@123456`）— 通过管理端或数据库修改  
> 2. **`SECRET_KEY`** — `openssl rand -hex 32`  
> 3. **`POSTGRES_PASSWORD`** — 强密码，勿使用示例值  
> 4. **`MINIO_ROOT_PASSWORD`** — 强密码，勿使用 `minioadmin`  
> 5. **`METRICS_API_KEY`** — 生产环境必须设置，否则 metrics 接口禁用  
>
> `backend/.env.prod` **不得提交到 Git**。

### 2. TLS 证书

将正式证书放入：

```
deploy/nginx/certs/fullchain.pem
deploy/nginx/certs/privkey.pem
```

内部试运行可生成自签证书：

```bash
sh deploy/nginx/certs/generate-self-signed.sh
```

### 3. 启动

```bash
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod config   # 校验
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod up -d --build
```

可选：水平扩展 worker（Compose 非 Swarm 模式用 `--scale`）：

```bash
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod up -d --scale worker=2
```

### 4. 验证

| 检查项 | 方式 |
|--------|------|
| Web 首页 | http://localhost |
| API 探活 | http://localhost/api/v1/health/live |
| 登录 | 默认 `admin` / `Admin@123456`（bootstrap 脚本创建） |
| Nginx 路由 | `/` → web:3000，`/api` → api:8000 |

---

## 如何替换 `.env.prod`

1. 停止栈：`docker compose -f docker-compose.prod.yml --env-file backend/.env.prod down`
2. 编辑 `backend/.env.prod`
3. 若改了 `NEXT_PUBLIC_API_BASE_URL`：`docker compose ... up -d --build web`
4. 若只改后端密钥/数据库：重建 api/worker/maintenance 即可

Compose 通过 `--env-file backend/.env.prod` 做 `${SECRET_KEY}` 等变量替换；各服务同时挂载该文件为容器 env。

---

## 持久化目录

数据统一落在 `./volumes/`：

| 路径 | 用途 |
|------|------|
| `volumes/postgres` | PostgreSQL 数据 |
| `volumes/minio` | 对象存储 |
| `volumes/redis` | Redis AOF |
| `volumes/nginx/logs` | Nginx 访问/错误日志 |
| `volumes/backups/postgres` | `backup-postgres.sh` 输出 |

---

## 数据库备份与恢复

### 备份（gzip + 保留策略）

```bash
sh deploy/backup/backup-postgres.sh
```

默认保留 14 天（`RETAIN_DAYS`），输出 `volumes/backups/postgres/erp_db_YYYYMMDD_HHMMSS.sql.gz`。

### 恢复

```bash
# 停止写入端
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod stop api worker maintenance

gunzip -c volumes/backups/postgres/erp_db_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml --env-file backend/.env.prod exec -T postgres \
  psql -U erp -d erp_db

docker compose -f docker-compose.prod.yml --env-file backend/.env.prod start api worker maintenance
```

---

## 如何查看 worker 日志

```bash
# 所有 worker 实例
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod logs -f worker

# 最近 200 行
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod logs --tail=200 worker
```

---

## 如何重启单个服务

```bash
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod restart nginx
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod restart api
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod restart web
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod restart worker
```

重建单个服务：

```bash
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod up -d --build web
```

---

## WebSocket / SSE 注意事项

Nginx 已单独配置：

| 路径 | 说明 |
|------|------|
| `/api/v1/realtime/ws` | WebSocket：`Upgrade` / `Connection: upgrade`，读超时 3600s |
| `/api/v1/realtime/stream` | SSE：`proxy_buffering off`，禁用缓存 |

**同源部署**：`NEXT_PUBLIC_API_BASE_URL` 留空，浏览器经 `http(s)://your-host/api/...` 访问，WS/SSE 与 Cookie 同域。

**跨域部署**：设置 `NEXT_PUBLIC_API_BASE_URL=https://api.example.com` 并 rebuild web；同时配置 `CORS_ORIGINS` 与 `REALTIME_PUBLIC_BASE_URL`。

`client_max_body_size 100m` 已全局启用，支持大文件上传/导出。

---

## 生产组件

| 服务 | 说明 |
|------|------|
| **web** | Next.js standalone（`:3000` 内网） |
| **api** | FastAPI，2 uvicorn workers |
| **worker** | 事件消费 / PDF 导出 |
| **maintenance** | 实时事件归档 |
| **nginx** | `:80` HTTP + `:443` HTTPS，统一入口 |
| **postgres / redis / minio** | 基础依赖 |

所有核心服务配置 `restart: unless-stopped` 与 healthcheck（api/worker/web/nginx）。

---

## 多租户准备

- 表 `tenants`，字段 `tenant_id` 已加入用户、报价、主数据、实时事件。
- 默认租户：`DEFAULT_TENANT_CODE=default`，`python scripts/seed_tenant.py` 回填。

## MES / OEE 基础

- `POST /api/v1/mes/equipment-signals` — 设备信号接入
- `GET /api/v1/workshop/board` — 车间看板

后续可对接 OPC-UA / MQTT 采集服务写入上述 API。
