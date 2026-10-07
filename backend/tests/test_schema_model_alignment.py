"""Schemas and models must agree about columns, in both directions.

Round 108 measured 160 schema classes paired with a model and found the two directions very different in size.
Every schema field that is not a column turned out to be **derived, an input, or a nested collection** — enum
labels, joined names, computed amounts, `machine_lines`, `UserCreate.password` — and every model column absent
from its Read schema is either a parent foreign key already implied by nesting, the internal `is_deleted`, or one
of three worth naming.

The measurement needed two corrections worth keeping in mind, because both produced large believable numbers:

* **`relationship()` is not a column.** The first version counted relationship attributes as model fields and
  reported "164 model fields missing from the Read schema" — all of them relationships, which a Read schema
  legitimately replaces with the foreign key. Only `mapped_column` counts.
* **The pairing is by name.** `XRead` pairs with `X`; the eighty schema classes that pair with nothing are
  request payloads, list wrappers and detail projections, and the test says nothing about them.

The test asserts both directions, with the exceptions listed rather than hidden, so that a schema field with no
column and no listed reason — a typo, a field somebody meant to add to the model — fails here.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODELS = REPO / "backend" / "app" / "models"
SCHEMAS = REPO / "backend" / "app" / "schemas"
SUFFIXES = ("Read", "Create", "Update", "Base", "List", "Response")

# Controls: if these are not extracted, the parse is broken and every verdict below is meaningless.
CONTROL_COLUMNS = (("Customer", "code"), ("User", "username"), ("WorkOrder", "work_order_no"))
CONTROL_SCHEMA_FIELDS = (("UserCreate", "password"), ("RoleRead", "permission_codes"))

# Schema fields that are derived, inputs or nested collections rather than columns. Each is a decision somebody
# made; the list exists so that a *new* one has to be looked at.
DERIVED_OR_INPUT_FIELDS = {
    ("AcceptanceRecordRead", "punch_items"),
    ("AccountingEntryRead", "lines"),
    ("AfterSalesServiceRequestRead", "assignee_name"),
    ("AfterSalesServiceRequestRead", "customer_name"),
    ("AfterSalesServiceRequestRead", "equipment_serial"),
    ("CostEstimateCreate", "machine_lines"),
    ("CostEstimateCreate", "material_lines"),
    ("CostEstimateCreate", "process_lines"),
    ("CostEstimateRead", "machine_lines"),
    ("CostEstimateRead", "material_lines"),
    ("CostEstimateRead", "process_lines"),
    ("CostEstimateUpdate", "machine_lines"),
    ("CostEstimateUpdate", "material_lines"),
    ("CostEstimateUpdate", "process_lines"),
    ("FieldworkRecordRead", "record_type_label"),
    ("FieldworkRecordRead", "service_request_title"),
    ("FieldworkRecordRead", "status_label"),
    ("FieldworkRecordRead", "urgency_label"),
    ("OptionGroupRead", "items"),
    ("ProcurementEntryRead", "plan_amount"),
    ("ProductCostTemplateCreate", "lines"),
    ("ProductCostTemplateRead", "lines"),
    ("ProductCostTemplateUpdate", "lines"),
    ("ProductPriceTemplateCreate", "lines"),
    ("ProductPriceTemplateRead", "lines"),
    ("ProductPriceTemplateUpdate", "lines"),
    ("QuoteVersionCreate", "items"),
    ("RoleRead", "permission_codes"),
    ("UserCreate", "password"),
    ("UserCreate", "role_codes"),
    ("WorkOrderRead", "process_node_label"),
    ("WorkOrderRead", "status_label"),
}

# Model columns deliberately absent from the matching Read schema. Nesting covers the parent keys; `is_deleted` is
# internal; the rest are named in the round 108 record.
COLUMNS_NOT_IN_THE_READ_SCHEMA = {
    "AcceptanceRecord": ["created_by", "is_deleted", "updated_at"],
    "AcceptanceTemplate": ["created_by", "is_deleted", "updated_at"],
    "AccountingEntry": ["is_deleted"],
    "AccountingEntryLine": ["created_at", "created_by", "entry_id", "is_deleted", "updated_at"],
    "AfterSalesServiceRequest": ["is_deleted"],
    "ApprovalNode": ["created_at", "created_by", "dynamic_approver_expr", "is_deleted", "updated_at"],
    "CostEstimateMachineLine": ["cost_estimate_id", "is_deleted"],
    "CostEstimateMaterialLine": ["cost_estimate_id", "is_deleted"],
    "CostEstimateProcessLine": ["cost_estimate_id", "is_deleted"],
    "Department": ["created_at", "updated_at"],
    "EquipmentUnit": ["created_by", "is_deleted"],
    "InstallationPlan": ["created_by", "is_deleted", "updated_at"],
    "Notification": ["created_by", "is_deleted", "provider_id"],
    "OptionGroup": ["created_at", "created_by", "is_deleted", "updated_at"],
    "OptionItem": ["created_at", "created_by", "is_deleted", "updated_at"],
    "Permission": ["created_at", "updated_at"],
    "ProcurementPayableRequest": ["created_by", "is_deleted"],
    "ProductCostTemplateLine": ["created_at", "updated_at"],
    "ProductPriceTemplateLine": ["created_at", "updated_at"],
    "PunchListItem": ["created_by", "is_deleted", "updated_at"],
    "QuoteApproval": ["created_by", "is_deleted", "updated_at"],
    "QuoteItem": ["created_at", "created_by", "is_deleted", "updated_at"],
    "QuoteReceivableRequest": ["created_by", "is_deleted"],
    "Role": ["created_at", "updated_at"],
    "Tenant": ["created_at", "created_by", "is_deleted", "updated_at"],
}


def _class_fields(path: Path) -> dict[str, tuple[list[str], list[str]]]:
    """class name -> (own column names, base names). `relationship()` attributes are excluded: not columns."""
    result: dict[str, tuple[list[str], list[str]]] = {}
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.ClassDef):
            continue
        fields = []
        for statement in node.body:
            if not isinstance(statement, ast.AnnAssign) or not isinstance(statement.target, ast.Name):
                continue
            value = statement.value
            if isinstance(value, ast.Call):
                called = value.func
                name = called.id if isinstance(called, ast.Name) else (called.attr if isinstance(called, ast.Attribute) else "")
                if name == "relationship":
                    continue
            fields.append(statement.target.id)
        bases = [
            base.id if isinstance(base, ast.Name) else (base.attr if isinstance(base, ast.Attribute) else "")
            for base in node.bases
        ]
        result[node.name] = (fields, [base for base in bases if base])
    return result


def _gather(root: Path) -> dict[str, set[str]]:
    """Resolve every class to its full field set, following bases — the mixins in `app/models/base.py` are
    classes like any other, so models pick up `id`, `created_at`, `updated_at`, `created_by` and `is_deleted`
    through the same walk that lets `XRead` pick up `XBase`."""
    raw: dict[str, tuple[list[str], list[str]]] = {}
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        raw.update(_class_fields(path))

    resolved: dict[str, set[str]] = {}

    def walk(name: str, seen: set[str]) -> set[str]:
        if name in seen or name not in raw:
            return set()
        seen.add(name)
        own, bases = raw[name]
        fields = set(own)
        for base in bases:
            fields |= walk(base, seen)
        return fields

    for name in raw:
        resolved[name] = walk(name, set())
    return resolved


def test_the_extraction_finds_known_fields_and_columns():
    models = _gather(MODELS)
    schemas = _gather(SCHEMAS)
    for class_name, field in CONTROL_COLUMNS:
        assert class_name in models and field in models[class_name], (
            f"control column {class_name}.{field} was not extracted, so the model parse is broken"
        )
    for class_name, field in CONTROL_SCHEMA_FIELDS:
        assert class_name in schemas and field in schemas[class_name], (
            f"control schema field {class_name}.{field} was not extracted, so the schema parse is broken"
        )


def test_every_schema_field_is_a_column_or_a_recorded_exception():
    models = _gather(MODELS)
    schemas = _gather(SCHEMAS)
    model_names = {name for name in models if not name.endswith("Mixin")}

    unrecorded = []
    for name in sorted(schemas):
        model_name = next(
            (name[: -len(suffix)] for suffix in SUFFIXES if name.endswith(suffix) and name[: -len(suffix)] in model_names),
            None,
        )
        if model_name is None:
            continue
        for field in schemas[name] - models[model_name]:
            if (name, field) not in DERIVED_OR_INPUT_FIELDS:
                unrecorded.append(f"{name}.{field} (model {model_name})")

    assert unrecorded == [], (
        "these schema fields are neither a column on the matching model nor a recorded derived or input field, "
        "so the API would serialise something the database cannot supply:\n"
        + "\n".join(f"    {entry}" for entry in unrecorded)
    )


def test_every_model_column_is_either_exposed_or_recorded():
    models = _gather(MODELS)
    schemas = _gather(SCHEMAS)

    # Round 234: this used to iterate `COLUMNS_NOT_IN_THE_READ_SCHEMA` itself, so **a column added to a model not listed
    # there was invisible** — planting one on `Unit` passed the whole file in round 233. Measured: **58 models have a
    # matching `XRead` schema and only 25 were covered, while none of the other 33 currently omits a column.** The dict is
    # therefore a list of recorded exceptions rather than the scope, and the loop is over the models.
    unrecorded = []
    for model_name in sorted(models):
        if model_name.endswith("Mixin"):
            continue
        read_name = f"{model_name}Read"
        if read_name not in schemas:
            # A model with no Read schema reaches no client at all; whether it should have one is a different question,
            # and `test_model_schema_parity` owns the model-versus-database side.
            continue
        recorded = COLUMNS_NOT_IN_THE_READ_SCHEMA.get(model_name, ())
        for field in sorted(models[model_name] - schemas[read_name]):
            if field not in recorded:
                unrecorded.append(f"{model_name}.{field} is in no Read schema and in no recorded list")

    assert unrecorded == [], (
        "these model columns reach no client and are not recorded as deliberate:\n"
        + "\n".join(f"    {entry}" for entry in unrecorded)
    )
