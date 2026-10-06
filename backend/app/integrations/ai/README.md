## AI extension hooks (planned)

> **现状（已实测）**：本目录目前**只有一个 `__init__.py` 占位**，无任何模块导入它。真实的 AI 代码不在
> 这里，而在 `app/api/v1/endpoints/ai.py`（`GET /ai/copilot/quote-summary`）、
> `app/domains/quote/application/industrial_copilot.py` 与 `app/models/ai.py`
> （`ai_documents` / `ai_embeddings` / `embedding_tasks`）。下面的布局是**建议**，不是现状。
>
> 下方第 5 条"AI 不得绕过 repository、须遵守 RBAC 与租户边界"曾被实测出**两处未做到**并已修复：copilot
> 摘要与报价流转此前都未应用数据范围（`repo.get_quote` 提供了 `predicate` 接缝，另外三处调用都传了，
> 这两处漏了）。**任何新增的 AI 入口都必须把当前用户传进去并应用 `scope_predicate`。**

> **现状（已实测）**：本目录目前**只有一个 `__init__.py` 占位**，无任何模块导入它。真实的 AI 代码不在
> 这里，而在 `app/api/v1/endpoints/ai.py`（`GET /ai/copilot/quote-summary`）、
> `app/domains/quote/application/industrial_copilot.py` 与 `app/models/ai.py`
> （`ai_documents` / `ai_embeddings` / `embedding_tasks`）。下面的布局是**建议**，不是现状。
>
> 下方第 5 条"AI 不得绕过 repository、须遵守 RBAC 与租户边界"曾被实测出**两处未做到**并已修复：copilot
> 摘要与报价流转此前都未应用数据范围（`repo.get_quote` 提供了 `predicate` 接缝，另外三处调用都传了，
> 这两处漏了）。**任何新增的 AI 入口都必须把当前用户传进去并应用 `scope_predicate`。**

This ERP/MES backend is structured so AI features can be added without rewriting core modules:

- **Configuration**: add provider keys to `app.config.settings` (never commit secrets).
- **Services**: implement orchestration in `app/services/` and keep HTTP thin in `app/api/`.
- **Observability**: prefer structured logs + trace IDs on AI calls (to be added with OpenTelemetry).
- **Data access**: AI should not bypass repositories; respect RBAC and tenant boundaries.

Suggested future layout:

- `app/integrations/ai/providers/` vendor clients
- `app/integrations/ai/prompts/` versioned prompt templates
- `app/integrations/ai/tools/` safe tool-calling surfaces (MES/ERP read APIs)
