# mobile-app · 移动审批

Vite + React 工业移动审批端，接入真实 API 与实时事件。

## 开发

```bash
cp .env.example .env.local   # 可选
npm run dev -w mobile-app    # http://localhost:5174
```

账号：`admin` / `Admin@123456`

## 能力

- 登录 / JWT
- 待审报价列表（`reviewing` 状态）
- 审批通过 / 驳回（`useQuoteTransitionMutation`）
- 离线队列（`enqueueOfflineMutation` + 联网 `flushOffline`）
- 通知未读与标记已读
- KPI 条 + `useIndustrialRealtimeBridge` 实时刷新

## 构建

```bash
npm run build -w mobile-app
```
