# 振航 ERP 前端 UI 重构指令 — 轻科技·工业制造风

> 请严格按照以下规范，逐步重构振航 ERP 前端 UI。  
> 目标风格：**西门子 MES × Tesla UI × 企业级管理后台**  
> 关键词：**干净、专业、现代、轻科技、未来感、好维护**

---

## 一、全局设计 Token（第一步：优先执行）

### 1.1 CSS 变量定义

```css
:root {
  /* ===== 主色调 ===== */
  --color-primary:        #1677ff;
  --color-primary-hover:  #2563eb;
  --color-primary-light:  #e8f1ff;
  --color-primary-dark:   #0958d9;

  /* ===== Sidebar 深蓝 ===== */
  --color-sidebar-bg:      linear-gradient(180deg, #071a2f 0%, #0b2545 100%);
  --color-sidebar-hover:   rgba(22, 119, 255, 0.12);
  --color-sidebar-active:  rgba(22, 119, 255, 0.20);
  --color-sidebar-text:    #b8c7da;
  --color-sidebar-text-active: #ffffff;

  /* ===== 背景 ===== */
  --color-bg-primary:      #f4f8ff;
  --color-bg-secondary:    #f8fafc;
  --color-bg-card:         #ffffff;

  /* ===== 边框与分割线 ===== */
  --color-border:          #e5edf7;
  --color-border-light:    #edf2f9;

  /* ===== 文字 ===== */
  --color-text-primary:    #0f1a2e;
  --color-text-secondary:  #4b5568;
  --color-text-muted:      #8896a8;
  --color-text-placeholder:#b0bec5;

  /* ===== 功能色 ===== */
  --color-success:         #22c55e;
  --color-success-bg:      #e6f9ed;
  --color-warning:         #f59e0b;
  --color-warning-bg:      #fff8e6;
  --color-danger:          #ef4444;
  --color-danger-bg:       #fde8e8;
  --color-info:            #3b82f6;
  --color-info-bg:         #e8f1ff;

  /* ===== 圆角 ===== */
  --radius-sm:             6px;
  --radius-md:             10px;
  --radius-lg:             14px;
  --radius-xl:             18px;
  --radius-button:         8px;

  /* ===== 阴影 ===== */
  --shadow-xs:  0 1px 2px rgba(7, 26, 47, 0.04);
  --shadow-sm:  0 2px 8px rgba(7, 26, 47, 0.06);
  --shadow-md:  0 4px 16px rgba(7, 26, 47, 0.08);
  --shadow-lg:  0 8px 32px rgba(7, 26, 47, 0.10);
  --shadow-card: 0 2px 12px rgba(7, 26, 47, 0.05);

  /* ===== 间距 ===== */
  --space-xs:    4px;
  --space-sm:    8px;
  --space-md:    16px;
  --space-lg:    24px;
  --space-xl:    32px;
  --space-2xl:   48px;

  /* ===== 字体 ===== */
  --font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --font-size-xs:   12px;
  --font-size-sm:   13px;
  --font-size-base: 14px;
  --font-size-lg:   16px;
  --font-size-xl:   20px;
  --font-size-2xl:  26px;
  --font-size-3xl:  32px;

  /* ===== 侧栏宽度 ===== */
  --sidebar-width:        240px;
  --sidebar-collapsed:    68px;
  --topnav-height:        56px;
  --footer-height:        32px;

  /* ===== 过渡 ===== */
  --transition-fast: 0.15s ease;
  --transition-base: 0.25s ease;
}
```

### 1.2 Tailwind 扩展配置

```typescript
// tailwind.config.ts 扩展
colors: {
  brand: {
    50:  '#e8f1ff',
    100: '#c5dcff',
    200: '#9ec5ff',
    300: '#78adff',
    400: '#5c9aff',
    500: '#3d87ff',
    600: '#1677ff',   // 主色
    700: '#2563eb',
    800: '#124bbf',
    900: '#083399',
  },
  sidebar: {
    900: '#071a2f',
    800: '#0b2545',
    700: '#0f3060',
  }
},
borderRadius: {
  'card': '14px',
  'button': '8px',
},
boxShadow: {
  'card': '0 2px 12px rgba(7, 26, 47, 0.05)',
  'card-hover': '0 4px 24px rgba(7, 26, 47, 0.10)',
},
```

