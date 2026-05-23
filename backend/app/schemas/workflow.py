from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkflowStateCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    is_start: bool = False
    is_end: bool = False
    description: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "entity_type": "machine_bom",
                "code": "draft",
                "name": "草稿",
                "is_start": True,
                "is_end": False,
                "description": "初始状态",
            }
        }
    }


class WorkflowStateRead(WorkflowStateCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class WorkflowTransitionCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=64)
    from_state_id: UUID
    to_state_id: UUID
    action_code: str = Field(min_length=1, max_length=64)
    action_name: str = Field(min_length=1, max_length=120)
    description: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "entity_type": "machine_bom",
                "from_state_id": "11111111-1111-1111-1111-111111111111",
                "to_state_id": "22222222-2222-2222-2222-222222222222",
                "action_code": "submit",
                "action_name": "提交审核",
                "description": "草稿转待审",
            }
        }
    }


class WorkflowTransitionRead(WorkflowTransitionCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


class WorkflowActionPayload(BaseModel):
    action_code: str = Field(min_length=1, max_length=64)
