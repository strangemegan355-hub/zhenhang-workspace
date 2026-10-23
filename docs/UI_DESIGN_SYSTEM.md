# UI 设计系统（振航 ERP）

> 目标：**浅色科技感工业风 + 现代企业 SaaS + 数据工作台**  
> 现状：`globals.css` 已落地主色 `#1677ff` 与深蓝侧栏（2026-10-23）；细部页面仍按 Backlog 逐页对齐。

---

## 1. 色彩

| Token | 目标值 | 用途 |
|---|---|---|
| `--color-primary` | `#1677ff` | 主按钮、链接、选中态 |
| `--color-primary-hover` | `#0958d9` | 悬停 |
| `--color-primary-soft` | `#e6f4ff` | 选中行、轻背景 |
| `--color-bg` | `#f5f7fa` | 页面底 |
| `--color-surface` | `#ffffff` | 卡片/表格底 |
| `--color-border` | `#d9e0e7` | 分割线 |
| `--color-text` | `#1f2933` | 正文 |
| `--color-text-muted` | `#64748b` | 次要说明 |
| `--color-success` | `#16a34a` | 成功/完成 |
| `--color-warning` | `#d97706` | 警告 |
| `--color-danger` | `#dc2626` | 错误/危险操作 |

侧栏导航：深蓝 `#001529` 或 `#0f172a`（二选一，实施时统一），文字 `#ffffff` / `#94a3b8`。

**状态**：主色与侧栏 token 已于 2026-10-23 写入 `apps/web-admin/src/app/globals.css`（`--color-primary: #1677ff`，侧栏 `--color-sidebar`）。

---

## 2. 字体

-  family：Inter / "PingFang SC" / "Microsoft YaHei"（沿用）  

-  根字号：16px（建议从 18px 回调，提高数据密度 — 实施时 A/B）  
-  标题：页面 `text-xl`/`1.25rem` semibold；卡片标题 `text-base` medium  

---

## 3. 间距与圆角

| Token | 值 |
|---|---|
| `--radius-card` | `8px` |
| `--radius-btn` | `6px` |
| 页面水平 padding | `24px`（`max-w-[1600px]` 居中） |
| 卡片内 padding | `16px–20px` |
| 表格行高 | ≥ `44px` |

---

## 4. 组件（复用 `packages/ui`）

| 组件 | 用途 |
|---|---|
| `PageHeader` | 标题 + 描述 + 主操作（`packages/ui`；页内仅一个 `primary` 主操作） |
| `FilterBar` | 列表筛选行（`role="search"`；搜索 + 2–4 高频筛选项） |
| `IndustrialPage` | 页面纵向节奏 |
| MasterListPage / data-grid | 列表、筛选、分页；金额/数量列用 `GridColumn.align: "right"`（`tabular-nums`） |
| `StatusBadge` | 统一状态色 |
| 表单分组区块（Form section） | 表单分组 |
| `btn-primary` / `btn-secondary` | 全局按钮类（globals.css） |
| `moneyCellClass`（`form-styles.ts`） | 金额列：右对齐 + `tabular-nums` |
| `filterFieldClass` / `filterCheckClass` | FilterBar 字段最小宽度与勾选行高对齐 |

---

## 5. 数据展示

- 金额：右对齐、千分位、`tabular-nums`（优先用 `moneyCellClass`）；`CNY` 前缀或列标题注明  
- 日期：`YYYY-MM-DD` 展示，存储 ISO  
- 空态：说明原因 + 主操作按钮（如「新建报价」）  
- 加载：表格 skeleton，禁止长时间无反馈  

---

## 6. 图标

- Lucide，线宽一致，列表 16px，按钮 18px  

---

## 7. 暗色模式

- `next-themes` 已依赖；工业 ERP 默认 **浅色**；暗色为次要（车间端可单独主题）  

---

## 8. 迁移策略

1. 先改 `:root` token，不改布局。  
2. 再改 `app-shell` 侧栏色。  
3. 按 Backlog T001→T007 逐页替换硬编码色。  

验收：关键 6 页截图对比 + `build:web` + 无 a11y 回归（后续）。
