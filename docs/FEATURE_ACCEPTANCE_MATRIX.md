# 功能验收矩阵

> **说明**：本矩阵区分证据类型，避免把「有代码」写成「已验收」。  
> 图例：✅ 运行验证 · 📄 代码/静态测试 · ☐ 未验证 · ⚠️ 部分/存疑

最后更新：2026-10-23（K-028 DataGrid `align` + 采购/对客报价金额右齐；视口 `run-viewport-core-lists` PASS；`check-ui-batch` + `tsc` ✅）

---

## 总览

| 模块 | 页面/入口 | API | 持久化模型 | 静态对齐测试 | 运行验收 |
|---|---|---|---|---|---|
| 登录/会话 | `/login` | `/auth/*` | User | 📄 `test_token_types` 等 | ✅ 6 试用账号 `smoke_trial_login`；K-020 防 GET 泄密已修 |
| 运营看板 | `/dashboard` | `/dashboard/*` | 多表聚合 | 📄 `test_dashboard_*` | ✅ 浏览器可开（销售会话） |
| 报价中心 | `/quotes`, `/quotes/customer` | `/quotes/*` | Quote… | 📄 PageHeader；对客列表金额 `align:right` + 明细 `moneyCellClass`；去重页头主操作；`check-ui-batch`+`tsc` OK | ✅ 场景 A API；视口页头可见；列表 loading 未断言金额（K-028） |
| 项目 | `/projects`… | `/projects/*` | Project… | 📄 | ✅ 场景 B API；浏览器「项目台账」可开 |
| 产品库 | `/products` | `/products/*` | Product | 📄 | ✅ sales 列表 200 |
| 机型/BOM | `/machines`, `/boms` | … | Machine… | 📄 | ☐（侧栏隐藏） |
| 主数据 | customers 等 | … | … | 📄 | ✅ customers 列表 200 |
| 采购 | `/procurement` | … | … | 📄 PageHeader + 主操作 + DataGrid 金额/数量 `align:right`；`check-ui-batch` OK | ✅ 场景 C API；视口页头/主操作可见；库空无金额单元格 |
| 财务 | `/accounting*` | `/accounting/*` | … | 📄 三页 FilterBar + `moneyCellClass`；`check-ui-batch`+`tsc` OK | ✅ 场景 C/D API；视口金额表头右齐 ✅（`viewport-core-lists-out.txt`） |
| 审批 | `/approvals` | `/approvals/*` | … | 📄 | ✅ 浏览器「审批中心」可开（sales 待办 0，预期） |
| 权限 | 菜单+按钮 | `require_permissions` | Role… | ✅ | ✅ `verify_permissions` + 角色冒烟 |
| 车间 | `/workshop` + workshop-terminal | `/workshop` | … | 📄 | ✅ API board + UI 登录看板→DEMO BOM/KPI（§3.8） |
| 移动审批 | mobile-app | 同 API | — | 📄 | ✅ UI 登录→待审→通过（§3.7）；修 K-025 后 |

---

## 核心闭环（任务书场景 A–F）

| 场景 | 步骤摘要 | 预期 | 结果 | 证据 |
|---|---|---|---|---|
| A 产品→报价 | 维护产品 → 报价选品 → 保存 → 重开核对金额 | 前后端金额一致、行快照保留 | ✅ API | `POST /quotes/wizard` → `Q20261023-0001` total **1600.0000**；`GET` 重读一致；`product_id` 保留 |
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
node logs/run-viewport-core-lists.mjs
# 结果：logs/viewport-core-lists-out.txt
```

口令勿入库；本地可用 `logs/trial-passwords.local.env`（已 gitignore）。

### 本批 UI 缺口（诚实）

- DataGrid **列级 `align` 已落地**；采购/对客报价金额列已 `align:"right"`（K-028 代码侧关闭）。
- 视口已跑：`logs/run-viewport-core-lists.mjs` → `RESULT=PASS`（财务金额表头右齐；报价列表 headless 长期「加载报价列表…」；采购无数据无金额单元格）。
- UI 表单自动登录未发出 XHR（K-029）；视口用 API+localStorage 注入绕过。
- 作废账目 / 付款核销等**不可逆财务操作**未在本批改口径，仍按既有 confirm 对话框。
