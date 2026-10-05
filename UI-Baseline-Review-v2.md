# UI Baseline Review v2

> 目的：验证 Sprint 1.5 页面级接入修正是否真实落地。\
> 范围：仅审核 `Dashboard` / `Login` / `Customer` / `Supplier` / `Material` / `Project`。

## 审核总览
- `Customer`：PASS
- `Supplier`：PASS
- `Material`：PASS
- `Project`：PASS
- `Dashboard`：PARTIAL
- `Login`：PARTIAL

## 页面逐项审核

### Dashboard
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/dashboard/page.tsx`
- 是否接入 AppShell
  - **PASS**
- 是否接入 PageHeader
  - **FAIL**
- 是否接入 IndustrialPage
  - **FAIL**
- 是否存在旧 Header
  - **YES**
- 是否存在双 Page Container
  - **YES**
- 是否存在旧布局残留
  - **YES**
- 是否存在样式冲突
  - **YES**
- 判定
  - **PARTIAL**

### Login
- 页面截图位置
  - `apps/web-admin/src/app/login/page.tsx`
  - `apps/web-admin/src/components/login/login-form-panel.tsx`
- 是否接入 AppShell
  - **PASS**（登录页本身不应接入后台壳层）
- 是否接入 PageHeader
  - **FAIL**
- 是否接入 IndustrialPage
  - **FAIL**
- 是否存在旧 Header
  - **YES**
- 是否存在双 Page Container
  - **YES**
- 是否存在旧布局残留
  - **YES**
- 是否存在样式冲突
  - **YES**
- 判定
  - **PARTIAL**

### Customer
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/customers/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
- 是否接入 AppShell
  - **PASS**
- 是否接入 PageHeader
  - **PASS**
- 是否接入 IndustrialPage
  - **PASS**
- 是否存在旧 Header
  - **NO**
- 是否存在双 Page Container
  - **NO**
- 是否存在旧布局残留
  - **NO**
- 是否存在样式冲突
  - **LOW**
- 判定
  - **PASS**

### Supplier
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/suppliers/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
- 是否接入 AppShell
  - **PASS**
- 是否接入 PageHeader
  - **PASS**
- 是否接入 IndustrialPage
  - **PASS**
- 是否存在旧 Header
  - **NO**
- 是否存在双 Page Container
  - **NO**
- 是否存在旧布局残留
  - **NO**
- 是否存在样式冲突
  - **LOW**
- 判定
  - **PASS**

### Material
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/materials/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
- 是否接入 AppShell
  - **PASS**
- 是否接入 PageHeader
  - **PASS**
- 是否接入 IndustrialPage
  - **PASS**
- 是否存在旧 Header
  - **NO**
- 是否存在双 Page Container
  - **NO**
- 是否存在旧布局残留
  - **NO**
- 是否存在样式冲突
  - **LOW**
- 判定
  - **PASS**

### Project
- 页面截图位置
  - `apps/web-admin/src/app/(admin)/projects/page.tsx`
  - `apps/web-admin/src/components/master/master-list-page.tsx`
- 是否接入 AppShell
  - **PASS**
- 是否接入 PageHeader
  - **PASS**
- 是否接入 IndustrialPage
  - **PASS**
- 是否存在旧 Header
  - **NO**
- 是否存在双 Page Container
  - **NO**
- 是否存在旧布局残留
  - **NO**
- 是否存在样式冲突
  - **LOW**
- 判定
  - **PASS**

## Sprint 1.5 审核结论
- `Customer` / `Supplier` / `Material` / `Project` 已达到页面级接入标准。
- `Dashboard` 与 `Login` 不在本次页面接入修正范围内，仍保留旧布局与旧 Header 属于预期。

## 是否允许进入 Sprint 2
- **允许进入 Sprint 2：否**
- 理由：虽然四个主数据页面已 PASS，但本次审核范围明确要求保留 Dashboard / Login 未重构状态，因此整体 Sprint 1.5 仍不能按“全量完成”判定。

## 备注
- 如果后续只以主数据页面为 Sprint 1.5 范围，则可视为完成；
- 但按本次审核范围（含 Dashboard / Login）综合判定，仍为 `PARTIAL`。