### 1.3 全局样式重置

```css
/* globals.css */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html, body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--color-primary); text-decoration: none; }
::selection { background: var(--color-primary-light); }
/* 滚动条 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #c5d2e0; border-radius: 3px; }
```

---

## 二、Layout 布局重构（第二步：执行）

### 2.1 整体结构

```
┌──────────────────────────────────────────────────────┐
│ TopNav 顶部导航  (56px 高度, 白色背景, 底边线1px)     │
├────────────┬────────────────────────────┬────────────┤
│  Sidebar   │                            │  右侧信息栏 │
│  深蓝渐变  │      主内容区              │  可选展开   │
│  240px     │      Main Content          │  320px      │
│            │                            │             │
│  可折叠    │  面包屑导航                 │  通知中心    │
│  多级菜单  │  页面标题 + 操作按钮        │  日程安排    │
│  权限控制  │  卡片式内容区               │  系统公告    │
│            │                            │             │
├────────────┴────────────────────────────┴────────────┤
│ Footer 底部状态栏 (32px, 深色背景)                    │
└──────────────────────────────────────────────────────┘
```

### 2.2 Sidebar 组件规范

```typescript
// 菜单项结构
interface MenuItem {
  id: string;
  label: string;
  icon: React.ReactNode;       // lucide-react 图标
  path?: string;
  permission?: string;         // RBAC 权限码
  badge?: number;              // 角标数
  children?: MenuItem[];
  isExpanded?: boolean;
}
```

**视觉规范：**
- 背景：`linear-gradient(180deg, #071a2f 0%, #0b2545 100%)`
- Logo 区域：高度 64px，顶部 padding 16px，Logo 左侧 + 项目名右侧
- 菜单项高度：44px，间距 2px
- 菜单圆角：8px
- 图标大小：20px × 20px
- 字体大小：14px，颜色 `#b8c7da`
- Hover：背景 `rgba(22,119,255,0.12)`，文字 `#fff`
- Active：背景 `rgba(22,119,255,0.20)`，文字 `#fff`，左侧 3px 蓝色竖条
- 子菜单缩进：左侧 padding 增加 16px
- 折叠按钮：底部，图标 `ChevronLeft`/`ChevronRight`
- 折叠后：仅显示图标，tooltip 显示菜单名

**菜单模块化注册（只改一个文件即可增删模块）：**

```typescript
// config/menu.ts
import { dashboardMenu } from './menus/dashboard';
import { quoteMenu } from './menus/quote';
import { materialMenu } from './menus/material';
import { workflowMenu } from './menus/workflow';
import { fileMenu } from './menus/file';
import { systemMenu } from './menus/system';
// ... 按需导入

export const menuItems: MenuItem[] = [
  dashboardMenu,
  { type: 'divider', label: '业务管理' },
  quoteMenu,
  materialMenu,
  machineMenu,
  customerMenu,
  supplierMenu,
  projectMenu,
  procurementMenu,
  workOrderMenu,
  { type: 'divider', label: '系统管理' },
  workflowMenu,
  fileMenu,
  notificationMenu,
  auditMenu,
  systemMenu,
];
```

### 2.3 TopNav 组件规范

**高度：** 56px  
**背景：** 白色 `#fff`  
**底部边框：** 1px solid `#e5edf7`  
**布局：** flex，justify-between，padding 0 20px

**左侧区域：**
- 折叠按钮（汉堡菜单，仅在 Sidebar 收起的 Tablet 模式下显示）
- 面包屑导航（自动生成，最后一级高亮）

**右侧区域（间距 12px）：**

