export type MenuItem = {
  key: string;
  title: string;
  href: string;
  permission: string;
  placeholder?: boolean;
  /** 路由保留、代码保留，但不在侧栏展示 */
  hidden?: boolean;
  /** 业务设置开关字段，关闭时不显示菜单 */
  featureFlag?: "accounting_enabled" | "quote_receivable_enabled" | "procurement_approval_enabled";
};

export type MenuGroup = {
  key: string;
  title: string;
  items: MenuItem[];
  /** 侧栏子菜单默认展开（可被用户折叠状态覆盖） */
  defaultExpanded?: boolean;
};

/** V2.0 信息架构 — 侧栏可见分组 */
export const APP_MENU_GROUPS: MenuGroup[] = [
  {
    key: "cockpit",
    title: "运营驾驶舱",
    items: [{ key: "dashboard", title: "运营看板", href: "/dashboard", permission: "dashboard:view" }],
  },
  {
    key: "quotes",
    title: "报价中心",
    items: [
      { key: "quotes", title: "报价中心", href: "/quotes", permission: "business:quote:read" },
      { key: "quotes-customer", title: "对客报价", href: "/quotes/customer", permission: "business:quote:read" },
    ],
  },
  {
    key: "projects",
    title: "项目管理",
    items: [
      { key: "projects", title: "项目台账", href: "/projects", permission: "business:project:read" },
      { key: "costing", title: "成本核算", href: "/costing", permission: "business:cost_estimate:read" },
      { key: "order-profit", title: "订单利润", href: "/order-profit", permission: "business:project:read" },
    ],
  },
  {
    key: "products",
    title: "产品管理",
    defaultExpanded: false,
    items: [
      { key: "products", title: "产品库", href: "/products", permission: "master:product:read" },
      { key: "machines", title: "机型管理", href: "/machines", permission: "master:machine:read" },
      { key: "boms", title: "BOM 管理", href: "/boms", permission: "master:bom:read" },
      { key: "product-cost-templates", title: "成本模板", href: "/product-cost-templates", permission: "master:product_cost_template:read" },
      { key: "product-price-templates", title: "售价模板", href: "/product-price-templates", permission: "master:product_price_template:read" },
      { key: "option-groups", title: "选项组", href: "/option-groups", permission: "master:machine:read" },
      { key: "equipment-units", title: "设备序列号", href: "/equipment-units", permission: "master:equipment_unit:read" },
      { key: "acceptance", title: "验收管理", href: "/acceptance", permission: "master:machine:read" },
      { key: "installation", title: "安装调试", href: "/installation", permission: "master:machine:read" },
    ],
  },
  {
    key: "master",
    title: "基础数据",
    defaultExpanded: false,
    items: [
      { key: "customers", title: "客户管理", href: "/customers", permission: "master:customer:read" },
      { key: "suppliers", title: "供应商库", href: "/suppliers", permission: "master:supplier:read" },
      { key: "materials", title: "材料库", href: "/materials", permission: "master:material:read" },
      { key: "standards", title: "基础标准", href: "/standards", permission: "master:standard:read" },
    ],
  },
  {
    key: "supply",
    title: "供应链与生产",
    defaultExpanded: false,
    items: [
      { key: "procurement", title: "采购管理", href: "/procurement", permission: "business:procurement:read" },
      { key: "work-orders", title: "车间工单", href: "/work-orders", permission: "business:work_order:read" },
      { key: "fieldwork", title: "现场作业", href: "/fieldwork", permission: "business:fieldwork:read" },
      { key: "aftersales", title: "售后服务", href: "/aftersales", permission: "business:aftersales:read" },
      { key: "workshop", title: "车间看板", href: "/workshop", permission: "business:quote:read" },
    ],
  },
  {
    key: "finance",
    title: "财务中心",
    defaultExpanded: false,
    items: [
      {
        key: "accounting-ledger",
        title: "账目明细",
        href: "/accounting/ledger",
        permission: "business:accounting:read",
        featureFlag: "accounting_enabled",
      },
      {
        key: "accounting",
        title: "收支台账",
        href: "/accounting",
        permission: "business:accounting:read",
        featureFlag: "accounting_enabled",
      },
      {
        key: "accounting-supplier",
        title: "供应商台账",
        href: "/accounting/supplier-ledger",
        permission: "business:accounting:read",
        featureFlag: "accounting_enabled",
      },
    ],
  },
  {
    key: "platform",
    title: "平台中心",
    items: [
      { key: "approvals", title: "审批中心", href: "/approvals", permission: "business:approval:read" },
      { key: "audits", title: "审计日志", href: "/audits", permission: "platform:audit:read" },
      { key: "files", title: "文件中心", href: "/files", permission: "platform:file:read" },
      { key: "notifications", title: "通知中心", href: "/notifications", permission: "platform:notification:read" },
      { key: "business-settings", title: "业务设置", href: "/business-settings", permission: "platform:config:read" },
      { key: "system", title: "系统设置", href: "/settings", permission: "platform:config:read", hidden: true },
      { key: "users", title: "用户管理", href: "/users", permission: "system:user:read" },
      { key: "roles", title: "角色管理", href: "/roles", permission: "system:role:read" },
      {
        key: "departments",
        title: "部门管理",
        href: "/departments",
        permission: "system:department:read",
      },
      { key: "tenants", title: "租户管理", href: "/tenants", permission: "system:tenant:read" },
    ],
  },
];

