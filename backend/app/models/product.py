from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.machine import Machine, MachineBom
    from app.models.user import User


class ProductCategory(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "product_categories"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[ProductCategory | None] = relationship(
        remote_side="ProductCategory.id",
        foreign_keys=[parent_id],
        back_populates="children",
    )
    children: Mapped[list[ProductCategory]] = relationship(back_populates="parent")
    products: Mapped[list[Product]] = relationship(back_populates="category")
    creator: Mapped[User | None] = relationship(foreign_keys="ProductCategory.created_by", lazy="joined")


class Product(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "products"

    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    spec: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    power: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="EA", server_default="EA")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    reference_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    reference_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    machine_id: Mapped[UUID | None] = mapped_column(ForeignKey("machines.id", ondelete="SET NULL"), nullable=True, index=True)
    default_bom_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("machine_boms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    default_cost_template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_cost_templates.id", ondelete="SET NULL", use_alter=True, name="fk_products_default_cost_template"),
        nullable=True,
        index=True,
    )
    default_price_template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_price_templates.id", ondelete="SET NULL", use_alter=True, name="fk_products_default_price_template"),
        nullable=True,
        index=True,
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[ProductCategory | None] = relationship(back_populates="products")
    machine: Mapped[Machine | None] = relationship()
    default_bom: Mapped[MachineBom | None] = relationship()
    creator: Mapped[User | None] = relationship(foreign_keys="Product.created_by", lazy="joined")


class ProductCostTemplate(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "product_cost_templates"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    scrap_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")
    overhead_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped[Product | None] = relationship(foreign_keys=[product_id])
    lines: Mapped[list[ProductCostTemplateLine]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="ProductCostTemplateLine.sort_order",
    )
    creator: Mapped[User | None] = relationship(foreign_keys="ProductCostTemplate.created_by", lazy="joined")


class ProductCostTemplateLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_cost_template_lines"

    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_cost_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_type: Mapped[str] = mapped_column(String(32), nullable=False, default="material", server_default="material")
    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="EA", server_default="EA")
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=1, server_default="1")
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    template: Mapped[ProductCostTemplate] = relationship(back_populates="lines")


class ProductPriceTemplate(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "product_price_templates"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    cost_template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("product_cost_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    margin_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0.2, server_default="0.2")
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped[Product | None] = relationship(foreign_keys=[product_id])
    cost_template: Mapped[ProductCostTemplate | None] = relationship()
    lines: Mapped[list[ProductPriceTemplateLine]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="ProductPriceTemplateLine.sort_order",
    )
    creator: Mapped[User | None] = relationship(foreign_keys="ProductPriceTemplate.created_by", lazy="joined")


class ProductPriceTemplateLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_price_template_lines"

    template_id: Mapped[UUID] = mapped_column(
        ForeignKey("product_price_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="EA", server_default="EA")
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=1, server_default="1")
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    template: Mapped[ProductPriceTemplate] = relationship(back_populates="lines")