| 组件 | 说明 |
|------|------|
| 全局搜索 | 搜索框 240px，placeholder "搜索报价单、物料、客户...", ⌘K 快捷键 |
| 通知铃铛 | 角标数字，下拉通知列表（最近5条 + 查看全部） |
| 待办事项 | 角标数字，下拉待审批列表 |
| 消息中心 | 角标数字 |
| 帮助中心 | 下拉（文档/关于/快捷键） |
| 主题切换 | Sun/Moon 图标切换 |
| 用户头像 | 下拉（个人信息/系统设置/退出登录） |
| 右侧信息栏切换 | 展开/收起右侧信息面板 |

### 2.4 FooterStatusBar 组件规范

**高度：** 32px  
**背景：** `#0b2545`  
**文字颜色：** `#8896a8`  
**字体大小：** 12px  
**布局：** flex，右侧信息区

**显示内容（从左到右）：**
- WebSocket 连接状态（绿色/黄色/红色圆点 + 文字 "WS 正常"/"重连中"/"断开"）
- API 状态（绿色/黄色/红色圆点 + "API v1 正常"）
- 当前时间（实时更新）
- 系统版本 "v2.1.0"

### 2.5 右侧信息栏（RightPanel）

**宽度：** 320px（展开）/ 0（折叠）  
**背景：** 白色  
**左侧边框：** 1px solid `#e5edf7`  
**内容：** 3个 Tab

| 区块 | 内容 |
|------|------|
| 通知中心 | 分组（今天/昨天/更早），每条包含图标+标题+时间，未读蓝色圆点 |
| 日程安排 | 日期 + 事项列表，今天高亮 |
| 系统公告 | 公告卡片列表，重要公告红色 Tag |

---

## 三、Dashboard 首页重构（第三步：执行）

### 3.1 布局

```
┌──────────────────────────────────────────────────┐
│  [页面标题] 工作台概览         [日期范围选择器]    │
├──────────┬──────────┬──────────┬────────────────┤
│  KPI 1   │  KPI 2   │  KPI 3   │    KPI 4       │
│ 报价总额  │ 本月订单  │  毛利率   │  待审批数      │
│ ¥2,856万  │  186单   │  23.5%   │    12项        │
│ ↑12.5%   │  ↑8.3%   │ ↑2.1%    │   需处理       │
├──────────┴──────────┴──────────┴────────────────┤
│                                                  │
│  [图表区 - 2/3宽]          [右侧快捷区 - 1/3宽]   │
│  月度报价趋势(折线图)       待办事项快捷入口        │
│                            最近报价单              │
│                            审批状态统计            │
│                                                  │
├────────────────────┬─────────────────────────────┤
│  [1/2宽]           │  [1/2宽]                    │
│  各机型销量(柱状图) │  物料品类占比(饼图)          │
│                    │                             │
├────────────────────┴─────────────────────────────┤
│  [全宽] 最近报价单列表 (表格，前5条，查看全部→)    │
└──────────────────────────────────────────────────┘
```

### 3.2 KpiCard 组件规范

```typescript
interface KpiCardProps {
  title: string;
  value: string | number;
  prefix?: string;        // ¥ / % 等
  suffix?: string;
  trend?: 'up' | 'down' | 'flat';
  trendValue?: string;    // "+12.5%"
  compareLabel?: string;  // "同比增长"
  icon?: React.ReactNode;
  iconBgColor?: string;   // 图标淡色背景
  onClick?: () => void;
  isLoading?: boolean;
}
```

**视觉规范：**
- 卡片：白色背景，圆角 14px，`box-shadow: 0 2px 12px rgba(7,26,47,0.05)`
- Hover：阴影加深 `0 4px 24px rgba(7,26,47,0.10)`
- 布局：左侧图标 + 右侧数据
- 图标区域：48×48px，圆角 12px，淡色背景（如 `#e8f1ff`）
- 标题：14px，`#8896a8`
- 数值：28px，font-weight 700，`#0f1a2e`
- 趋势箭头：↑ 绿色 `#22c55e`，↓ 红色 `#ef4444`
- Skeleton 加载态：灰色脉冲动画

