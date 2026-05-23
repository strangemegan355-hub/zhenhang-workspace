"use client";

import { IndustrialPanel, typography } from "@zhenhang/ui";
import { designTokens } from "@zhenhang/ui";

type SystemStatusPanelProps = {
  apiUptimeSeconds?: number;
  errorRate?: number;
  wsConnections?: number;
  hotEvents?: number;
};

export function SystemStatusPanel({
  apiUptimeSeconds = 0,
  errorRate = 0,
  wsConnections = 0,
  hotEvents = 0,
}: SystemStatusPanelProps) {
  const uptimeH = Math.floor(apiUptimeSeconds / 3600);
  const uptimeM = Math.floor((apiUptimeSeconds % 3600) / 60);
  const apiOk = errorRate < 0.05;

  const rows = [
    { label: "API 可用性", value: apiOk ? "正常" : "降级", ok: apiOk },
    { label: "运行时长", value: `${uptimeH}h ${uptimeM}m`, ok: true },
    { label: "实时连接", value: String(wsConnections), ok: wsConnections >= 0 },
    { label: "热事件缓存", value: String(hotEvents), ok: true },
  ];

  return (
    <IndustrialPanel title="系统状态">
      <ul className="space-y-2">
        {rows.map((row) => (
          <li key={row.label} className="flex items-center justify-between text-sm">
            <span className={typography.body}>{row.label}</span>
            <span
              className={typography.monoNumber}
              style={{ color: row.ok ? designTokens.colors.success.default : designTokens.colors.warning.default }}
            >
              {row.value}
            </span>
          </li>
        ))}
      </ul>
    </IndustrialPanel>
  );
}
