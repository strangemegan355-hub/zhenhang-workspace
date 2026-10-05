# 工业报价系统 — 演示指南

## 环境

- 后端: `http://localhost:8000`
- Web: `npm run dev:web`
- 移动审批: `npm run dev:mobile` (5174)
- 车间看板: `npm run dev:workshop` (5175)
- 账号: `admin`（口令由 `BOOTSTRAP_ADMIN_PASSWORD` 提供，无默认值）

## 演示数据

在 `backend` 目录执行（需先完成 `bootstrap_admin` 与数据库迁移）：

```bash
python scripts/seed_demo_quote.py
```

将生成演示报价单 **DEMO-Q-001**（含 24 行 BOM 物料）。PDF/Excel 导出需另开终端运行 `python -m workers.event_worker`。

## 正式演示顺序（12 步）

适合内部交付演示与客户试运行，约 15–20 分钟。

| 步骤 | 端 | 操作 |
|------|-----|------|
| 1 | Web | 登录 `admin` → 进入看板 |
| 2 | Web | `/dashboard` 查看 KPI、审批状态、实时通知 |
| 3 | Web | 打开 **报价中心** `/quotes` |
| 4 | Web | 选择 **DEMO-Q-001** 进入工业工作台 |
| 5 | Web | 修改一条报价行（数量/单价） |
| 6 | Web | 工具栏 **保存版本** |
| 7 | Web | **版本对比** V1→V2，查看 BOM/成本差异 |
| 8 | Web | **提交审核** → **审批通过**（或 Mobile 审批） |
| 9 | Web | 选择导出模板 → **生成 PDF** → **下载**（需 Worker） |
| 10 | Web | 查看顶栏通知与 `/notifications` |
| 11 | Mobile | http://localhost:5174 待审列表 → 通过/驳回 |
| 12 | Workshop | http://localhost:5175 看板刷新 → 点击报价查看 **BOM 树** |

**前置：** 完成 seed（`seed_demo_quote.py`）、API + Worker 已启动；生产环境经 Nginx 访问 http://localhost。

## 5 分钟演示脚本

1. **登录** → 报价中心 `/quotes`
2. **选择报价** → 进入工业工作台（开发环境显示演示步骤条）
3. **BOM** → 展开模块树、搜索物料、拖拽排序顶级模块、点击「导入报价」
4. **报价行** → 编辑数量/单价，查看行内公式与毛利列；拖拽排序行；`Ctrl+Z` / `Ctrl+Y` 撤销重做
5. **成本** → 观察成本结构条与 KPI 实时变化
6. **保存版本** → 工具栏「保存版本」
7. **版本对比** → 调整 V1→V2 对比
8. **审批** → 快捷意见 + `Ctrl+Enter` 通过（或手机端审批）
9. **导出** → 选择模板查看区块预览 → 生成 → 下载
10. **AI** → 查看风险等级与审批建议，点击「重新分析」

## P2 端到端验证（报价闭环 + 通知 + 实时 + Worker）

### 启动顺序

```powershell
docker compose up -d postgres redis minio
cd backend
python scripts/run_local_api.py
# 另开终端 — 导出任务消费（必需）
python -m workers.event_worker
# 另开终端 — Web 管理端
npm run dev -w web-admin
```

可选 API 自动化脚本（需 API 已启动，演示数据已 seed）：

```bash
cd backend
python scripts/verify_p2_flow.py
```

### 验证清单

| 环节 | 操作 | 预期 |
|------|------|------|
| 报价闭环 | `/quotes` 选 DEMO-Q-001 → 保存版本 → 版本对比 → 提交/审批 → 导出 PDF | 无 500；状态流转正确 |
| 导出下载 | 导出完成后点击「下载」 | 打开 MinIO 签名 URL，非 JSON 预览页 |
| 通知 | 顶栏「通知」角标、看板实时通知面板、`/notifications` | 审批/导出后未读数增加；标记已读后减少 |
| 实时刷新 | 保持页面打开，执行审批或导出 | Toast + 列表/看板自动刷新；断网恢复后数据同步 |
| Worker | `event_worker` 日志 | 导出任务 `pending → completed`；`quote_export_tasks` 有记录 |

### WebSocket / SSE

管理端通过 `IndustrialRealtimeProvider` 连接 `/api/v1/realtime/ws`（或 SSE 回退）。断线后会自动重连并刷新看板、报价、通知缓存。

## P3 三端联动（Mobile + Workshop + Web）

### 启动

```powershell
# 基础设施 + API + Worker（同 P2）
docker compose up -d postgres redis minio
cd backend
python scripts/run_local_api.py
python -m workers.event_worker   # 另开终端

# 三端前端（各开终端）
npm run dev:web        # http://localhost:3000
npm run dev:mobile     # http://localhost:5174
npm run dev:workshop   # http://localhost:5175
```

构建：`npm run build:mobile` · `npm run build:workshop`

### 三端演示路径

| 端 | 地址 | 能力 |
|----|------|------|
| Web 管理端 | :3000 | 报价工作台、导出、看板、通知中心 |
| 移动审批 | :5174 | 待审列表 · 通过/驳回 · 离线队列 · 通知已读 |
| 车间终端 | :5175 | 报价队列 · BOM 只读树 · 产线/设备/报警 · 实时看板 |

### 联动验证

1. Web `/quotes` 将 DEMO-Q-001 **提交审核**（状态 → reviewing）
2. **Mobile** 待审列表出现该单 → 审批通过
3. **Workshop** 报价队列与 KPI 自动刷新；点击报价行查看 **BOM 模块树**
4. Web 执行 **导出 PDF**（需 Worker）→ Mobile/Workshop/Web 通知与看板同步更新

CORS 需包含 `5174` / `5175`（见 `backend/.env.example` 中 `CORS_ORIGINS`）。

## 能力清单

| 能力 | 操作 |
|------|------|
| BOM 虚拟滚动 | 大量物料流畅滚动 |
| BOM 分组 | 按物料编码前缀自动模块树 |
| 拖拽 | BOM 顶级模块、报价行 |
| 行内公式 | 数量×单价、毛利额/率 |
| 撤销重做 | 工具栏或 Ctrl+Z / Ctrl+Y |
| 快速审批 | Ctrl+Enter 通过，快捷意见 chip |
| 导出区块 | 模板卡片 + A4 区块预览 |
| AI 分析 | 摘要、发现、风险、建议 |