### 3.3 图表区域规范

使用 **Recharts**，统一样式：

```typescript
// 图表通用配置
const chartColors = {
  primary: '#1677ff',
  success: '#22c55e',
  warning: '#f59e0b',
  danger:  '#ef4444',
  purple:  '#8b5cf6',
  cyan:    '#06b6d4',
};
```

- 折线图：`strokeWidth=2`，`dot={false}`，渐变面积填充
- 柱状图：`radius={[6,6,0,0]}`，hover 颜色加深
- 饼图：内半径 60%，外半径 80%，中心显示总数
- Tooltip：白色卡片，圆角 8px，阴影 `shadow-md`
- 所有图表容器圆角 14px，白色背景，padding 20px

### 3.4 快捷入口区

右侧面板包含：
- 待办任务数 + 快捷跳转
- 最近更新的报价单（3条）
- 待审批数量统计（按类型分组）
- "新建报价单"快捷按钮

---

## 四、通用组件抽象（第四步：执行）

### 4.1 StatusBadge 状态标签

```typescript
type StatusVariant = 'draft' | 'pending' | 'approved' | 'rejected' | 'active' | 'inactive' | 'processing';

interface StatusBadgeProps {
  variant: StatusVariant;
  label?: string;
  dot?: boolean;        // 是否显示左侧圆点
}
```

| Variant | 背景色 | 文字色 | 圆点色 |
|---------|--------|--------|--------|
| draft | `#f0f4fa` | `#4b5568` | `#8896a8` |
| pending | `#fff8e6` | `#b45309` | `#f59e0b` |
| approved | `#e6f9ed` | `#166534` | `#22c55e` |
| rejected | `#fde8e8` | `#991b1b` | `#ef4444` |
| active | `#e8f1ff` | `#1e40af` | `#1677ff` |
| inactive | `#f0f0f0` | `#6b7280` | `#9ca3af` |
| processing | `#e8f1ff` | `#1e40af` | `#3b82f6` |

样式：圆角 20px，padding 2px 10px，字体 12px，font-weight 500

### 4.2 RealtimeDot 实时状态指示灯

```typescript
interface RealtimeDotProps {
  status: 'online' | 'reconnecting' | 'offline';
  label?: string;
  size?: 'sm' | 'md';
}
```

- online: `#22c55e` + 呼吸动画（可选）
- reconnecting: `#f59e0b` + 闪烁动画
- offline: `#ef4444`
- 外圈 8px + 内圈 4px，内圈颜色同状态色，外圈 30% 不透明度

### 4.3 DataCard 通用数据卡片容器

```typescript
interface DataCardProps {
  title: string;
  icon?: React.ReactNode;
  extra?: React.ReactNode;     // 右上角操作区
  collapsible?: boolean;
  loading?: boolean;
  className?: string;
  children: React.ReactNode;
}
```

- 白色背景，圆角 14px，阴影 `shadow-card`
- 标题栏：左边图标+标题，右边操作区
- 内容区 padding 20px
- 可折叠时显示折叠箭头

### 4.4 SectionHeader 区块标题

```typescript
interface SectionHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;   // 右侧按钮组
}
```

- 标题 18px，font-weight 600，`#0f1a2e`
- 描述 13px，`#8896a8`
- 左侧竖线装饰（3px 宽，品牌蓝，圆角）

### 4.5 DataTable 数据表格（增强）

基于 shadcn/ui Table 扩展：

- **工具栏区（Toolbar）：** 左侧标题+数量，右侧搜索框+筛选按钮+导出按钮+列设置
- **筛选区（FilterBar）：** 可折叠，多条件筛选（时间范围/状态下拉/关键字）
- **表格主体：** 列头固定，斑马纹（hover行 `#f8fafc`），点击行高亮 `#e8f1ff`
- **批量操作栏：** 选中后出现，显示选中数量 + 批量操作按钮
- **分页：** 底部，左侧显示总计，右侧页码+跳转
- **空状态：** 插图 + "暂无数据" + "新建"按钮

