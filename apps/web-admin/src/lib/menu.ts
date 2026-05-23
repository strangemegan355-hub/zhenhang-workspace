export type MenuItem = {
  key: string;
  title: string;
  href: string;
  permission: string;
};

export const APP_MENUS: MenuItem[] = [
  { key: "dashboard", title: "Dashboard", href: "/dashboard", permission: "dashboard:view" },
  {
    key: "notifications",
    title: "Notifications",
    href: "/notifications",
    permission: "platform:notification:read",
  },
  { key: "quotes", title: "Quotes", href: "/quotes", permission: "business:quote:read" },
  { key: "quotes-new", title: "New Quote", href: "/quotes/new", permission: "business:quote:create" },
];
