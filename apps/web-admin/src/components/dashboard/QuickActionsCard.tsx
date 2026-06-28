"use client";

import Link from "next/link";
import {
  FileUp,
  FolderPlus,
  PackagePlus,
  PlusCircle,
  Users,
  Wrench,
} from "lucide-react";
import { DashboardCard } from "./dashboard-card";

const ACTIONS = [
  { href: "/quotes?create=1", label: "新建报价", icon: PlusCircle },
  { href: "/projects", label: "新建项目", icon: FolderPlus },
  { href: "/procurement", label: "新建采购", icon: PackagePlus },
  { href: "/work-orders", label: "新建工单", icon: Wrench },
  { href: "/files", label: "上传文件", icon: FileUp },
  { href: "/customers", label: "客户管理", icon: Users },
] as const;

export function QuickActionsCard() {
  return (
    <DashboardCard title="快捷入口">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {ACTIONS.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="group flex flex-col items-center gap-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-3 py-3 text-center transition hover:bg-white"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded bg-[var(--color-primary-soft)] text-[var(--color-text)]">
              <action.icon className="h-4 w-4" />
            </div>
            <span className="text-[11px] font-medium text-[var(--color-text)]">{action.label}</span>
          </Link>
        ))}
      </div>
    </DashboardCard>
  );
}
