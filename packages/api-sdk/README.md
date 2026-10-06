# @zhenhang/api-sdk

**这是一个手写的、目前没有任何地方引用的 24 行类型桩，不是生成产物。** 本节记录 2026-02 实测到的事实，
以免读者被目录名误导。

## 现状（实测）

| 事实 | 证据 |
| --- | --- |
| `src/generated/index.ts` 是**手写**的，仅 24 行 / 669 字节 | 内容为 `ApiPageResponse<T>`、`LoginRequest`、`LoginResponse` 三个类型和一个手写的 `AuthApi.login` |
| **没有任何源码导入本包** | 全仓库 7 处引用全部是构建/配置元数据（根 `package.json`、`package-lock.json`、根与 `apps/web-admin` 的 `eslint.config.mjs`、`apps/web-admin/next.config.ts`、`apps/web-admin/package.json`），没有一条 `import ... from "@zhenhang/api-sdk"` |
| `npm run generate`（根脚本 `sdk:generate`）**无法独立运行** | 它读取 `http://localhost:8000/openapi.json`，需要一个正在运行的 API |
| `npm run generate:local` **也无法运行** | 它读取 `../../backend/openapi.json`，而**该文件不在仓库中** |
| 一旦真跑起来，会**整个覆盖**上面那个手写文件 | 生成器的 `--output src/generated` 指向同一目录，且后端实际暴露 **171 条路径 / 214 个 schema** |

生成器本身是装好的（`openapi-typescript-codegen`），所以两条路径失败的原因分别是"缺服务"和"缺输入文件"，
不是工具缺失。

## 如果要让这一层变成真的

最小改法是给 `generate:local` 补上一个前置步骤，让后端自己导出规范（`app.openapi()` 可直接生成 171 条路径
的完整文档），再据其生成客户端——但那会**覆盖**当前手写文件，因此需要先决定保留哪些手写类型。
`src/generated/index.ts` 目前被 `tsconfig.packages.json` 的类型检查覆盖，所以它是**合法的 TypeScript**，
只是没人用。

## 建议

三选一，属于结构性决策：

1. **删除本包**（并清理 `next.config.ts` 与两个 eslint 配置里的引用）——前端目前只用 `@zhenhang/http-client`、
   `@zhenhang/query-hooks`、`@zhenhang/realtime`，本包没有消费者。
2. **做成真实的生成层**：补一个导出规范的脚本，把 `generate:local` 变成可运行的两步，并决定手写类型的去留。
3. **保持现状**，但不要再把它当作"已对齐的 SDK 层"。
