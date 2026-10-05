# 内部试运行操作手册

面向公司内部小范围试运行（P6）。不新增业务功能，按角色使用现有 Web / Mobile / Workshop 端。

---

## 1. 环境准备与启动

### 1.1 一次性初始化（服务器）

```bash
# 生产栈
cp backend/.env.prod.example backend/.env.prod
# 填写 SECRET_KEY、POSTGRES_PASSWORD、MINIO_ROOT_PASSWORD、METRICS_API_KEY

docker compose -f docker-compose.prod.yml --env-file backend/.env.prod up -d --build

# 试运行用户与权限（容器内或本机 backend 目录）
cd backend
python scripts/setup_trial_users.py
python scripts/seed_demo_quote.py          # 可选演示单 DEMO-Q-001
python scripts/import_initial_master_data.py --dir data/import_samples   # 可选真实主数据
```

### 1.2 本地混合启动（开发/彩排）

```powershell
docker compose up -d postgres redis minio
cd backend
python scripts/run_local_api.py
# 另开终端
python -m workers.event_worker
# Web
npm run dev:web
```

### 1.3 自动化检查

```powershell
.\scripts\verify_delivery.ps1
cd backend
python scripts/verify_permissions.py
```

---

## 2. 登录

| 入口 | 地址 |
|------|------|
| Web 管理端 | http://localhost （生产）/ http://localhost:3000 （开发） |
| 移动审批 | http://localhost:5174 |
| 车间终端 | http://localhost:5175 |

**试运行账号**（执行 `setup_trial_users.py` 后生效）：

口令不再有默认值。为每个账号设置对应的环境变量，或让 `setup_trial_users.py` 生成随机口令
（生成的随机口令只在脚本本次输出中显示一次）：

| 角色 | 用户名 | 口令来源 |
|------|--------|----------|
| 老板 | boss | `TRIAL_BOSS_PASSWORD` |
| 试运行管理员 | trialadmin | `TRIAL_ADMIN_PASSWORD` |
| 销售 | sales01 | `TRIAL_SALES_PASSWORD` |
| 技术 | tech01 | `TRIAL_TECH_PASSWORD` |
| 车间 | workshop01 | `TRIAL_WORKSHOP_PASSWORD` |
| 财务 | finance01 | `TRIAL_FINANCE_PASSWORD` |
| 审批人 | approver01 | `TRIAL_APPROVER_PASSWORD` |

> **⚠️ 首次登录后必须修改密码。** 系统暂未实现强制改密，由部门负责人在试运行启动会上明确要求，并在 [`TRIAL_FEEDBACK_TEMPLATE.md`](TRIAL_FEEDBACK_TEMPLATE.md) 中记录违规账号。

---

## 3. 老板 — 看 Dashboard

1. 使用 `boss` 登录 Web。
2. 进入 **看板** `/dashboard`（页眉显示「内部试运行」标识）。
3. 关注：待审数量、报价流水线、导出队列、实时通知、系统状态。
4. 不可在线修改系统配置（**系统设置** 仅提示联系管理员）。

---

## 4. 销售 — 新建报价

1. 使用 `sales01` 登录。
2. **报价中心** → **新建报价** `/quotes/new`，选择客户、机型、BOM。
3. 在 **报价中心** 打开报价单，编辑行、保存版本、提交审核。
4. 可查看 **客户管理**；无 BOM 维护、无审批权限。

---

## 5. 技术 — 维护 BOM

1. 使用 `tech01` 登录。
2. **机型管理** / **BOM 管理** 维护主数据。
3. 批量导入：`python scripts/import_initial_master_data.py --dir data/import_samples`。
4. 无报价审批、无财务导出权限。

---

## 6. 审批人 — Web / Mobile 审批

1. Web：`approver01` → 报价中心 → 待审单 → 通过/驳回。
2. Mobile：http://localhost:5174 登录同一账号 → 待审列表 → 审批。
3. 审批后三端通知与看板应自动刷新（需 Worker + 实时连接正常）。

---

## 7. 车间 — 查看看板

1. `workshop01` 登录 **车间终端**（:5175）或 Web **车间看板**。
2. 查看产线 KPI、报价队列；点击报价查看 BOM 树（只读）。
3. 无报价创建、无 BOM 编辑权限。

---

## 8. 导出报价 PDF

1. 使用 `sales01` 或 `finance01`（有 `business:quote:export`）。
2. 报价工作台 → 选择模板 → 生成 PDF。
3. **必须**运行 `event_worker`；完成后点击下载。
4. 财务侧重核对金额与导出文件，不负责改 BOM。

---

## 9. 查看通知

1. 顶栏铃铛角标 → **通知中心** `/notifications`。
2. 筛选未读、标记已读。
3. 无通知时页面提示：审批/导出操作后将在此显示。

---

## 10. 主数据导入

```bash
cd backend
# 预览
python scripts/import_initial_master_data.py --dir data/import_samples --dry-run
# 正式导入（不覆盖 DEMO-Q-001）
python scripts/import_initial_master_data.py --dir data/import_samples
```

样例文件：`backend/data/import_samples/*.csv`。支持单文件 CSV 或 Excel 多 Sheet。

---

## 11. 常见问题

| 现象 | 处理 |
|------|------|
| 登录 403 / 菜单缺失 | 确认 `setup_trial_users.py` 已执行；用 `verify_permissions.py` 检查 |
| 看不到 DEMO-Q-001 | 执行 `seed_demo_quote.py` |
| 导出一直 pending | 启动 `python -m workers.event_worker` |
| 通知不刷新 | 检查 WS/SSE；生产环境看 Nginx 配置 |
| 导入失败 | 使用 `--dry-run` 查看错误行；确认 `admin` 与 ROOT 部门存在 |
| metrics 403 | 生产需配置 `METRICS_API_KEY`，见 `ENTERPRISE_DEPLOYMENT.md` |

---

## 12. 问题反馈

使用 [`docs/TRIAL_FEEDBACK_TEMPLATE.md`](TRIAL_FEEDBACK_TEMPLATE.md) 提交问题。

交付验收清单：[`docs/DELIVERY_ACCEPTANCE.md`](DELIVERY_ACCEPTANCE.md)
