# UI Refactor Plan

> Scope: scan the `apps/web-admin` frontend only. No code was modified. This document is an execution plan based on the current implementation.

## 1. Inventory of component locations

### 1.1 Card components

| Location | Notes |
|---|---|
| `apps/web-admin/src/components/dashboard/dashboard-card.tsx` | Generic dashboard card base, currently uses hard-coded borders/colors |
| `apps/web-admin/src/components/dashboard/dashboard-kpi-card.tsx` | KPI card with repeated card shell patterns and hard-coded accents |
| `apps/web-admin/src/components/dashboard/QuickActionsCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/NotificationCenterCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/RecentFilesCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/RecentWorkOrdersCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/RecentProjectsCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/RecentQuotesCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/WorkflowProgressCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/SystemStatusCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/RiskCenterCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/ApprovalCenterCard.tsx` | Dashboard card variant |
| `apps/web-admin/src/components/dashboard/SalesOverviewPanel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/recent-quotes-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/risk-center-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/workshop-status-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/profit-overview-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/system-status-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/realtime-notifications-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/approval-status-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/quick-actions-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/quote-trend-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/dashboard/export-status-panel.tsx` | Panel/card hybrid |
| `apps/web-admin/src/components/projects/project-actual-costs-panel.tsx` | Domain panel/card |
| `apps/web-admin/src/components/master/master-list-page.tsx` | Wraps list pages in panel container |
| `apps/web-admin/src/components/table-shell.tsx` | Table-page container with card-like shell |
| `apps/web-admin/src/components/login/login-form-panel.tsx` | Login form card |
| `apps/web-admin/src/app/(admin)/*/page.tsx` | Several pages embed local card shells directly |

### 1.2 Table components

| Location | Notes |
|---|---|
| `apps/web-admin/src/components/master/master-list-page.tsx` | Uses `DataGrid` as the canonical list renderer |
| `apps/web-admin/src/components/table-shell.tsx` | Implements filter/search/export/pagination wrapper |
| `apps/web-admin/src/components/dashboard/*panel.tsx` | Several panels render table-like lists instead of using a shared table shell |
| `apps/web-admin/src/app/(admin)/quotes/page.tsx` | Quote list page (table-heavy) |
| `apps/web-admin/src/app/(admin)/quotes/customer/page.tsx` | Quote detail/edit page with table sections |
| `apps/web-admin/src/app/(admin)/projects/page.tsx` | Project list page |
| `apps/web-admin/src/app/(admin)/procurement/page.tsx` | Procurement list page |
| `apps/web-admin/src/app/(admin)/work-orders/page.tsx` | Work-order list page |
| `apps/web-admin/src/app/(admin)/customers/page.tsx` | Customer list page |
| `apps/web-admin/src/app/(admin)/suppliers/page.tsx` | Supplier list page |
| `apps/web-admin/src/app/(admin)/materials/page.tsx` | Materials list page |
| `apps/web-admin/src/app/(admin)/machines/page.tsx` | Machines list page |
| `apps/web-admin/src/app/(admin)/files/page.tsx` | Files list page |
| `apps/web-admin/src/app/(admin)/notifications/page.tsx` | Notification list page |
| `apps/web-admin/src/app/(admin)/standards/page.tsx` | Standards list page |
| `apps/web-admin/src/app/(admin)/boms/page.tsx` | BOM list/detail page |
| `apps/web-admin/src/app/(admin)/costing/page.tsx` | Costing list/detail page |
| `apps/web-admin/src/app/(admin)/fieldwork/page.tsx` | Fieldwork list page |
| `apps/web-admin/src/app/(admin)/workshop/page.tsx` | Workshop list/dashboard hybrid |

### 1.3 Form components

