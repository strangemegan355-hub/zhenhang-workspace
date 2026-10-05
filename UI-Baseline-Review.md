# UI Baseline Review

> 目的：验证 Sprint 1（UI-T001 / UI-T002 / UI-T003）实际落地情况。\
> 范围：仅审核，不修改代码；不进入 Sprint 2。

## 审核结论总览
- **Sprint 1 审核结论：PARTIAL**
- **是否允许进入 Sprint 2：否**
- 原因：基础组件已开始落地，但页面级接入并未完成；Dashboard / Customer / Supplier / Material / Project 仍大量使用旧页面壳和旧卡片布局，尚未统一接入 `PageHeader` / `IndustrialPage` / `AppShell` 的标准路径。

---

## 1. Dashboard
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/dashboard/page.tsx`
- 是否接入 AppShell
  - **PASS**（Dashboard 位于 admin 布局树下，运行时由全站壳层包裹）
- 是否接入 PageHeader
  - **FAIL**
- 是否接入 IndustrialPage
  - **FAIL**
- 是否存在旧布局残留
  - **YES**：页面仍是手写 `header + 多个 section + 多个 card div` 的页面壳
- 是否存在样式冲突
  - **YES**：大量页面内硬编码 `bg-white` / `border-[var(--color-border)]` / `rounded-[12px]`，与基础组件统一目标不一致
- 是否存在重复 Header
  - **YES**：页面内自定义 header 与未来统一 `PageHeader` 重复
- 是否存在重复 Page Container
  - **YES**：页面根容器 `.space-y-6` + 多级 section 卡片容器
- 判定
  - **PARTIAL**

---

## 2. Login
- 页面截图位置
  - `apps/web-admin/src/app/login/page.tsx`
  - `apps/web-admin/src/components/login/login-form-panel.tsx`
- 是否接入 AppShell
  - **PASS**（登录页通常不应接入后台 AppShell；当前为独立认证页）
- 是否接入 PageHeader
  - **FAIL**
- 是否接入 IndustrialPage
  - **FAIL**
- 是否存在旧布局残留
  - **YES**：登录页仍是独立全屏认证布局，未纳入统一页面骨架
- 是否存在样式冲突
  - **YES**：登录页使用大量局部渐变/背景/卡片样式，未复用统一页面壳组件
- 是否存在重复 Header
  - **YES**：品牌区与标题区属于登录页内部定制 header 逻辑
- 是否存在重复 Page Container
  - **YES**：`min-h-screen` + 自定义背景容器为独立页面容器
- 判定
  - **PARTIAL**

---

## 3. Customer
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/customers/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
- 是否接入 AppShell
  - **PASS**（运行在 admin 布局下）
- 是否接入 PageHeader
  - **FAIL**
- 是否接入 IndustrialPage
  - **PASS**（已通过 `MasterListPage` / `IndustrialPage` 组合）
- 是否存在旧布局残留
  - **YES**：列表页标题、操作区和筛选区仍由 `MasterListPage` 内部封装，尚未显式改为统一 `PageHeader` / `FilterBar` / `ActionToolbar`
- 是否存在样式冲突
  - **YES**：列表页仍有页面内级别的列表壳样式依赖
- 是否存在重复 Header
  - **YES**：`MasterListPage` 内部自带标题区，未来 `PageHeader` 接入后会形成重复风险
- 是否存在重复 Page Container
  - **YES**：`MasterListPage` + `IndustrialPage` 叠加式结构仍存在
- 判定
  - **PARTIAL**

---

## 4. Supplier
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/suppliers/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
  - `apps/web-admin/src/components/master/master-create-form.tsx`
- 是否接入 AppShell
  - **PASS**
- 是否接入 PageHeader
  - **FAIL**
- 是否接入 IndustrialPage
  - **PASS**（页面最外层已使用 `IndustrialPage`）
- 是否存在旧布局残留
  - **YES**：仍使用 `MasterListPage` + `MasterCreateForm` 组合，没有显式统一到基础组件池
- 是否存在样式冲突
  - **YES**：表单区域与列表区域样式体系仍不统一
- 是否存在重复 Header
  - **YES**：列表组件内部标题区与未来 `PageHeader` 方向重复
- 是否存在重复 Page Container
  - **YES**：`IndustrialPage` 外层 + `MasterListPage` 内层双容器结构
- 判定
  - **PARTIAL**

---

## 5. Material
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/materials/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
  - `apps/web-admin/src/components/master/master-create-form.tsx`
- 是否接入 AppShell
  - **PASS**
- 是否接入 PageHeader
  - **FAIL**
- 是否接入 IndustrialPage
  - **PASS**
- 是否存在旧布局残留
  - **YES**：继续依赖 `MasterListPage` / `MasterCreateForm` 的传统组合
- 是否存在样式冲突
  - **YES**：基础标准选择与材料录入表单尚未统一成 FormSection 结构
- 是否存在重复 Header
  - **YES**
- 是否存在重复 Page Container
  - **YES**
- 判定
  - **PARTIAL**

---

## 6. Project
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/projects/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
  - `apps/web-admin/src/components/master/master-create-form.tsx`
  - `apps/web-admin/src/components/projects/project-actual-costs-panel.tsx`
- 是否接入 AppShell
  - **PASS**
- 是否接入 PageHeader
  - **FAIL**
- 是否接入 IndustrialPage
  - **PASS**
- 是否存在旧布局残留
  - **YES**：页面内仍自建 `KpiCard`、`IndustrialPanel`、`MasterListPage` 多层组合
- 是否存在样式冲突
  - **YES**：项目详情、盈亏面板、列表壳使用不同视觉来源
- 是否存在重复 Header
  - **YES**
- 是否存在重复 Page Container
  - **YES**
- 判定
  - **PARTIAL**

---

## Sprint 1 审核结论
- `UI-T002` / `UI-T003` 已有基础组件实现痕迹，但**页面侧统一接入尚未完成**。
- `UI-T001` 的壳层已存在，但全站页面仍大量保留旧式页面容器和局部标题块。
- 当前更准确的状态是：**基础组件已搭好，页面改造尚处于中间阶段**。

## 最终结论
- **Sprint 1 审核结论：PARTIAL**
- **是否允许进入 Sprint 2：否**

## 审核依据
1. `Dashboard` 仍为手写多区块布局，没有接入 `PageHeader` / `IndustrialPage` 统一页壳。
2. `Customer` / `Supplier` / `Material` / `Project` 仍主要依赖 `MasterListPage` 与 `MasterCreateForm` 的旧组合方式。
3. `Login` 为独立认证页，尚未纳入统一页面骨架，但这不构成错误，只是说明其未参与 `AppShell` 体系。
4. 多页面仍有重复标题区、重复页面容器和样式来源分裂的问题。

## 建议
- 先完成页面级接入统一：`PageHeader`、`IndustrialPage`、`AppShell`
- 再进入 `FilterBar` / `ActionToolbar` / `TableShell`
- 之后再评估是否允许进入 Sprint 2