### 4.6 FormDialog 表单弹窗

- 标题栏：左侧图标+标题，右侧关闭按钮
- 内容区：JSON Schema 动态渲染表单
- 底部栏：取消按钮（次要样式）+ 确认按钮（主色）
- 宽度：480px（小）/ 640px（中）/ 800px（大）
- 表单网格：默认 2 列，可配置 1/2/3 列

### 4.7 ApprovalTimeline 审批流程时间线

横向步骤条风格（非纵向）：

```
[① 提交] ─── [② 部门审批 ✓] ─── [③ 财务审批 ●] ─── [④ 总经理审批 ○]
   已完成       已完成(绿勾)         进行中(蓝圈)         待处理(灰圈)
```

- 每步显示：步骤名 + 审批人 + 审批意见(悬浮) + 时间
- 已完成：绿色线条 + 绿色圆点 + 白色勾
- 进行中：蓝色圆点 + 脉冲动画
- 待处理：灰色圆点
- 已拒绝：红色圆点 + 红色文字

---

## 五、页面逐个重构（第五步：执行）

### 5.1 报价单列表页 `/quotes`

**页头：**
- 标题"报价单管理" + 数量统计 + "新建报价单"主按钮
- 快捷筛选 Tab：全部 / 草稿 / 待审批 / 已通过 / 已驳回

**筛选区（可折叠）：**
- 搜索框（报价单号/客户名）
- 日期范围选择器
- 状态下拉选择
- 销售人员下拉
- "查询"+"重置"按钮

**表格列：**
| 报价单号 | 客户名称 | 机型 | 报价金额 | 状态标签 | 创建人 | 创建时间 | 操作 |
|---------|---------|------|---------|---------|--------|---------|------|
| QT-2026-001 | XX公司 | Model-A | ¥128,000 | 待审批 | 张三 | 2026-05-28 | 查看/编辑/删除 |

**操作列按钮风格：**
- 查看：文字链接，`#1677ff`
- 编辑：文字链接
- 删除：文字链接，`#ef4444`，Delete → 确认弹窗
- 更多：三点下拉菜单

### 5.2 报价详情页 `/quotes/:id`

**布局：左右分栏（2:1）**

**左侧主区（Tabs 切换）：**

| Tab | 内容 |
|-----|------|
| 基本信息 | 报价单号、客户、机型、报价金额、BOM明细表、备注 |
| 版本历史 | 版本列表 + 版本对比（左右两栏 diff） |
| 审批记录 | 横向步骤条审批时间线 + 操作记录表 |
| 文件附件 | 关联文件网格列表 |

**右侧信息栏：**
- 状态标签（大号）
- 创建信息（创建人/时间/来源）
- 报价概要（机型/数量/总金额/毛利率）
- 快捷操作按钮组（编辑/提交审批/导出PDF/导出Excel）
- 操作时间线（最近操作记录）

### 5.3 BOM 物料页 `/materials`

**页头：** 标题 + "新增物料"主按钮 + "批量导入"次要按钮

**左侧分类树：**
- 树形组件，展开物料分类
- 每项显示名称 + 数量角标
- 选中高亮（品牌蓝背景）
- 宽度 240px

**右侧表格：**
- 列：物料编码 / 名称 / 规格 / 分类 / 单位 / 状态标签 / 更新时间 / 操作
- 行展开：展开后显示 BOM 子项树（缩进层级）
- 状态流转按钮：草稿→提交审核→审核通过→启用→停用

### 5.4 工作流审批页 `/workflow/my-tasks`

**页头：** 标题"待我审批" + 待审批数量角标

**筛选 Tab：** 全部 / 报价审批 / 物料审批 / 其他

**列表卡片（非表格风格）：**

每个审批任务一张卡片：
```
┌────────────────────────────────────────────────┐
│ [图标]  报价审批                                │
│         报价单号：QT-2026-001                   │
│         申请人：张三    金额：¥128,000            │
│         提交时间：2026-05-28 14:30               │
│                              [查看详情] [审批]   │
└────────────────────────────────────────────────┘
```

