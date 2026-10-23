# 局域网部署、备份与恢复

> 汇总现有文档并标注验证状态。详细步骤仍以 `docs/ENTERPRISE_DEPLOYMENT.md`、`README.md` 为准。

---

## 1. 启动（开发/局域网）

| 方式 | 命令 | 端口 |
|---|---|---|
| Docker 全栈 | 仓库根目录 `docker compose up --build` | API 8000 |
| 脚本 | `scripts/start-erp.ps1` | Web 3000 等 |
| 仅 Web | `npm run dev:web` | 3000 |

**验证**：`docs/DELIVERY_ACCEPTANCE.md` §1。

**本轮（2026-10-23）**：本机 API ready ✅、Web :3000 ✅、Mobile :5174 / Workshop :5175 页可达。

---

## 2. 生产 Compose

```powershell
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod config
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod up -d --build
# api/web 重建后务必 reload，否则可能 502（上游 IP 缓存）
powershell -NoProfile -File scripts\reload-prod-nginx.ps1
```

- **入口：** `http://127.0.0.1/login`（请用 **127.0.0.1**，勿用 `localhost`/IPv6；**不要**再用 `:3000`）
- **口令：** `backend/.env.prod` → `BOOTSTRAP_ADMIN_PASSWORD`（不入库）
- Nginx 反代 Web/API/WS/SSE；Web 为 Next standalone（见 DELIVERY §5）
- `NEXT_PUBLIC_API_BASE_URL` 构建为空串时走**同源** `/api`（见 K-027）

---

## 3. 数据卷

| 卷 | 用途 |
|---|---|
| `volumes/postgres` | 数据库持久化 |
| `volumes/redis` | 缓存 |
| `volumes/minio` | 对象存储（导出 PDF 等） |
| `volumes/nginx/logs` | 访问日志 |
| `volumes/backups/postgres` | 备份占位 |

---

## 4. 备份建议

1. **PostgreSQL**：定时 `pg_dump` 到 `volumes/backups/postgres` 或离线存储。  
2. **MinIO**：bucket 同步或卷快照。  
3. **配置**：安全保存 `backend/.env.prod`（不入库）。

---

## 5. 恢复演练

| 步骤 | 状态 |
|---|---|
| 从 dump 恢复到新实例 | ✅ 2026-10-23：`scripts/verify-backup-restore.ps1 -Container integration_tests-postgres-1` |
| 表行数 + alembic revision 对比 | ✅ 82 表一致；revision `fb6c0904ae35`（`logs/backup-restore-drill.txt`） |
| Web/API smoke login | ✅ 本机 API 试用账号登录 PASS（非 restore 后新实例全栈） |

操作人：Cursor 执行批次（任务书）。prod 卷全栈恢复仍 ☐。

---

## 6. 更新与回滚

- 更新：拉代码 → 构建镜像 → `alembic upgrade head` → 滚动重启  
- 回滚：保留上一版镜像 + DB 迁移 downgrade 策略（生产前必须在 staging 测 downgrade 可行性）

---

## 7. 安全边界（局域网）

- 不对公网开放 Postgres/Redis/MinIO 端口  
- Metrics 路径 IP 白名单（见 DELIVERY 4.8；`deploy/nginx/nginx.conf` 已配私网 allow）  
- 首次部署后修改 admin 密码：`python scripts/rotate_admin_password.py`（在 API 容器或连 prod DB 的环境执行；把输出口令存入密钥库 / `.env.prod`，勿提交 git）