| Location | Notes |
|---|---|
| `apps/web-admin/src/components/login/login-form-panel.tsx` | Login form |
| `apps/web-admin/src/components/master/master-create-form.tsx` | Generic create form |
| `apps/web-admin/src/app/(admin)/quotes/new/page.tsx` | Quote creation form |
| `apps/web-admin/src/app/(admin)/quotes/customer/page.tsx` | Customer quote form |
| `apps/web-admin/src/app/(admin)/costing/page.tsx` | Costing form |
| `apps/web-admin/src/app/(admin)/business-settings/page.tsx` | Business settings form |
| `apps/web-admin/src/app/(admin)/settings/page.tsx` | Settings form |
| `apps/web-admin/src/app/(admin)/projects/page.tsx` | Project form sections |
| `apps/web-admin/src/app/(admin)/materials/page.tsx` | Material create/edit forms |
| `apps/web-admin/src/app/(admin)/suppliers/page.tsx` | Supplier create/edit forms |
| `apps/web-admin/src/app/(admin)/customers/page.tsx` | Customer create/edit forms |
| `apps/web-admin/src/app/(admin)/machines/page.tsx` | Machine create/edit forms |
| `apps/web-admin/src/app/(admin)/boms/page.tsx` | BOM create/edit forms |
| `apps/web-admin/src/app/(admin)/work-orders/page.tsx` | Work-order forms |
| `apps/web-admin/src/app/(admin)/fieldwork/page.tsx` | Fieldwork forms |

### 1.4 Status components

| Location | Notes |
|---|---|
| `apps/web-admin/src/components/notification-bell.tsx` | Notification count/status UI |
| `apps/web-admin/src/components/theme-toggle.tsx` | Theme state indicator |
| `apps/web-admin/src/components/dashboard/SystemStatusCard.tsx` | System health status |
| `apps/web-admin/src/components/dashboard/system-status-panel.tsx` | System health status |
| `apps/web-admin/src/components/dashboard/realtime-notifications-panel.tsx` | Notification state |
| `apps/web-admin/src/components/dashboard/approval-status-panel.tsx` | Approval status |
| `apps/web-admin/src/components/dashboard/risk-center-panel.tsx` | Risk status |
| `apps/web-admin/src/components/dashboard/workshop-status-panel.tsx` | Workshop equipment/status |
| `apps/web-admin/src/components/dashboard/export-status-panel.tsx` | Export job status |
| `apps/web-admin/src/app/(admin)/notifications/page.tsx` | Notification status list |
| `apps/web-admin/src/app/(admin)/workshop/page.tsx` | Workshop status badges |
| `apps/web-admin/src/app/(admin)/work-orders/page.tsx` | Work-order status labels |
| `apps/web-admin/src/app/(admin)/quotes/page.tsx` | Quote status labels |
| `apps/web-admin/src/app/(admin)/projects/page.tsx` | Project status labels |
| `apps/web-admin/src/app/(admin)/procurement/page.tsx` | Procurement status labels |
| `apps/web-admin/src/app/(admin)/boms/page.tsx` | BOM status labels |

### 1.5 PageHeader locations

| Location | Notes |
|---|---|
| `apps/web-admin/src/app/(admin)/dashboard/page.tsx` | Dashboard header area |
| `apps/web-admin/src/app/(admin)/quotes/page.tsx` | Page title + actions |
| `apps/web-admin/src/app/(admin)/quotes/new/page.tsx` | Form page header |
| `apps/web-admin/src/app/(admin)/quotes/customer/page.tsx` | Detail/edit page header |
| `apps/web-admin/src/app/(admin)/projects/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/materials/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/suppliers/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/customers/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/machines/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/procurement/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/costing/page.tsx` | Form/list header |
| `apps/web-admin/src/app/(admin)/business-settings/page.tsx` | Settings header |
| `apps/web-admin/src/app/(admin)/settings/page.tsx` | Settings header |
| `apps/web-admin/src/app/(admin)/work-orders/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/fieldwork/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/files/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/notifications/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/standards/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/boms/page.tsx` | List page header |
| `apps/web-admin/src/app/(admin)/workshop/page.tsx` | Control-room header |
| `apps/web-admin/src/app/(admin)/layout.tsx` | Shell-level page chrome |

### 1.6 Color hard-coding locations

The scan shows widespread direct use of hex colors, rgba values, gradient strings, and dark-mode overrides in these areas:

- `apps/web-admin/src/components/dashboard/dashboard-card.tsx`
- `apps/web-admin/src/components/dashboard/dashboard-kpi-card.tsx`
- `apps/web-admin/src/components/app-shell.tsx`
- `apps/web-admin/src/components/login/login-form-panel.tsx`
- `apps/web-admin/src/components/table-shell.tsx`
- `apps/web-admin/src/components/dashboard/*.tsx`
- `apps/web-admin/src/app/(admin)/*.tsx`
- `apps/web-admin/src/app/globals.css`
- `apps/web-admin/src/app/layout.tsx`

Because the question requires a location list, the most important confirmed hotspots are the files above. These files contain the bulk of the hard-coded color system.

### 1.7 Token definition locations

| Location | Notes |
|---|---|
| `apps/web-admin/src/app/globals.css` | CSS custom properties and theme overrides |
| `packages/ui/src/theme/design-tokens.ts` | Shared design tokens source |
| `packages/ui/src/theme/interaction-tokens.ts` | Interaction spacing / motion tokens |
| `packages/ui/src/theme/design-tokens.ts` | Color, spacing, radius, typography tokens |
| `packages/ui/src/theme/interaction-tokens.ts` | Layout/gap/focus tokens |
| `packages/ui/src/components/industrial/industrial-panel.tsx` | Uses shared tokens for panel shell |
| `packages/ui/src/components/kpi/kpi-card.tsx` | Uses shared tokens for KPI presentation |
| `packages/ui/src/components/layout/industrial-page.tsx` | Uses shared spacing tokens |

---

## 2. Unified plan

### 2.1 Target architecture

建立 6 个基础组件作为前端统一外壳：

1. `IndustrialCard`
2. `TableShell`
3. `FormSection`
4. `StatusBadge`
5. `PageHeader`
6. `AppShell`

### 2.2 Standardization rules

- 所有页面卡片只能通过 `IndustrialCard` 或其领域变体实现。
- 所有列表页必须走 `TableShell`，禁止在页面内重复写搜索、筛选、导出、分页布局。
- 所有表单页必须拆成 `FormSection`，统一标题、说明、字段间距、校验提示、操作区。
- 所有状态显示必须通过 `StatusBadge`，禁止在页面内直接写颜色和圆点。
- 所有页面标题统一走 `PageHeader`，包含标题、描述、统计、主操作、次操作。
- 所有路由壳层统一走 `AppShell`，包含侧栏、顶栏、全局搜索、用户菜单、通知、主题切换。

### 2.3 Token policy

- 禁止页面直接写 hex / rgba / gradient 颜色。
- 颜色、圆角、阴影、间距、字号、动画时长全部从 token 读取。
- 深色模式只允许在 token 层实现，不允许在页面组件中再写第二套散落的色值。
- Dashboard / 登录页允许保留少量视觉装饰，但装饰颜色也必须来自 token。

---

## 3. Refactor roadmap for the six base components

### Phase 1 — `AppShell`

**Priority:** P0

**Why first:** 所有页面都依赖壳层；先统一壳层可以立刻减少全站视觉漂移。

**Expected files to touch:** 1~3

**Estimated effort:** 1.5~2.5 days

**Risk:** High

**Deliverables:**
- 拆分 header / sidebar / footer / right panel
- 统一顶部搜索、通知、主题切换、用户菜单
- 统一侧栏 active / collapsed / permission gating

### Phase 2 — `PageHeader`

**Priority:** P0

**Why:** 页面标题、筛选区、动作区高度重复，统一后可立刻减少各业务页样式分叉。

**Expected files to touch:** 15~25

**Estimated effort:** 1.5~2 days

**Risk:** Medium

**Deliverables:**
- 标题、描述、统计、主按钮、次按钮标准化
- Dashboard / 列表页 / 详情页统一标题结构

### Phase 3 — `IndustrialCard`

**Priority:** P0

**Why:** Dashboard 和多个业务页都存在重复卡片壳。

**Expected files to touch:** 12~18

