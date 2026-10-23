# 安全审查（基线）

> 2026-10-23 — 以代码与 **265 项单元/架构测试** 为主；**未**做渗透测试或生产配置审计。

---

## 1. 认证与凭证

| 项 | 结论 | 证据 |
|---|---|---|
| 密码哈希 | bcrypt（passlib） | `core/security.py` 📄 |
| JWT 类型分离 | access / refresh / realtime ticket 分 `typ` | `security.py` + `test_token_types` ✅ |
| 登录枚举 | 失败路径与 dummy hash | `test_login_enumeration` ✅ |
| 登录失败记录 | 近期提交 feat(auth) | git log 📄 |
| Bootstrap 密码 | 无默认弱密码；`BOOTSTRAP_ADMIN_PASSWORD` 必填 | README + `test_no_default_credentials` ✅ |

---

## 2. 授权

| 项 | 结论 | 证据 |
|---|---|---|
| 端点权限依赖 | `require_permissions` 广泛使用 | `test_authorization_dependencies` ✅ |
| 数据范围 | repository predicate + scope 测试 | `test_data_scope_*` ✅ |
| Admin 面提升 | admin plane 单测 | `test_admin_plane.py` ✅ |
| 前端隐藏 ≠ 安全 | 测试强调服务端 | 架构测试文化 📄 |

---

## 3. 配置与密钥

| 项 | 结论 | 证据 |
|---|---|---|
| 仓库内无提交密钥 | 扫描测试 | `test_no_committed_secrets` ✅ |
| `.env.prod` 不入库 | 交付清单 | `DELIVERY_ACCEPTANCE.md` 📄 |
| 生产 Swagger 关闭 | 环境开关 | 交付清单 4.4 📄 |
| Metrics API Key | 生产 403/密钥头 | 交付清单 4.5–4.6 📄 |

**本轮未验证**：实际 `backend/.env` / 生产服务器是否存在弱 `SECRET_KEY`（仅确认本地已设置、长度 >32，未记录值）。

**本会话运行时**：发现 Windows 上 `REDIS_URL=redis://localhost` 导致连接超时（IPv6）；已改为 `127.0.0.1` 并给 Redis 客户端加连接超时，避免探针与依赖 Redis 的路径无限挂起（见 `KNOWN_ISSUES` K-011）。

---

## 4. Web 与传输

| 项 | 结论 | 证据 |
|---|---|---|
| CORS 配置 | 有单测 | `test_cors_configuration` ✅ |
| 安全响应头 | 有单测 | `test_web_security_headers` ✅ |
| Realtime ACL | channel 级 | `test_realtime_acl` ✅ |
| 上传大小限制 | settings 边界 | `test_upload_size_limit` ✅ |

---

## 5. 审计与日志

| 项 | 结论 | 证据 |
|---|---|---|
| 审计 payload 脱敏 | 不测 secrets 进 audit | `test_audit_payload_secrets` ✅ |
| Audit 索引/FK | 迁移 0040 | 📄 |

---

## 6. 依赖与镜像

| 项 | 状态 |
|---|---|
| 容器镜像漏洞扫描 | ❓ 未跑 |
| Python/npm CVE | ❓ 未跑 |

---

## 7. 备份与恢复

| 项 | 状态 |
|---|---|
| `volumes/postgres`、`deploy/backup` | 目录存在 📄 |
| 恢复演练 | ❓ 见 `DEPLOYMENT_AND_BACKUP_GUIDE.md` |

---

## 8. P0/P1 整改跟踪

| ID | 描述 | 状态 |
|---|---|---|
| SEC-01 | 生产环境强制轮换 admin 与基础设施密码 | 流程文档化；**环境待验** |
| SEC-02 | 局域网 metrics/Redis/Postgres 端口暴露边界 | 见 ENTERPRISE_DEPLOYMENT；**待验** |
| SEC-03 | 集成测试覆盖租户边界 | 测试存在；**待执行** `test_tenant_boundary` |

---

## 9. 结论

- **代码层**安全基线较好：认证分类型、权限与 scope 测试密集、无明文密钥测试失败。  
- **运行层**与**财务越权/事务**仍需 integration + 手工验收后才能声称生产就绪。