**卡片状态颜色左边框：**
- 紧急（<24h）：红色左边框 3px
- 正常：蓝色左边框 3px

**审批弹窗：**
- 显示报价基本信息摘要
- 审批意见文本框
- "通过"按钮（绿色）+ "驳回"按钮（红色）+ "取消"按钮

### 5.5 文件中心 `/files`

**页头：** 标题 + "上传文件"主按钮 + "新建文件夹"次要按钮

**工具栏：**
- 搜索框
- 视图切换（网格/列表图标）
- 排序下拉

**左侧文件夹树：**
- 树形结构（全部文件 / 报价附件 / 物料图纸 / 合同文件 / 其他）
- 每项显示数量角标

**右侧内容区：**

网格视图：
```
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  [图标] │ │  [图标] │ │  [图标] │ │  [图标] │
│ 文件名  │ │ 文件名  │ │ 文件名  │ │ 文件名  │
│  2.3MB  │ │  1.1MB  │ │  5.5MB  │ │  0.8MB  │
│ 05-28   │ │ 05-27   │ │ 05-26   │ │ 05-25   │
└────────┘ └────────┘ └────────┘ └────────┘
```

列表视图：文件名 / 大小 / 类型 / 关联业务 / 上传人 / 上传时间 / 操作

**上传弹窗：**
- 拖拽区域（虚线边框，拖入高亮）
- 选择文件按钮
- 上传进度条

**文件预览：** 新页面或 Drawer，图片/PDF 查看器

### 5.6 登录页 `/login`

**布局：** 左右分栏

**左侧（50%宽）：**
- 深蓝渐变背景（同 Sidebar）
- 居中显示：产品 Logo + 产品名 + Slogan
- Slogan："振航智能制造 · 让制造更智慧"
- 底部：产品特点图标列表（高效/安全/智能/可靠）
- 可选：淡色工业制造插画（轮廓线风格，非3D）

**右侧（50%宽）：**
- 白色背景
- 居中 420px 宽卡片
- 标题"欢迎回来" + 副标题"请输入账号密码登录"
- 账号输入框（前缀用户图标）
- 密码输入框（前缀锁图标 + 后缀显示/隐藏）
- 记住密码 Checkbox + 忘记密码链接
- "登录"按钮（主色，全宽，44px 高度，圆角 8px）
- 底部信息 "振航科技 © 2026"

**登录页额外元素：**
- 无 Sidebar / TopNav
- 背景无网格/噪点
- 不出现霓虹灯效果

---

## 六、主题切换（第六步：执行）

### 6.1 暗色主题 Token

```css
.dark {
  --color-bg-primary:      #0d1521;
  --color-bg-secondary:    #121c2d;
  --color-bg-card:         #162035;
  --color-border:          #1e2d45;
  --color-border-light:    #263550;
  --color-text-primary:    #e8edf5;
  --color-text-secondary:  #a0aec0;
  --color-text-muted:      #6b7d95;

  --shadow-xs:  0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow-sm:  0 2px 8px rgba(0, 0, 0, 0.25);
  --shadow-md:  0 4px 16px rgba(0, 0, 0, 0.3);
  --shadow-card: 0 2px 12px rgba(0, 0, 0, 0.2);
}
```

### 6.2 主题切换实现

- 使用 Zustand `ui-store.ts` 管理主题状态
- 切换时在 `document.documentElement` 上 toggle `dark` class
- 持久化到 localStorage
- 默认跟随系统主题 (`prefers-color-scheme`)
- KpiCard/DataCard 等组件自动适配暗色变量

---

## 七、响应式布局（第七步：执行）

### 7.1 断点定义

