"""ORM models (import order matters for mapper configuration)."""

from app.models.accounting_entry import AccountingEntry
from app.models.accounting_entry_line import AccountingEntryLine
from app.models.customer_ledger_account import CustomerLedgerAccount
from app.models.supplier_ledger_account import SupplierLedgerAccount
from app.models.associations import role_permission_association, user_role_association
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.cost_estimate import (
    CostEstimate,
    CostEstimateMachineLine,
    CostEstimateMaterialLine,
    CostEstimateProcessLine,
)
from app.models.customer import Customer, CustomerContact, CustomerFollowup
from app.models.department import Department
from app.models.domain_event import DomainEvent
from app.models.file_center import FileLifecyclePolicy, FileObject, FilePreviewCache, FileRelation
from app.models.material import Material
from app.models.material_category import MaterialCategory
from app.models.supplier import Supplier
from app.models.unit import Unit
from app.models.equipment_unit import EquipmentUnit
from app.models.installation_plan import InstallationPlan
from app.models.machine import (
    Machine,
    MachineBom,
    MachineBomItem,
    MachineCategory,
    MachineImage,
    MachineParameter,
)
from app.models.permission import Permission
from app.models.fieldwork_record import FieldworkRecord
from app.models.procurement_entry import ProcurementEntry
from app.models.procurement_payable_request import ProcurementPayableRequest
from app.models.product import (
    Product,
    ProductCategory,
    ProductCostTemplate,
    ProductCostTemplateLine,
    ProductPriceTemplate,
    ProductPriceTemplateLine,
)
from app.models.project import Project
from app.models.project_actual_cost import ProjectActualCost
from app.models.acceptance import AcceptanceRecord, AcceptanceTemplate, PunchListItem
from app.models.option_group import OptionGroup, OptionItem
from app.models.quote import Quote, QuoteApproval, QuoteItem, QuoteVersion
from app.models.quote_receivable_request import QuoteReceivableRequest
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
from app.models.work_order import WorkOrder
from app.models.workflow import WorkflowState, WorkflowTransition

__all__ = [
    "Base",
    "Department",
    "AuditLog",
    "WorkOrder",
    "WorkflowState",
    "WorkflowTransition",
    "DomainEvent",
    "SystemConfig",
    "FileObject",
    "FileRelation",
    "FilePreviewCache",
    "FileLifecyclePolicy",
    "FieldworkRecord",
    "InstallationPlan",
    "ProcurementEntry",
    "ProcurementPayableRequest",
    "ProductCategory",
    "Product",
    "ProductCostTemplate",
    "ProductCostTemplateLine",
    "ProductPriceTemplate",
    "ProductPriceTemplateLine",
    "Project",
    "ProjectActualCost",
    "PunchListItem",
    "Quote",
    "QuoteVersion",
    "QuoteItem",
    "QuoteApproval",
    "ApprovalTemplate",
    "ApprovalNode",
    "ApprovalRecord",
    "QuoteExportTask",
    "QuoteReceivableRequest",
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
    "CostEstimate",
    "CostEstimateMaterialLine",
    "CostEstimateMachineLine",
    "CostEstimateProcessLine",
    "AccountingEntry",
    "AccountingEntryLine",
    "AccountingSettlement",
    "CustomerLedgerAccount",
    "Customer",
    "CustomerContact",
    "CustomerFollowup",
    "Material",
    "MaterialCategory",
    "Supplier",
    "Unit",
    "AcceptanceRecord",
    "AcceptanceTemplate",
    "EquipmentUnit",
    "OptionGroup",
    "OptionItem",
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
