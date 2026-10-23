# 项目本体交付摘要（2026-10-23）

> BODY-CLOSE 批次。Git HEAD：`4230de8`（干净工作区起点；本批文档/种子可选旗标/冒烟日志可为后续 commit）。  
> **交付签字**：`DELIVERY_ACCEPTANCE.md` §6 已签字（内部试运行）。  
> **UI_PHASE_GATE：开启** — 禁止启动 ERP 前端 UI 重构指令、UX-002 Tab 合并、K-006「按角色换整套布局」。

---

## 1. 已完成模块

| 域 | 状态 | 要点 |
|---|---|---|
| 登录/会话 / RBAC | ✅ | 6 试用账号；`verify_permissions`；K-020 防 GET 泄密 |
| 报价 / 产品 / 项目 | ✅ | 场景 A/B；UX-001 侧栏机型 hidden；UX-004 客户锁定+服务端 400 |
| 采购 → 应付 → 付款 | ✅ | 场景 C；K-030 列表 schema；视口金额右齐 |
| 应收 → 收款 → 核销 | ✅ | 场景 D；行锁 / noload（K-015/K-017） |
| 审批中心 | ✅ | 金额列右齐；TRIAL 样本视口 PASS；boss 批准 TRIAL-PR-0002 |
| 财务三页 | ✅ | UX-003 子导航；试用种子开记账（本地锁定） |
| Dashboard 卡门禁 | ✅ 门禁 | UX-006 / K-006 四角色 headless PASS；整套布局仍 ☐ |
| Mobile / Workshop | ✅ | §3.7 / §3.8；K-025 http-client |
| 本地 + prod Compose | ✅ | Nginx/API/WS/SSE/Worker/MinIO；安全 §4.x |
| 试用种子策略 | ✅ | `43896d6` 本地强制开记账；非本地默认拒绝 |

---

## 2. 场景 A–F

| 场景 | 结果 | 证据索引 |
|---|---|---|
| A 产品→报价 | ✅ API | `FEATURE_ACCEPTANCE_MATRIX`；`Q20261023-0001` total 1600 |
| B 报价↔项目 | ✅ API | `PRJ-20261023-001`；UX-004 客户一致 |
| C 采购→应付→付款 | ✅ API | `PR-20261023-*`；TRIAL 视口 + 批准样本 |
| D 应收→收款→核销 | ✅ API | `AR-20261023-003`；超额 400 |
| E 异常/重复 | ✅ 部分 | 越权 403；超额/重复 400 |
| F 角色权限 | ✅ | `smoke_trial_login` + `verify_permissions` |

签字与运维入口见 `docs/FINAL_DELIVERY_REPORT.md`。

---

## 3. 证据路径（本机 `logs/`，勿把口令入库）

| 主题 | 路径 |
|---|---|
| 审批金额视口 PASS | `logs/approvals-money-align-note.txt`、`approvals-money-align-out.txt`、`viewport-approvals.png` |
| TRIAL 待办创建 / 批准 | `logs/approvals-trial-pending-*.json`、`approvals-trial-approve-*.json`、`approvals-trial-approve-note.txt` |
| 核心列表视口 | `logs/viewport-core-lists-out.txt`（RESULT=PASS） |
| Dashboard 四角色卡门禁 | `logs/dashboard-role-cards-out.txt` |
| 记账种子 / UI 静态 | `logs/seed-trial-money-viewport.txt`、`check-ui-batch-*.txt` |
| BODY-CLOSE 冒烟 | `logs/body-close-smoke-*.txt`（本批写入） |
| 集成测试 | `logs/integration-pytest.txt`（44 passed / 3 xfailed） |

---

## 4. 明确 gated（勿做）

1. **UI_PHASE / ERP 前端 UI 重构指令**（步骤 1–7 大改）  
2. **UX-002** 内部报价 ↔ 对客报价 **合并 Tab**（两套模型）  
3. **K-006** Dashboard **按角色换整套布局**（卡门禁已够用）  
4. 削弱财务不可逆规则或种子本地策略（`43896d6`）  
5. 对生产库盲跑种子 / `--allow-non-local` 无明确意图时勿用  

---

## 5. 风险与脚枪

| 风险 | 说明 | 缓解 |
|---|---|---|
| **55432 vs 5432** | `backend/.env` 常写 5432；试用 API/视口证据多在集成栈 **55432** | 种子/脚本显式 `$env:DATABASE_URL=...55432...`；README 已写 |
| **无 git remote**（K-014） | 无法 `git push` 远端备份 | 本机 commit + 外置备份；不假装已推送 |
| 财务并发/核销 | 历史 P0/P1 已修（K-015/K-017） | 勿回退 `for_update`/`noload` |
| 试用口令 | `logs/trial-passwords.local.env`（gitignore） | 勿提交；生产须轮换 |

---

## 6. 可选工具（本批）

```powershell
# 默认：仅材料/请购/draft 账 + 开记账（本地）
$env:DATABASE_URL="postgresql+psycopg://erp:erp@127.0.0.1:55432/erp_db"
python -u backend/scripts/seed_trial_money_viewport.py

# 可选：再种一条 pending 采购应付（默认关；仍受本地库守卫）
python -u backend/scripts/seed_trial_money_viewport.py --with-pending-approval
```

---

## 7. 建议后续（非本批）

- 文档/种子旗标/冒烟日志若值得入库：见 agent handoff 建议 commit message；**不要 push**（无 remote）。  
- UI 偏好与大改：等负责人解除 `UI_PHASE_GATE` 后再开新批次。