| 断点 | 宽度 | 布局变化 |
|------|------|---------|
| XS | < 768px | 仅移动端（审批等场景） |
| SM | 768px - 1024px | 平板，Sidebar 折叠为图标模式，无右侧面板 |
| MD | 1024px - 1366px | 小桌面，Sidebar 折叠为图标模式，可选右侧面板 |
| LG | 1366px - 1920px | 标准桌面，完整三栏布局 |
| XL | > 1920px | 大屏，完整布局 + 可选更多列 |

### 7.2 各断点关键行为

| 元素 | < 1024px | 1024-1366 | > 1366 |
|------|----------|-----------|--------|
| Sidebar | 默认折叠，悬浮展开 | 默认折叠 | 默认展开 |
| 右侧面板 | 隐藏 | 隐藏/可选 | 可选展开 |
| KPI 卡片 | 2列 | 2列 | 4列 |
| 表格 | 水平滚动 | 正常 | 正常 |
| 图表 | 单列堆叠 | 2列 | 2列 |
| 页头按钮 | 图标无文字 | 正常 | 正常 |

---

## 八、实施检查清单

### 第一步：Theme Token
- [ ] CSS 变量全部定义完成
- [ ] Tailwind 配置扩展
- [ ] globals.css 全局样式重置
- [ ] 亮色主题渲染正确
- [ ] 暗色主题渲染正确

### 第二步：Layout 重构
- [ ] Sidebar 深蓝渐变背景 + 菜单项样式
- [ ] 菜单模块化注册机制
- [ ] TopNav 搜索/通知/待办/主题/头像
- [ ] FooterStatusBar WS/API/时间/版本
- [ ] 右侧信息面板
- [ ] 面包屑导航自动生成
- [ ] 折叠/展开动画流畅（0.25s ease）

### 第三步：Dashboard
- [ ] 4个 KPI 卡片
- [ ] 月度趋势折线图
- [ ] 机型销量柱状图
- [ ] 物料占比饼图
- [ ] 最近报价单表格
- [ ] 快捷操作区

### 第四步：通用组件
- [ ] StatusBadge（7种状态）
- [ ] RealtimeDot（3种状态+动画）
- [ ] DataCard 容器
- [ ] SectionHeader
- [ ] DataTable（含Toolbar/FilterBar/分页/空状态）
- [ ] FormDialog
- [ ] ApprovalTimeline
- [ ] KpiCard（含Skeleton态）

### 第五步：页面重构
- [ ] 报价单列表页
- [ ] 报价详情页
- [ ] BOM 物料页
- [ ] 工作流审批页
- [ ] 文件中心
- [ ] 登录页

### 第六步：主题
- [ ] 亮色主题完整
- [ ] 暗色主题完整
- [ ] 切换无闪烁

### 第七步：响应式
- [ ] 1366px 正常
- [ ] 1920px 正常
- [ ] 1024px 平板可用
- [ ] 768px 移动端关键页面可用

---

## 九、禁止事项

- ❌ 大面积霓虹灯光晕
- ❌ CSS 粒子特效 / 雪花 / 星空 / 扫描线
- ❌ 复杂 3D 变换 / Three.js
- ❌ 修改任何 API 接口调用代码
- ❌ 修改数据模型 / TypeScript 类型定义
- ❌ 修改路由参数命名
- ❌ 修改权限判断逻辑
- ❌ 行内样式（统一用 Tailwind class 或 CSS 变量）
- ❌ 一次性重构所有页面（按第五步逐个改）
- ❌ 使用不明所以的 emoji 作为 UI 元素
- ❌ 动画时长超过 300ms
- ❌ 字体大小小于 12px

---

## 十、图标与插图

- 图标统一使用 **lucide-react**（不要混用多种图标库）
- 图标大小规范：导航 20px / 按钮 16px / 表格 14px / 标签 12px
- 空状态插图可使用简单的 SVG 线框图（非 3D 插画）
- 品牌 Logo 单独配置，不在组件中 hardcode

---

> 请按以上规范，**从第一步逐步执行到第七步**，每完成一步请输出可运行的代码。  
> 目标交付物：一个干净、专业、现代、可长期维护的轻科技工业风 ERP 管理后台。