"use client";

import { EmptyState, IndustrialPage, IndustrialPanel, typography } from "@zhenhang/ui";
import Link from "next/link";

export default function SettingsPage() {
  return (
    <IndustrialPage gap="md" fill>
      <IndustrialPanel fill title="系统设置">
        <EmptyState
          message="在线配置中心尚未开放"
          hint="生产配置（密钥、数据库、MinIO 等）请联系系统管理员在服务器维护，本页面不提供在线修改。"
        />
        <p className={`${typography.caption} mt-4 text-center text-amber-700 dark:text-amber-400`}>
          部署与运维说明请参阅 docs/ENTERPRISE_DEPLOYMENT.md
        </p>
        <p className={`${typography.caption} mt-2 text-center`}>
          返回 <Link href="/dashboard" className="text-blue-500 hover:underline">运营看板</Link>
        </p>
      </IndustrialPanel>
    </IndustrialPage>
  );
}
