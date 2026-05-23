## AI extension hooks (planned)

This ERP/MES backend is structured so AI features can be added without rewriting core modules:

- **Configuration**: add provider keys to `app.config.settings` (never commit secrets).
- **Services**: implement orchestration in `app/services/` and keep HTTP thin in `app/api/`.
- **Observability**: prefer structured logs + trace IDs on AI calls (to be added with OpenTelemetry).
- **Data access**: AI should not bypass repositories; respect RBAC and tenant boundaries.

Suggested future layout:

- `app/integrations/ai/providers/` vendor clients
- `app/integrations/ai/prompts/` versioned prompt templates
- `app/integrations/ai/tools/` safe tool-calling surfaces (MES/ERP read APIs)
