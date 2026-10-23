# 功能验收矩阵

> **说明**：本矩阵区分证据类型，避免把「有代码」写成「已验收」。  
> 图例：✅ 运行验证 · 📄 代码/静态测试 · ☐ 未验证 · ⚠️ 部分/存疑

最后更新：2026-10-23（K-005 新建强制 product_id；NON-UI：MinIO lifecycle / lint / 幂等；种子 43896d6；UI_PHASE_GATE 仍 ON）

---

## 总览

| 模块 | 页面/入口 | API | 持久化模型 | 静态对齐测试 | 运行验收 |
|---|---|---|---|---|---|
| 登录/会话 | `/login` | `/auth/*` | User | 📄 `test_token_types` 等 | ✅ 6 试用账号 `smoke_trial_login`；K-020 防 GET 泄密已修 |
| 运营看板 | `/dashboard` | `/dashboard/*` | 多表聚合 | 📄 `test_dashboard_*` + UX 静态（门禁 + 种子角色矩阵） | ✅ 四角色 headless 卡显隐 PASS（`run-dashboard-role-cards.mjs`）；⚠️「按角色换整套布局」仍 ☐（K-006） |
| 报价中心 | `/quotes`, `/quotes/customer` | `/quotes/*` | Quote… | 📄 PageHeader；K-005 新建强制 product_id；对客金额 `align:right`；UX-002 侧栏 hidden + 页内深链；合并 Tab ☐（两套模型，非小补丁） | ✅ 场景 A API；视口页头可见；列表 loading 未断言金额（K-028） |
| 项目 | `/projects`… | `/projects/*` | Project… | 📄 | ✅ 场景 B API；浏览器「项目台账」可开 |
| 产品库 | `/products` | `/products/*` | Product | 📄 | ✅ sales 列表 200 |
| 机型/BOM | `/machines`, `/boms` | ✅ | Machine… | 📄 UX-001 侧栏 `hidden`；**K-005 已强制**新建报价 `product_id`（machine-only → 400） | ✅ URL/权限保留；历史机型报价可读；新建 machine-only 已禁 |
| 主数据 | customers 等 | … | … | 📄 | ✅ customers 列表 200 |
| 采购 | `/procurement` | … | … | 📄 PageHeader + 主操作 + DataGrid 金额/数量 `align:right`；空材料/供应商引导链；`check-ui-batch` OK | ✅ 场景 C API；视口金额 `right=9/9`（试用 TRIAL-PR-*）；K-030 修列表 500 |
| 财务 | `/accounting*` | `/accounting/*` | … | 📄 三页 FilterBar + `moneyCellClass`；未开记账提示指向 trialadmin；`check-ui-batch`+`tsc` OK | ✅ 场景 C/D API；视口金额 `right=3/3`（试用种子开记账 + draft 样例） |
| 审批 | `/approvals` | `/approvals/*` | … | 📄 金额/优惠列 `align:right`；文案强调本页处理勿重复录入；`check-ui-batch` | ✅ 视口金额 `right=4/4`（TRIAL-PR-0002 待办样本）；随后 boss `/approvals/action` **approve** PASS（本地 55432）；见 `logs/approvals-money-align-*.txt` + `logs/approvals-trial-approve-*.json` |
| 权限 | 菜单+按钮 | `require_permissions` | Role… | ✅ | ✅ `verify_permissions` + 角色冒烟 |
| 车间 | `/workshop` + workshop-terminal | `/workshop` | … | 📄 | ✅ API board + UI 登录看板→DEMO BOM/KPI（§3.8） |
| 移动审批 | mobile-app | 同 API | — | 📄 | ✅ UI 登录→待审→通过（§3.7）；修 K-025 后 |

---

## 核心闭环（任务书场景 A–F）

