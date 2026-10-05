# workshop-terminal · 车间数字看板

Vite + React 车间终端，接入 `/api/v1/workshop/board` 与实时事件。

## 开发

```bash
cp .env.example .env.local   # 可选
npm run dev -w workshop-terminal   # http://localhost:5175
```

账号：由后端 `BOOTSTRAP_ADMIN_PASSWORD` 决定（本仓库不再提供默认口令）

## 能力

- 登录 / JWT
- 报价队列、产线状态、设备状态、工业报警（看板 API）
- 点击报价行 → BOM 模块树（只读）
- 离线 / 断网提示 + SSE/WS 实时刷新

## 构建

```bash
npm run build -w workshop-terminal
```
