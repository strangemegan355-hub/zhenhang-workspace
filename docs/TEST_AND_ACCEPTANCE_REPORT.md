# 测试与验收报告

> 批次：第五批（2026-10-23）— integration_tests + verify_delivery + 浏览器页/API 闭环续跑。  
> 原则：**禁止伪造验收**；未跑通的场景标记 ☐。

---

## 1. 已执行

| 命令 / 检查 | 环境 | 结果 |
|---|---|---|
| `pytest -q`（unit） | backend venv | ✅ **265 passed**（前期） |
| `pytest integration_tests` | compose `55432/56379/59000` + 种子账号 | ✅ **44 passed, 3 xfailed**（约 334s；`logs/integration-pytest.txt`） |
| `scripts/verify_delivery.ps1 -BaseUrl http://127.0.0.1:8000` | 本机 API+Web | ✅ **4 passed, 0 failed, 1 skipped**（metrics：EnvFile=prod 但本机 API 非 prod → SKIP） |
| `GET` live/ready | 127.0.0.1:8000 | ✅ 200 |
| `GET /` web | 127.0.0.1:3000 | ✅ 200 |
| `npm run lint:web` / `build:web` / workshop / mobile | 前期 | ✅ |
| 场景 A（API） | sales01 wizard | ✅ `Q20261023-0002` total **1600.0000**（本批新建） |
| 场景 B（API） | 项目关联主报价 + summary | ✅ project `52d758a7-…` linked `Q20261023-0002` |
| 浏览器页冒烟 | dashboard/quotes/projects/accounting/approvals | ✅ 壳层可开；报价「新建」表单可开 |
| 浏览器完整点击闭环（下拉选客/品并保存） | IDE Browser | ⚠️ 列表曾卡在 loading（K-021 已修）；自动化下 axios 列表仍偶发不刷新，改以 API 证据为准 |
| `integration_tests` 首次未种子 | — | ❌ 13 failed（口令/种子）；补 `bootstrap`+`--reset-passwords` 后全绿 |

---

## 2. 本批修复

| 项 | 说明 |
|---|---|
| K-020 | 登录 `method=post` + `preventDefault` |
| K-021 | 报价列表 loading 不再等待 `machinesQuery` |
| verify_delivery | EnvFile=prod 但 BaseUrl 返回 metrics 200 → **SKIP** 而非误 FAIL |
| http-client / providers | API 默认 `127.0.0.1:8000`；providers 启动时强制 `apiClient.defaults.baseURL` |
| integration 种子 | 对 55432 库执行 bootstrap / seed_tenant / seed_workflows / `setup_trial_users --reset-passwords` |

---

## 3. 任务书场景 A–F

见 `FEATURE_ACCEPTANCE_MATRIX.md`。API 层 A–F 已实证；浏览器为页可达 + 新建表单，完整点击仍待人工。

---

## 4. 第六批补充（同日）

| 项 | 结果 |
|---|---|
| UX-007 | ✅ `MasterCreateForm` + 项目/采购/工单/现场/安装/验收/设备/实际成本改 `type="date"` |
| K-022 | ✅ providers 模块顶层注册 `baseURL`/token（避免首屏相对请求挂起） |
| IDE Browser 建单点击 | ☐ 自动化环境下列表仍常停在 loading；请本机浏览器硬刷新 `/quotes` 验证 |

## 5. 下一步

1. **人工**：硬刷新 `http://127.0.0.1:3000/quotes`，确认左侧列表与客户/产品下拉有数据并新建一单。  
2. 对真实 prod BaseUrl 再跑 `verify_delivery`（期望 metrics 403）。  
3. 备份恢复演练。