**Estimated effort:** 2~3 days

**Risk:** Medium

**Deliverables:**
- 标准卡片容器
- 标题栏 / 工具栏 / 内容区 / 状态区
- 支持 fill、hover、soft border、panel variants

### Phase 4 — `TableShell`

**Priority:** P0

**Why:** 列表页最多，收益最大。

**Expected files to touch:** 18~30

**Estimated effort:** 3~4 days

**Risk:** High

**Deliverables:**
- 搜索、筛选、导出、刷新、分页统一
- 支持空状态、错误状态、加载态
- 与 `DataGrid` / 列表页 API 对齐

### Phase 5 — `FormSection`

**Priority:** P1

**Why:** 表单页数量较多，但比列表页更容易局部迁移。

**Expected files to touch:** 10~20

**Estimated effort:** 2~3 days

**Risk:** Medium

**Deliverables:**
- 统一表单段落标题、说明、字段栅格、操作栏
- 支持基础字段布局和高级字段布局

### Phase 6 — `StatusBadge`

**Priority:** P1

**Why:** 状态散点和颜色硬编码大量存在，统一后能显著降低视觉混乱。

**Expected files to touch:** 20~35

**Estimated effort:** 1.5~2.5 days

**Risk:** Low

**Deliverables:**
- 成功、警告、失败、进行中、草稿、关闭、离线、待审批等状态统一
- 支持点状、胶囊、标签三种外观

---

## 4. Implementation priority

### Highest priority

1. `AppShell`
2. `TableShell`
3. `PageHeader`
4. `IndustrialCard`

### Medium priority

5. `FormSection`
6. `StatusBadge`

### Supporting work

- 统一 tokens
- 清理 hard-coded color
- 重构 dashboard panels
- 合并重复 API hooks
- 清理登录页与空状态样式

---

## 5. Estimated effort summary

| Item | Priority | Estimated file count | Estimated effort | Risk |
|---|---:|---:|---:|---|
| AppShell | P0 | 1~3 | 1.5~2.5 days | High |
| PageHeader | P0 | 15~25 | 1.5~2 days | Medium |
| IndustrialCard | P0 | 12~18 | 2~3 days | Medium |
| TableShell | P0 | 18~30 | 3~4 days | High |
| FormSection | P1 | 10~20 | 2~3 days | Medium |
| StatusBadge | P1 | 20~35 | 1.5~2.5 days | Low |

---

## 6. Risk notes

- `AppShell` 和 `TableShell` 是高风险改造点，因为它们触达面最广。
- `Dashboard` 变体较多，若不先统一 `IndustrialCard`，会继续产生新样式分叉。
- `StatusBadge` 虽然实现简单，但在业务页和列表页会被大量使用，必须先定义 token 套路。
- `FormSection` 的风险主要来自字段布局差异，建议先做最小可用统一层。

---

## 7. Recommended execution sequence

1. 先定 token 和视觉规则，冻结颜色硬编码新增。
2. 重构 `AppShell`。
3. 重构 `PageHeader`。
4. 引入 `IndustrialCard`。
5. 切换 `Dashboard` 和若干核心列表页到新基座。
6. 引入 `TableShell`。
7. 引入 `FormSection`。
8. 引入 `StatusBadge`。
9. 批量迁移业务页面。
10. 最后清理残留的 hard-coded color 和重复样式。

---

## 8. Notes on evidence

This plan is based on the currently implemented frontend files under `apps/web-admin/src`, including:
- `apps/web-admin/src/components/dashboard/dashboard-card.tsx`
- `apps/web-admin/src/components/dashboard/dashboard-kpi-card.tsx`
- `apps/web-admin/src/components/master/master-list-page.tsx`
- `apps/web-admin/src/components/table-shell.tsx`
- `apps/web-admin/src/components/app-shell.tsx`
- `apps/web-admin/src/components/login/login-form-panel.tsx`
- `apps/web-admin/src/app/globals.css`
- the route pages under `apps/web-admin/src/app/(admin)/*`

The plan intentionally avoids changing code and is intended for execution planning only.