| 场景 | 步骤摘要 | 预期 | 结果 | 证据 |
|---|---|---|---|---|
| A 产品→报价 | 维护产品 → 报价选品 → 保存 → 重开核对金额 | 前后端金额一致、行快照保留；**合计服务端权威**（`strip_client_quote_totals` + 版本行 sum；Create DTO 无 client total） | ✅ API | `POST /quotes/wizard` → `Q20261023-0001` total **1600.0000**；`GET` 重读一致；`product_id` 保留；回归 `test_quote_track_and_totals` |
| B 报价↔项目 | 建项目带 `primary_quote_id` → 客户自动一致；冲突 400；summary 关联报价 | 客户与报价一致 | ✅ API | `PRJ-20261023-001` 关联 `Q20261023-0001`；summary 返回 linked_quote |
| C 采购→应付→付款 | 采购 → 下单 → 应付申请 → boss 审批 → 部分付款 | 余额一致、防重复申请 | ✅ API | `PR-20261023-*` → pending→approved → `PY-20261023-001`；重复申请 400 |
| D 应收→收款→核销 | 应收 → 部分收款 → 超额拒绝 → 结清 | 余额准、超额 400 | ✅ API | `AR-20261023-003` → RC-001/002；settled=1000 open=0；超额 400 |
| E 异常/重复 | 重复提交、越权 | 4xx | ✅ 部分 | finance→configs **403**；超额核销/重复应付 **400** |
| F 角色权限 | 多角色登录 | 菜单+API 双端一致 | ✅ API | 6 账号登录 PASS；权限门禁 All checks passed |

---

## 自动化可复现命令

```powershell
cd D:\cursorxiangmu\shengtaixitong\backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\verify_permissions.py
# 需 TRIAL_*_PASSWORD：
.\.venv\Scripts\python.exe scripts\smoke_trial_login.py

# UI 布局静态冒烟（报价/采购/财务 + DataGrid align）
cd D:\cursorxiangmu\shengtaixitong
node logs/check-ui-batch.mjs
cd apps/web-admin; npx tsc --noEmit -p tsconfig.json

# 视口冒烟（需本机 web:3000 + api:8000；口令见 trial-passwords.local.env）
# 先确保 Chromium：npx playwright@1.51.1 install chromium
# 试用金额环境（指向与 API 同一库；本机常为 55432，见 README / .env.example）：
#   $env:DATABASE_URL="postgresql+psycopg://erp:erp@127.0.0.1:55432/erp_db"
#   python -u backend/scripts/seed_trial_money_viewport.py
# 可选（默认关）：再种一条采购应付 pending，供审批金额视口（仍仅本地库）：
#   python -u backend/scripts/seed_trial_money_viewport.py --with-pending-approval
node scripts/ui/run-viewport-core-lists.mjs
# 结果：logs/viewport-core-lists-out.txt（含 /approvals）

# UX-006 多角色 Dashboard 卡门禁（trialadmin/finance01/sales01/workshop01）
node scripts/ui/run-dashboard-role-cards.mjs
# 结果：logs/dashboard-role-cards-out.txt

# UX-001/002/006 静态钉：
cd backend; .\.venv\Scripts\python.exe -m pytest -q tests/test_ux_menu_and_dashboard_static.py
```

口令勿入库；本地可用 `logs/trial-passwords.local.env`（已 gitignore）。

### 本批 UI 缺口（诚实）

- DataGrid **列级 `align` 已落地**；采购/对客报价/审批金额列已 `align:"right"`（K-028/K-030）。
- 视口列表：`run-viewport-core-lists.mjs` → `RESULT=PASS`（报价/采购/财务金额右齐；审批壳层 OK）。
- UX-006 / K-006：**四角色 Dashboard 卡显隐** headless `RESULT=PASS`（API 权限与 DOM 一致；证据 `logs/dashboard-role-cards-out.txt` + `viewport-dashboard-*.png`）。「整套按角色换布局」仍 ☐。
- UX-002：侧栏 hidden + 报价中心页内深链 ✅；**合并 Tab 暂缓 / UI_PHASE_GATE**（两套模型，非小补丁）。
- UX-004：**已验收** — 前端选报价锁定客户；服务端 create/update 冲突 **400**；场景 B API 已覆盖。
- 审批金额视口：✅ PASS（`money=right=4/4`）；样本 `TRIAL-PR-0002` 应付申请 → boss 批准（本地 55432 only）；证据 `logs/approvals-money-align-note.txt`、`logs/approvals-trial-approve-note.txt`。
- 试用记账种子：`43896d6` 锁定本地库强制开记账 + 非本地拒绝；可选 `--with-pending-approval`（**默认关**）种 pending 应付供视口，不削弱财务策略。
- K-030 / K-029 既有修复仍保留；E2E 仍用 `playwright-core`（无 `@playwright/test`）。
- **GATED（勿开）：** ERP 前端 UI 重构 / UX-002 Tab 合并 / K-006「按角色换整套布局」。
- **NON-UI（本批）：** MinIO lifecycle no-op（AbortIncomplete 不支持）；报价服务端合计权威 + 产品轨 helpers；财务幂等/防重单测；ruff/mypy 非阻塞基线；脚本 DB 55432 脚枪探测。
