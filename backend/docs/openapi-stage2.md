# Stage 2 OpenAPI 文档（基础数据中心）

FastAPI 自动生成文档：

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

以下是阶段二新增模块（均为 JWT + RBAC 保护）：

## 客户系统 `/api/v1/customers`

- `POST /customers` 新增客户
- `GET /customers?page=1&page_size=20&q=关键词` 客户分页/搜索
- `PUT /customers/{customer_id}` 更新客户
- `DELETE /customers/{customer_id}` 软删除客户

联系人：

- `POST /customers/contacts`
- `GET /customers/contacts?page=1&page_size=20&q=关键词`
- `PUT /customers/contacts/{contact_id}`
- `DELETE /customers/contacts/{contact_id}`

跟进记录：

- `POST /customers/followups`
- `GET /customers/followups?page=1&page_size=20&q=关键词`
- `PUT /customers/followups/{followup_id}`
- `DELETE /customers/followups/{followup_id}`

## 设备标准库 `/api/v1/machines`

设备分类：

- `POST /machines/categories`
- `GET /machines/categories?page=1&page_size=20&q=关键词`
- `PUT /machines/categories/{category_id}`
- `DELETE /machines/categories/{category_id}`

设备主数据：

- `POST /machines`
- `GET /machines?page=1&page_size=20&q=关键词`
- `PUT /machines/{machine_id}`
- `DELETE /machines/{machine_id}`

设备参数：

- `POST /machines/parameters`
- `GET /machines/parameters?page=1&page_size=20&q=关键词`
- `PUT /machines/parameters/{parameter_id}`
- `DELETE /machines/parameters/{parameter_id}`

设备图片：

- `POST /machines/images`
- `GET /machines/images?page=1&page_size=20&q=关键词`
- `PUT /machines/images/{image_id}`
- `DELETE /machines/images/{image_id}`

## BOM 系统 `/api/v1/boms`

BOM 主表：

- `POST /boms`
- `GET /boms?page=1&page_size=20&q=关键词`
- `PUT /boms/{bom_id}`
- `DELETE /boms/{bom_id}`

BOM 明细：

- `POST /boms/items`
- `GET /boms/items?page=1&page_size=20&q=关键词`
- `PUT /boms/items/{item_id}`
- `DELETE /boms/items/{item_id}`

## 统一规则

- 分页参数：`page`、`page_size`
- 搜索参数：`q`
- 删除策略：统一软删除（`is_deleted=true`）
- 审计字段：`created_at`、`updated_at`、`created_by`、`is_deleted`

## 阶段二增强接口

- `POST /api/v1/boms/items/batch`：BOM明细批量新增（事务）
- `POST /api/v1/boms/batch-delete`：BOM批量软删除（事务）
- `POST /api/v1/boms/{bom_id}/actions/transition`：BOM状态流动作
- `POST /api/v1/workflows/states`：创建状态
- `GET /api/v1/workflows/states?page=1&page_size=20&q=xxx&entity_type=machine_bom`
- `POST /api/v1/workflows/transitions`：创建迁移动作
- `GET /api/v1/workflows/transitions?page=1&page_size=20&q=xxx&entity_type=machine_bom`

业务规则说明：

- 设备编码 `machine_code` 由服务层按规则自动生成：`{code前缀}-{yyyymmdd}-{序号}`。
- BOM版本在同一设备下唯一；冲突返回标准异常：`{"code":"UNIQUE_VIOLATION","message":"..."}`。
- BOM明细变更后自动重算 `line_total` 与 `machine_boms.total_cost`。
- 关键操作会写入 `audit_logs`。
