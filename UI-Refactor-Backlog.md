# UI Refactor Backlog

> 说明：本 Backlog 拆分为可独立提交 Git Commit 的最小任务单元，适合 Cursor 逐项执行。

## 推荐执行顺序
1. `P0`：先统一 `AppShell` / `PageHeader` / `IndustrialPage`
2. `P0`：再统一 `TableShell` / `FilterBar` / `ActionToolbar`
3. `P0`：再统一 `FormSection` / `StatusBadge`
4. `P1`：再统一 `IndustrialCard` / `NotificationPanel` / `SideSummaryPanel`
5. `P1`：重构 Dashboard 与登录页
6. `P2`：收口特殊页面与细节优化

---

## 任务清单

| 任务编号 | 任务名称 | 影响文件 | 预计工时 | 优先级 | 风险等级 | 前置依赖 | 验收标准 |
|---|---|---|---:|---|---|---|---|
| UI-T001 | 拆分并统一 AppShell 顶部栏/侧边栏/底栏 | `apps/web-admin/src/components/app-shell.tsx`, `apps/web-admin/src/components/notification-bell.tsx`, `apps/web-admin/src/components/theme-toggle.tsx` | 6h | P0 | Critical | 无 | Shell 逻辑分层清晰，页面导航行为不变，构建通过 |
| UI-T002 | 引入统一 PageHeader 组件 | `apps/web-admin/src/components/**/page.tsx`, `packages/ui/src/components/layout/*` | 4h | P0 | Major | UI-T001 | 各页面标题区样式一致，支持副标题、标签、操作按钮 |
| UI-T003 | 统一 IndustrialPage 页面壳 | `packages/ui/src/components/layout/industrial-page.tsx`, `apps/web-admin/src/app/(admin)/**/page.tsx` | 5h | P0 | Major | UI-T001 | Dashboard / 列表页 / 详情页统一纵向节奏 |
| UI-T004 | 抽象 TableShell 基础层 | `apps/web-admin/src/components/table-shell.tsx`, `packages/data-grid/src/index.tsx`, `apps/web-admin/src/app/(admin)/**/page.tsx` | 6h | P0 | Critical | UI-T002 | 所有列表页使用统一筛选、导出、分页壳 |
| UI-T005 | 抽象 FilterBar 与 ActionToolbar | `apps/web-admin/src/components/table-shell.tsx`, `apps/web-admin/src/components/master/master-list-page.tsx` | 4h | P0 | Major | UI-T004 | 搜索/筛选/批量操作统一，减少页面重复工具条 |
| UI-T006 | 抽象 FormSection 表单分组 | `apps/web-admin/src/components/master/master-create-form.tsx`, `apps/web-admin/src/components/login/login-form-panel.tsx`, `apps/web-admin/src/app/(admin)/**/page.tsx` | 6h | P0 | Critical | UI-T002 | 表单视觉与字段间距统一，支持分组/说明/错误提示 |
| UI-T007 | 统一 StatusBadge 视觉语义 | `apps/web-admin/src/components/**`, `packages/ui/src/components/**` | 4h | P0 | Major | UI-T002 | 状态颜色与文案规范统一，避免硬编码散落 |
| UI-T008 | Dashboard 卡片基座 IndustrialCard | `apps/web-admin/src/components/dashboard/*.tsx`, `apps/web-admin/src/app/(admin)/dashboard/page.tsx` | 8h | P1 | Critical | UI-T001, UI-T002, UI-T007 | KPI / 趋势 / 状态卡统一成单一容器规范 |
| UI-T009 | 通知中心统一为 NotificationPanel | `apps/web-admin/src/components/notification-bell.tsx`, `apps/web-admin/src/components/dashboard/NotificationCenterCard.tsx`, `apps/web-admin/src/app/(admin)/notifications/page.tsx` | 5h | P1 | Major | UI-T007 | 通知铃铛、面板、页面列表视觉一致 |
| UI-T010 | 统一 SideSummaryPanel / 右侧摘要栏 | `apps/web-admin/src/components/dashboard/*.tsx`, `apps/web-admin/src/components/projects/project-actual-costs-panel.tsx` | 6h | P1 | Major | UI-T008 | Dashboard 与详情页右侧摘要风格统一 |
| UI-T011 | Dashboard 首页重构成统一仪表盘 | `apps/web-admin/src/app/(admin)/dashboard/page.tsx`, `apps/web-admin/src/components/dashboard/*` | 8h | P1 | Critical | UI-T008, UI-T009, UI-T010 | 首页卡片、流程、告警、系统状态统一 |
| UI-T012 | 登录页重构为统一认证页模板 | `apps/web-admin/src/components/login/login-form-panel.tsx`, `apps/web-admin/src/components/login/login-industrial-background.tsx` | 5h | P1 | Major | UI-T006 | 登录页结构清晰，品牌区与表单区分离 |
| UI-T013 | Customer 列表页接入统一列表模板 | `apps/web-admin/src/app/(admin)/customers/page.tsx`, `apps/web-admin/src/components/master/master-list-page.tsx` | 5h | P1 | Major | UI-T004, UI-T005 | 客户列表搜索/分页/导出一致 |
| UI-T014 | Supplier 列表页接入统一列表模板 | `apps/web-admin/src/app/(admin)/suppliers/page.tsx` | 4h | P1 | Major | UI-T004, UI-T005 | 供应商列表壳统一 |
| UI-T015 | Materials 列表页接入统一列表模板 | `apps/web-admin/src/app/(admin)/materials/page.tsx` | 4h | P1 | Major | UI-T004, UI-T005 | 材料库列表壳统一 |
| UI-T016 | BOM / Quote 页面统一表单与明细容器 | `apps/web-admin/src/app/(admin)/boms/page.tsx`, `apps/web-admin/src/app/(admin)/quotes/new/page.tsx`, `apps/web-admin/src/app/(admin)/quotes/customer/page.tsx` | 8h | P1 | Critical | UI-T004, UI-T006, UI-T007 | 明细编辑、状态、提示统一 |
| UI-T017 | Projects / Costing 页面统一详情容器 | `apps/web-admin/src/app/(admin)/projects/page.tsx`, `apps/web-admin/src/app/(admin)/costing/page.tsx`, `apps/web-admin/src/components/projects/project-actual-costs-panel.tsx` | 6h | P1 | Major | UI-T002, UI-T010 | 项目详情结构统一 |
| UI-T018 | Procurement / Work Orders 页面统一列表方案 | `apps/web-admin/src/app/(admin)/procurement/page.tsx`, `apps/web-admin/src/app/(admin)/work-orders/page.tsx` | 6h | P1 | Major | UI-T004, UI-T007 | 采购与工单列表页统一 |
| UI-T019 | Workshop / Fieldwork 看板统一 | `apps/web-admin/src/app/(admin)/workshop/page.tsx`, `apps/web-admin/src/app/(admin)/fieldwork/page.tsx`, `apps/web-admin/src/components/dashboard/workshop-status-panel.tsx` | 6h | P2 | Major | UI-T008, UI-T007 | 车间和现场模块保持一致的状态表达 |
| UI-T020 | Files / Notifications / Settings 统一页面模板 | `apps/web-admin/src/app/(admin)/files/page.tsx`, `apps/web-admin/src/app/(admin)/notifications/page.tsx`, `apps/web-admin/src/app/(admin)/settings/page.tsx`, `apps/web-admin/src/app/(admin)/business-settings/page.tsx` | 6h | P2 | Major | UI-T002, UI-T004, UI-T006 | 三类非核心页面壳统一 |
| UI-T021 | 清理 Dashboard 旧重复卡片实现 | `apps/web-admin/src/components/dashboard/*.tsx` | 6h | P2 | Minor | UI-T008, UI-T009, UI-T010 | 移除过时重复卡片与面板实现 |
| UI-T022 | 清理页面内硬编码颜色与样式 | `apps/web-admin/src/app/(admin)/**/page.tsx`, `apps/web-admin/src/components/**` | 8h | P2 | Major | UI-T002, UI-T007 | 颜色与状态尽量引用 token / 组件 prop |
| UI-T023 | 页面级 EmptyState / Loading 状态收口 | `apps/web-admin/src/app/(admin)/**/page.tsx`, `packages/ui/src/components/**` | 4h | P2 | Minor | UI-T004, UI-T006 | 空态和加载态一致 |
| UI-T024 | 细化图标与标题区统一规范 | `apps/web-admin/src/app/(admin)/**/page.tsx`, `apps/web-admin/src/components/**` | 3h | P2 | Minor | UI-T002 | 标题区、图标大小、间距一致 |

---

## 任务执行约束
- 每个任务都应能独立提交一个 Git Commit。
- 每个任务都要只改一个主题，避免大而全提交。
- 每次提交前，先完成对应的基础组件依赖。
- 发现重复页面时，不直接“重构整个前端”，必须拆成可验证的小任务。

## 验收建议
- 每个任务结束后执行：
  - 前端构建检查
  - 关键页面手工打开确认
  - 无新增 ESLint / TypeScript 错误
