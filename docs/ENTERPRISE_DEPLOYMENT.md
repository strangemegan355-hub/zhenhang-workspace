# Enterprise Stabilization — 部署与运维

## 事件生命周期（realtime_events）

| 阶段 | 默认策略 | 环境变量 |
|------|----------|----------|
| 热数据（在线 replay） | 7 天 | `REALTIME_HOT_RETENTION_DAYS` |
| Replay API 可查范围 | 3 天 | `REALTIME_REPLAY_RETENTION_DAYS` |
| 归档表保留 | 90 天 | `REALTIME_ARCHIVE_RETENTION_DAYS` |

流程：超过热保留期 → 批量迁入 `realtime_events_archive` → 超过归档保留期物理删除。

分区扩展（数据量 > 千万行时）：对 `realtime_events` 按 `created_at` 做 PostgreSQL RANGE 月分区，detach 旧分区至冷存储。当前实现为**归档表 + 索引**以降低运维复杂度。

维护任务：`python -m workers.maintenance_worker`（`docker-compose.prod.yml` 中 `maintenance` 服务）。

## 监控指标

`GET /api/v1/health/metrics`（无需包装在业务权限内，建议生产用 Nginx IP 白名单或内网抓取）

| 分类 | 指标 |
|------|------|
| API | `request_total`, `error_total`, `avg_request_ms`, `last_request_ms` |
| Realtime | `ws_connections_active`, `sse_connections_active`, `reconnect_total`, `replay_*`, `events_hot/archive_count` |
| Export | `export_total`, `export_duration_ms_last`, `export_failures_total` |
| Worker | `queue_backlog_pending`, `queue_backlog_dead_letter`, `worker_failures_total` |
| Retention | `archived_last_run`, `purged_last_run` |

探针：`/api/v1/health/live`、`/api/v1/health/ready`。

## 生产部署

```bash
cp backend/.env.example backend/.env.prod
# 编辑 SECRET_KEY、POSTGRES_PASSWORD、CORS_ORIGINS 等

# TLS：将证书放入 deploy/nginx/certs/fullchain.pem 与 privkey.pem

docker compose -f docker-compose.prod.yml --env-file backend/.env.prod up -d --build
```

组件：

- **api**：2 uvicorn workers
- **worker**：`WORKER_REPLICAS` 可水平扩展（默认 2）
- **maintenance**：事件归档与指标刷新
- **nginx**：HTTPS + WebSocket/SSE 长连接

备份：`deploy/backup/backup-postgres.sh`（建议 cron 每日执行）。

## 多租户准备

- 表 `tenants`，字段 `tenant_id` 已加入用户、报价、主数据、实时事件。
- 默认租户：`DEFAULT_TENANT_CODE=default`，`python scripts/seed_tenant.py` 回填。
- Replay / ACL 按 `tenant_id` 过滤（空 tenant_id 视为全局兼容数据）。

## MES / OEE 基础

- `POST /api/v1/mes/equipment-signals` — 设备信号接入
- `GET /api/v1/mes/equipment-signals` — 近期信号
- `POST /api/v1/mes/oee-snapshots` — OEE 快照
- 车间看板 `/api/v1/workshop/board` 合并 MES 数据（若存在）

后续可对接 OPC-UA / MQTT 采集服务写入上述 API，无需新增 runtime 包。
