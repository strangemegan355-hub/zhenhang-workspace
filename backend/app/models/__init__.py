"""ORM models (import order matters for mapper configuration)."""

from app.models.associations import role_permission_association, user_role_association
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.customer import Customer, CustomerContact, CustomerFollowup
from app.models.department import Department
from app.models.domain_event import DomainEvent
from app.models.file_center import FileLifecyclePolicy, FileObject, FilePreviewCache, FileRelation
from app.models.machine import (
    Machine,
    MachineBom,
    MachineBomItem,
    MachineCategory,
    MachineImage,
    MachineParameter,
)
from app.models.permission import Permission
from app.models.quote import Quote, QuoteApproval, QuoteItem, QuoteVersion
from app.models.quote import ApprovalNode, ApprovalRecord, ApprovalTemplate, QuoteExportTask
from app.models.quote_template import QuoteExcelTemplate, QuotePDFTemplate
from app.models.role import Role
from app.models.notification import Notification, NotificationProvider
from app.models.realtime_event import RealtimeEvent
from app.models.realtime_event_archive import RealtimeEventArchive
from app.models.tenant import Tenant
from app.models.mes import MesEquipmentSignal, MesOeeSnapshot
from app.models.ai import AIContext, AIDocument, AIEmbedding, EmbeddingTask
from app.models.tasking import JobExecution, TaskQueue
from app.models.system_config import SystemConfig
from app.models.user import User
from app.models.workflow import WorkflowState, WorkflowTransition

__all__ = [
    "Base",
    "Department",
    "AuditLog",
    "WorkflowState",
    "WorkflowTransition",
    "DomainEvent",
    "SystemConfig",
    "FileObject",
    "FileRelation",
    "FilePreviewCache",
    "FileLifecyclePolicy",
    "Quote",
    "QuoteVersion",
    "QuoteItem",
    "QuoteApproval",
    "ApprovalTemplate",
    "ApprovalNode",
    "ApprovalRecord",
    "QuoteExportTask",
    "QuotePDFTemplate",
    "QuoteExcelTemplate",
    "NotificationProvider",
    "Notification",
    "RealtimeEvent",
    "RealtimeEventArchive",
    "Tenant",
    "MesEquipmentSignal",
    "MesOeeSnapshot",
    "TaskQueue",
    "JobExecution",
    "AIContext",
    "AIDocument",
    "AIEmbedding",
    "EmbeddingTask",
    "Customer",
    "CustomerContact",
    "CustomerFollowup",
    "MachineCategory",
    "Machine",
    "MachineParameter",
    "MachineImage",
    "MachineBom",
    "MachineBomItem",
    "Permission",
    "Role",
    "User",
    "role_permission_association",
    "user_role_association",
]
