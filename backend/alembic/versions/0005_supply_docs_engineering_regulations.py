"""
Solar Operations OS — Alembic Migration 0005: Supply, Documents, Engineering, Regulations schemas
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "0005_supply_docs_engineering_regulations"
down_revision = "0004_engineering_and_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Engineering ───────────────────────────────────────────────────────────
    op.create_table(
        "design",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("design_version", sa.Integer(), nullable=False, default=1),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("system_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="draft"),
        sa.Column("capacity_kw_dc", sa.Numeric(10, 2), nullable=False),
        sa.Column("capacity_kw_ac", sa.Numeric(10, 2), nullable=False),
        sa.Column("panel_make", sa.String(100), nullable=False),
        sa.Column("panel_model", sa.String(100), nullable=False),
        sa.Column("panel_wattage", sa.Numeric(6, 1), nullable=False),
        sa.Column("panel_count", sa.Integer(), nullable=False),
        sa.Column("inverter_make", sa.String(100), nullable=False),
        sa.Column("inverter_model", sa.String(100), nullable=False),
        sa.Column("inverter_count", sa.Integer(), nullable=False),
        sa.Column("tilt_degrees", sa.Numeric(5, 2), nullable=False, default=15.0),
        sa.Column("azimuth_degrees", sa.Numeric(5, 2), nullable=False, default=180.0),
        sa.Column("expected_annual_generation_kwh", sa.Numeric(12, 2), nullable=True),
        sa.Column("performance_ratio_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("approved_by_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("organization_id", "project_id", "design_version", name="uq_design_project_ver"),
    )
    op.create_index("ix_design_project", "design", ["project_id"])
    op.create_index("ix_design_org", "design", ["organization_id"])

    op.create_table(
        "string_configuration",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("design_id", UUID(as_uuid=True), sa.ForeignKey("design.id", ondelete="CASCADE"), nullable=False),
        sa.Column("string_number", sa.Integer(), nullable=False),
        sa.Column("inverter_index", sa.Integer(), nullable=False, default=1),
        sa.Column("mppt_tracker_index", sa.Integer(), nullable=False, default=1),
        sa.Column("panels_count", sa.Integer(), nullable=False),
        sa.Column("vmp_volts", sa.Numeric(6, 2), nullable=True),
        sa.Column("voc_volts", sa.Numeric(6, 2), nullable=True),
        sa.Column("imp_amps", sa.Numeric(6, 2), nullable=True),
        sa.Column("isc_amps", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("design_id", "string_number", name="uq_string_config_num"),
    )

    op.create_table(
        "bom",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("design_id", UUID(as_uuid=True), sa.ForeignKey("design.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bom_version", sa.Integer(), nullable=False, default=1),
        sa.Column("status", sa.String(50), nullable=False, default="draft"),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_by_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "project_id", "bom_version", name="uq_bom_project_ver"),
    )

    op.create_table(
        "bom_item",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("bom_id", UUID(as_uuid=True), sa.ForeignKey("bom.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("item_code", sa.String(100), nullable=True),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("specifications", JSONB(), nullable=False, server_default="{}"),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit_of_measure", sa.String(20), nullable=False, default="NOS"),
        sa.Column("is_serialized", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_bom_item_bom", "bom_item", ["bom_id"])

    # ── Supply Chain ──────────────────────────────────────────────────────────
    op.create_table(
        "supplier",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("gstin", sa.String(20), nullable=True),
        sa.Column("pan", sa.String(15), nullable=True),
        sa.Column("contact_name", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address", JSONB(), nullable=False, server_default="{}"),
        sa.Column("state_code", sa.String(10), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "code", name="uq_supplier_org_code"),
    )
    op.create_index("ix_supplier_name", "supplier", ["organization_id", "name"])

    op.create_table(
        "warehouse",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("address", JSONB(), nullable=False, server_default="{}"),
        sa.Column("state_code", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "code", name="uq_warehouse_org_code"),
    )

    op.create_table(
        "purchase_order",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("po_number", sa.String(50), nullable=False),
        sa.Column("supplier_id", UUID(as_uuid=True), sa.ForeignKey("supplier.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="draft"),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_delivery_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, default="INR"),
        sa.Column("subtotal_amount", sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "po_number", name="uq_po_org_num"),
    )
    op.create_index("ix_po_supplier", "purchase_order", ["organization_id", "supplier_id"])

    op.create_table(
        "po_line",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("purchase_order_id", UUID(as_uuid=True), sa.ForeignKey("purchase_order.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bom_item_id", UUID(as_uuid=True), sa.ForeignKey("bom_item.id", ondelete="SET NULL"), nullable=True),
        sa.Column("item_description", sa.String(255), nullable=False),
        sa.Column("ordered_quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("received_quantity", sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column("unit_of_measure", sa.String(20), nullable=False, default="NOS"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_rate_percent", sa.Numeric(5, 2), nullable=False, default=18.0),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_po_line_po", "po_line", ["purchase_order_id"])

    op.create_table(
        "shipment",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("purchase_order_id", UUID(as_uuid=True), sa.ForeignKey("purchase_order.id", ondelete="CASCADE"), nullable=False),
        sa.Column("destination_warehouse_id", UUID(as_uuid=True), sa.ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tracking_number", sa.String(100), nullable=True),
        sa.Column("transporter_name", sa.String(100), nullable=True),
        sa.Column("lr_number", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="dispatched"),
        sa.Column("dispatch_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_shipment_po", "shipment", ["purchase_order_id"])
    op.create_index("ix_shipment_status", "shipment", ["organization_id", "status"])

    op.create_table(
        "shipment_line",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("shipment_id", UUID(as_uuid=True), sa.ForeignKey("shipment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("po_line_id", UUID(as_uuid=True), sa.ForeignKey("po_line.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dispatched_quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("accepted_quantity", sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column("rejected_quantity", sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_shipment_line_shipment", "shipment_line", ["shipment_id"])

    op.create_table(
        "stock_movement",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("asset.id", ondelete="SET NULL"), nullable=True),
        sa.Column("movement_type", sa.String(50), nullable=False),
        sa.Column("from_warehouse_id", UUID(as_uuid=True), sa.ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True),
        sa.Column("to_warehouse_id", UUID(as_uuid=True), sa.ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True),
        sa.Column("to_project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False, default=1),
        sa.Column("movement_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stock_movement_asset", "stock_movement", ["asset_id"])
    op.create_index("ix_stock_movement_to_proj", "stock_movement", ["to_project_id"])

    # ── Documents ─────────────────────────────────────────────────────────────
    op.create_table(
        "document_type",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, default="other"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_mandatory_for_commissioning", sa.Boolean(), nullable=False, default=False),
        sa.Column("validity_period_months", sa.Integer(), nullable=True),
        sa.Column("allowed_mime_types", ARRAY(sa.String(50)), nullable=False),
        sa.Column("max_file_size_mb", sa.Integer(), nullable=False, default=25),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "code", name="uq_doc_type_org_code"),
    )
    op.create_index("ix_doc_type_category", "document_type", ["organization_id", "category"])

    op.create_table(
        "document",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("document_type_id", UUID(as_uuid=True), sa.ForeignKey("document_type.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=True),
        sa.Column("plant_id", sa.String(50), nullable=True),
        sa.Column("site_id", UUID(as_uuid=True), sa.ForeignKey("site.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="pending_verification"),
        sa.Column("current_version_num", sa.Integer(), nullable=False, default=1),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_document_project", "document", ["organization_id", "project_id"])
    op.create_index("ix_document_plant", "document", ["organization_id", "plant_id"])
    op.create_index("ix_document_status", "document", ["organization_id", "status"])

    op.create_table(
        "document_version",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("document.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_num", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("uploaded_by_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("document_id", "version_num", name="uq_doc_version_num"),
    )
    op.create_index("ix_doc_ver_sha256", "document_version", ["organization_id", "sha256_hash"])

    op.create_table(
        "document_verification",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", UUID(as_uuid=True), sa.ForeignKey("document_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("verifier_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("extracted_fields", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_doc_verif_version", "document_verification", ["version_id"])

    op.create_table(
        "certificate",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("certificate_type", sa.String(100), nullable=False),
        sa.Column("certificate_number", sa.String(100), nullable=False),
        sa.Column("issuing_authority", sa.String(255), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_cert_project", "certificate", ["organization_id", "project_id"])
    op.create_index("ix_cert_plant", "certificate", ["organization_id", "plant_id"])

    # ── Regulations ───────────────────────────────────────────────────────────
    op.create_table(
        "authority",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("level", sa.String(50), nullable=False, default="state"),
        sa.Column("state_code", sa.String(10), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "code", name="uq_authority_org_code"),
    )

    op.create_table(
        "regulation",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("authority_id", UUID(as_uuid=True), sa.ForeignKey("authority.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("applies_to_states", ARRAY(sa.String(10)), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "code", name="uq_regulation_org_code"),
    )
    op.create_index("ix_regulation_authority", "regulation", ["organization_id", "authority_id"])

    op.create_table(
        "rule",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("regulation_id", UUID(as_uuid=True), sa.ForeignKey("regulation.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="active"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("condition_dsl", JSONB(), nullable=False, server_default="{}"),
        sa.Column("action_meta", JSONB(), nullable=False, server_default="{}"),
        sa.Column("min_capacity_kw", sa.String(20), nullable=True),
        sa.Column("max_capacity_kw", sa.String(20), nullable=True),
        sa.Column("applies_to_system_types", ARRAY(sa.String(30)), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("regulation_id", "code", name="uq_rule_reg_code"),
    )
    op.create_index("ix_rule_type", "rule", ["organization_id", "rule_type"])

    op.create_table(
        "rule_set",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("state_code", sa.String(10), nullable=True),
        sa.Column("system_type", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rule_ids", ARRAY(sa.String(36)), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "code", name="uq_ruleset_org_code"),
    )


def downgrade() -> None:
    op.drop_table("rule_set")
    op.drop_table("rule")
    op.drop_table("regulation")
    op.drop_table("authority")
    op.drop_table("certificate")
    op.drop_table("document_verification")
    op.drop_table("document_version")
    op.drop_table("document")
    op.drop_table("document_type")
    op.drop_table("stock_movement")
    op.drop_table("shipment_line")
    op.drop_table("shipment")
    op.drop_table("po_line")
    op.drop_table("purchase_order")
    op.drop_table("warehouse")
    op.drop_table("supplier")
    op.drop_table("bom_item")
    op.drop_table("bom")
    op.drop_table("string_configuration")
    op.drop_table("design")