/**
 * 隐藏菜单 — 路由与页面代码保留，仅不在侧栏展示。
 * 含：BOM、机型管理、文件中心；AI/MES 无独立 Web 菜单项。
 */
export const HIDDEN_APP_MENUS: MenuItem[] = [
  { key: "product-categories", title: "产品分类", href: "/product-categories", permission: "master:product_category:read", hidden: true },
];

/** 全量菜单（含隐藏项），用于路由高亮与标题解析 */
export const APP_MENUS: MenuItem[] = [
  ...APP_MENU_GROUPS.flatMap((group) => group.items),
  ...HIDDEN_APP_MENUS,
];

/** V2.0 路由 → 信息架构分组映射（URL 不变，仅文档/调试用途） */
export const ROUTE_GROUP_MAP: Record<string, { group: string; groupKey: string; routeGroup: string }> = {
  "/users": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/roles": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/departments": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/tenants": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/dashboard": { group: "运营驾驶舱", groupKey: "cockpit", routeGroup: "(cockpit)" },
  "/quotes": { group: "报价中心", groupKey: "quotes", routeGroup: "(quotes)" },
  "/quotes/customer": { group: "报价中心", groupKey: "quotes", routeGroup: "(quotes)" },
  "/quotes/new": { group: "报价中心", groupKey: "quotes", routeGroup: "(quotes)" },
  "/projects": { group: "项目管理", groupKey: "projects", routeGroup: "(projects)" },
  "/costing": { group: "项目管理", groupKey: "projects", routeGroup: "(projects)" },
  "/order-profit": { group: "项目管理", groupKey: "projects", routeGroup: "(projects)" },
  "/customers": { group: "基础数据", groupKey: "master", routeGroup: "(products)" },
  "/product-categories": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/products": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/product-cost-templates": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/product-price-templates": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/equipment-units": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/machines": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/boms": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/acceptance": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/installation": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/materials": { group: "基础数据", groupKey: "master", routeGroup: "(products)" },
  "/suppliers": { group: "基础数据", groupKey: "master", routeGroup: "(products)" },
  "/standards": { group: "基础数据", groupKey: "master", routeGroup: "(products)" },
  "/procurement": { group: "供应链与生产", groupKey: "supply", routeGroup: "(supply)" },
  "/work-orders": { group: "供应链与生产", groupKey: "supply", routeGroup: "(supply)" },
  "/fieldwork": { group: "供应链与生产", groupKey: "supply", routeGroup: "(supply)" },
  "/aftersales": { group: "供应链与生产", groupKey: "supply", routeGroup: "(supply)" },
  "/workshop": { group: "供应链与生产", groupKey: "supply", routeGroup: "(supply)" },
  "/accounting": { group: "财务中心", groupKey: "finance", routeGroup: "(finance)" },
  "/accounting/ledger": { group: "财务中心", groupKey: "finance", routeGroup: "(finance)" },
  "/accounting/supplier-ledger": { group: "财务中心", groupKey: "finance", routeGroup: "(finance)" },
  "/option-groups": { group: "产品管理", groupKey: "products", routeGroup: "(products)" },
  "/audits": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/approvals": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/notifications": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/business-settings": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/settings": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
  "/files": { group: "平台中心", groupKey: "platform", routeGroup: "(platform)" },
};
