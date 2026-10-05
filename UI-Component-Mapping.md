# UI Component Mapping

> 说明：本文件基于前端代码实现扫描结果整理，目的在于把现有页面映射到统一基础组件池，便于逐项重构与独立提交。

## 统一组件池
- `AppShell`
- `IndustrialPage`
- `PageHeader`
- `FilterBar`
- `ActionToolbar`
- `IndustrialCard`
- `TableShell`
- `FormSection`
- `StatusBadge`
- `TimelinePanel`
- `NotificationPanel`
- `SideSummaryPanel`
- `EmptyState`

## 页面映射

### Dashboard
- 当前实现
  - `apps/web-admin/src/app/(admin)/dashboard/page.tsx`
  - 直接使用多个 `div` 卡片容器、KPI 列表、流程区、车间区、系统概况区
  - 依赖 `@zhenhang/ui` 的 `InlineLoadingBar`、`ErrorBanner`、`typography`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `IndustrialCard`
  - `SideSummaryPanel`
  - `NotificationPanel`
  - `StatusBadge`
- 重构收益
  - Dashboard 统一视觉语言，消除卡片样式漂移
  - 降低首页后续业务模块插入成本
- 风险等级
  - Critical

### Login
- 当前实现
  - `apps/web-admin/src/components/login/login-form-panel.tsx`
  - `apps/web-admin/src/components/login/login-industrial-background.tsx`
- 未来统一组件
  - `IndustrialCard`
  - `FormSection`
  - `PageHeader`
- 重构收益
  - 认证页视觉与结构统一，可复用到邀请登录、试运行登录、管理员登录
- 风险等级
  - Major

### Customers
- 当前实现
  - `apps/web-admin/src/app/(admin)/customers/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
  - `apps/web-admin/src/components/master/master-create-form.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `FilterBar`
  - `ActionToolbar`
  - `TableShell`
  - `FormSection`
  - `EmptyState`
- 重构收益
  - 主数据列表、筛选、导出、编辑体验统一
- 风险等级
  - Critical

### Suppliers
- 当前实现
  - `apps/web-admin/src/app/(admin)/suppliers/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `FilterBar`
  - `TableShell`
  - `StatusBadge`
- 重构收益
  - 统一供应商列表壳与状态展示，减少单页特化逻辑
- 风险等级
  - Major

### Materials
- 当前实现
  - `apps/web-admin/src/app/(admin)/materials/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `FilterBar`
  - `TableShell`
  - `FormSection`
- 重构收益
  - 材料库与分类页共享列表/编辑骨架
- 风险等级
  - Major

### BOM
- 当前实现
  - `apps/web-admin/src/app/(admin)/boms/page.tsx`
  - `apps/web-admin/src/app/(admin)/quotes/new/page.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `TableShell`
  - `FormSection`
  - `StatusBadge`
  - `TimelinePanel`
- 重构收益
  - BOM 编辑与报价 BOM 展示统一，利于成本与版本管理
- 风险等级
  - Critical

### Quotes
- 当前实现
  - `apps/web-admin/src/app/(admin)/quotes/page.tsx`
  - `apps/web-admin/src/app/(admin)/quotes/new/page.tsx`
  - `apps/web-admin/src/app/(admin)/quotes/customer/page.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `FilterBar`
  - `ActionToolbar`
  - `IndustrialCard`
  - `FormSection`
  - `TimelinePanel`
  - `StatusBadge`
- 重构收益
  - 报价列表、报价表单、客户报价页面统一结构
- 风险等级
  - Critical

### Projects
- 当前实现
  - `apps/web-admin/src/app/(admin)/projects/page.tsx`
  - `apps/web-admin/src/components/projects/project-actual-costs-panel.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `IndustrialCard`
  - `SideSummaryPanel`
  - `TimelinePanel`
  - `StatusBadge`
- 重构收益
  - 项目台账和项目成本面板统一信息层级
- 风险等级
  - Major

### Procurement
- 当前实现
  - `apps/web-admin/src/app/(admin)/procurement/page.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `FilterBar`
  - `ActionToolbar`
  - `TableShell`
  - `StatusBadge`
- 重构收益
  - 采购列表与审批入口统一，减少重复操作区
- 风险等级
  - Major

### Workshop
- 当前实现
  - `apps/web-admin/src/app/(admin)/workshop/page.tsx`
  - `apps/web-admin/src/components/dashboard/workshop-status-panel.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `IndustrialCard`
  - `StatusBadge`
  - `SideSummaryPanel`
- 重构收益
  - 车间看板与仪表卡统一视觉与状态语义
- 风险等级
  - Major

### Files
- 当前实现
  - `apps/web-admin/src/app/(admin)/files/page.tsx`
  - `apps/web-admin/src/components/dashboard/RecentFilesCard.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `TableShell`
  - `StatusBadge`
  - `EmptyState`
- 重构收益
  - 文件中心可统一上传、列表、预览、状态显示
- 风险等级
  - Major

### Notifications
- 当前实现
  - `apps/web-admin/src/app/(admin)/notifications/page.tsx`
  - `apps/web-admin/src/components/notification-bell.tsx`
  - `apps/web-admin/src/components/dashboard/NotificationCenterCard.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `NotificationPanel`
  - `StatusBadge`
- 重构收益
  - 通知中心、铃铛、看板通知模块统一展示与已读状态逻辑
- 风险等级
  - Major

### Settings
- 当前实现
  - `apps/web-admin/src/app/(admin)/settings/page.tsx`
  - `apps/web-admin/src/app/(admin)/business-settings/page.tsx`
- 未来统一组件
  - `AppShell`
  - `IndustrialPage`
  - `PageHeader`
  - `FormSection`
  - `ActionToolbar`
- 重构收益
  - 系统设置和业务设置统一表单组织与提交反馈
- 风险等级
  - Major

## 页面补充覆盖
- `Costing`
  - 未来统一组件：`IndustrialPage` / `PageHeader` / `TableShell` / `FormSection`
  - 风险等级：Critical
- `Machines`
  - 未来统一组件：`TableShell` / `FormSection` / `StatusBadge`
  - 风险等级：Major
- `Standards`
  - 未来统一组件：`TableShell` / `FormSection`
  - 风险等级：Minor
- `Fieldwork`
  - 未来统一组件：`TimelinePanel` / `StatusBadge`
  - 风险等级：Major
- `Order Profit`
  - 未来统一组件：`IndustrialCard` / `SideSummaryPanel`
  - 风险等级：Major

## 统一方案
1. 先统一 `AppShell` 与 `PageHeader`，保证全站导航与页面标题一致。
2. 再统一 `IndustrialPage`、`TableShell`、`FormSection`，覆盖绝大多数列表和表单页。
3. 然后统一 `IndustrialCard`、`StatusBadge`、`NotificationPanel`、`SideSummaryPanel`，收敛 Dashboard 和详情页变体。
4. 最后处理登录页与特殊页面，保证视觉收口。

## 预计重构收益
- 统一卡片/表格/表单/状态的语义与视觉
- 减少页面内局部样式与特化逻辑
- 提升新增页面速度
- 减少后续主题切换和设计调整成本
