"""
Solar Operations OS — Alembic Migration 0006: Compliance, Reconciliation, Field, Warranty, OAM, Telemetry
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "0006_compliance_field_warranty_oam_telemetry"
down_revision = "0005_supply_docs_engineering_regulations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Compliance ────────────────────────────────────────────────────────────
    op.create_table(
        "compliance_run",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_set_id", UUID(as_uuid=True), nullable=True),
        sa.Column("triggered_by_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("triggered_by_event", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_rules", sa.Integer(), nullable=False, default=0),
        sa.Column("passed", sa.Integer(), nullable=False, default=0),
        sa.Column("failed", sa.Integer(), nullable=False, default=0),
        sa.Column("warned", sa.Integer(), nullable=False, default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("context_snapshot", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_compliance_run_project", "compliance_run", ["organization_id", "project_id"])
    op.create_index("ix_compliance_run_status", "compliance_run", ["organization_id", "status"])

    op.create_table(
        "compliance_result",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("compliance_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_id", UUID(as_uuid=True), nullable=True),
        sa.Column("rule_code", sa.String(100), nullable=False),
        sa.Column("rule_title", sa.String(512), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="pass"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("evidence", JSONB(), nullable=False, server_default="{}"),
        sa.Column("waiver_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_compliance_result_run", "compliance_result", ["run_id"])

    op.create_table(
        "compliance_waiver",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_code", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("granted_by_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_waiver_project_rule", "compliance_waiver", ["project_id", "rule_code"])

    # ── Reconciliation ────────────────────────────────────────────────────────
    op.create_table(
        "reconciliation_run",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        sa.Column("triggered_by_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("triggered_by_event", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=False, default=0),
        sa.Column("matched", sa.Integer(), nullable=False, default=0),
        sa.Column("mismatched", sa.Integer(), nullable=False, default=0),
        sa.Column("summary", JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_recon_run_project", "reconciliation_run", ["organization_id", "project_id"])

    op.create_table(
        "reconciliation_comparison",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("reconciliation_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_key", sa.String(255), nullable=False),
        sa.Column("item_type", sa.String(100), nullable=False),
        sa.Column("result", sa.String(50), nullable=False, default="match"),
        sa.Column("planned_value", JSONB(), nullable=True),
        sa.Column("actual_value", JSONB(), nullable=True),
        sa.Column("delta", JSONB(), nullable=True),
        sa.Column("mismatch_reason", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_recon_comparison_run", "reconciliation_comparison", ["run_id"])

    op.create_table(
        "source_snapshot",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("reconciliation_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(100), nullable=False),
        sa.Column("snapshot_data", JSONB(), nullable=False, server_default="{}"),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Field ─────────────────────────────────────────────────────────────────
    op.create_table(
        "meter",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("meter_type", sa.String(50), nullable=False),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=False),
        sa.Column("meter_number", sa.String(100), nullable=True),
        sa.Column("discom_asset_id", sa.String(100), nullable=True),
        sa.Column("capacity_kw", sa.Numeric(10, 2), nullable=True),
        sa.Column("installed_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "serial_number", name="uq_meter_serial"),
    )
    op.create_index("ix_meter_project", "meter", ["organization_id", "project_id"])

    op.create_table(
        "inspection_template",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("checklist", JSONB(), nullable=False, server_default="[]"),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "code", name="uq_insp_template_code"),
    )

    op.create_table(
        "inspection",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("inspection_template.id", ondelete="SET NULL"), nullable=True),
        sa.Column("inspector_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("conducted_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="scheduled"),
        sa.Column("score_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("overall_result", sa.String(20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("geo_location", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inspection_project", "inspection", ["organization_id", "project_id"])

    op.create_table(
        "inspection_item",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("inspection_id", UUID(as_uuid=True), sa.ForeignKey("inspection.id", ondelete="CASCADE"), nullable=False),
        sa.Column("check_code", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("result", sa.String(50), nullable=True),
        sa.Column("numeric_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("text_value", sa.Text(), nullable=True),
        sa.Column("photo_storage_key", sa.String(512), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_insp_item_inspection", "inspection_item", ["inspection_id"])

    op.create_table(
        "wcr",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("wcr_number", sa.String(100), nullable=False),
        sa.Column("wcr_version", sa.Integer(), nullable=False, default=1),
        sa.Column("status", sa.String(50), nullable=False, default="draft"),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("capacity_installed_kw", sa.Numeric(10, 2), nullable=False),
        sa.Column("asset_ids", ARRAY(sa.String(36)), nullable=False, server_default="{}"),
        sa.Column("document_storage_key", sa.String(512), nullable=True),
        sa.Column("document_sha256", sa.String(64), nullable=True),
        sa.Column("submitted_by_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "wcr_number", "wcr_version", name="uq_wcr_num_ver"),
    )
    op.create_index("ix_wcr_project", "wcr", ["organization_id", "project_id"])

    op.create_table(
        "commissioning_record",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        sa.Column("commissioned_date", sa.Date(), nullable=True),
        sa.Column("commissioned_by_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("grid_synchronization_date", sa.Date(), nullable=True),
        sa.Column("initial_generation_kwh", sa.Numeric(10, 3), nullable=True),
        sa.Column("test_results", JSONB(), nullable=False, server_default="{}"),
        sa.Column("checklist_results", JSONB(), nullable=False, server_default="{}"),
        sa.Column("discom_approval_reference", sa.String(255), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "project_id", name="uq_commissioning_project"),
    )
    op.create_index("ix_commissioning_plant", "commissioning_record", ["organization_id", "plant_id"])

    # ── Warranty ──────────────────────────────────────────────────────────────
    op.create_table(
        "warranty",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("asset.id", ondelete="SET NULL"), nullable=True),
        sa.Column("warranty_type", sa.String(50), nullable=False),
        sa.Column("provider_name", sa.String(255), nullable=False),
        sa.Column("certificate_number", sa.String(100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("period_years", sa.Integer(), nullable=False),
        sa.Column("coverage_details", sa.Text(), nullable=False),
        sa.Column("exclusions", sa.Text(), nullable=True),
        sa.Column("document_storage_key", sa.String(512), nullable=True),
        sa.Column("document_sha256", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_warranty_project", "warranty", ["organization_id", "project_id"])
    op.create_index("ix_warranty_end", "warranty", ["organization_id", "end_date"])

    op.create_table(
        "warranty_claim",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("warranty_id", UUID(as_uuid=True), sa.ForeignKey("warranty.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_number", sa.String(100), nullable=False),
        sa.Column("opened_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="opened"),
        sa.Column("defect_description", sa.Text(), nullable=False),
        sa.Column("affected_components", ARRAY(sa.String(100)), nullable=False, server_default="{}"),
        sa.Column("reported_by_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolved_date", sa.Date(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("replacement_asset_ids", ARRAY(sa.String(36)), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "claim_number", name="uq_claim_number"),
    )
    op.create_index("ix_claim_warranty", "warranty_claim", ["warranty_id"])

    op.create_table(
        "claim_event",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", UUID(as_uuid=True), sa.ForeignKey("warranty_claim.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_claim_event_claim", "claim_event", ["claim_id"])

    # ── O&M ───────────────────────────────────────────────────────────────────
    op.create_table(
        "sla_policy",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False),
        sa.Column("first_response_hours", sa.Integer(), nullable=False),
        sa.Column("resolution_hours", sa.Integer(), nullable=False),
        sa.Column("escalation_hours", sa.Integer(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "name", name="uq_sla_name"),
    )

    op.create_table(
        "maintenance_plan",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_maint_plan_project", "maintenance_plan", ["organization_id", "project_id"])

    op.create_table(
        "maintenance_task",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("maintenance_plan.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("frequency", sa.String(50), nullable=False),
        sa.Column("estimated_duration_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("checklist_template", JSONB(), nullable=False, server_default="[]"),
        sa.Column("assigned_team_id", UUID(as_uuid=True), nullable=True),
        sa.Column("next_due_date", sa.Date(), nullable=True),
        sa.Column("last_completed_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_maint_task_due", "maintenance_task", ["organization_id", "next_due_date"])

    op.create_table(
        "ticket",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_number", sa.String(50), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, default="corrective"),
        sa.Column("priority", sa.String(50), nullable=False, default="medium"),
        sa.Column("status", sa.String(50), nullable=False, default="open"),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reporter_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assignee_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sla_policy_id", UUID(as_uuid=True), sa.ForeignKey("sla_policy.id", ondelete="SET NULL"), nullable=True),
        sa.Column("first_response_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("affected_asset_ids", ARRAY(sa.String(36)), nullable=False, server_default="{}"),
        sa.Column("tags", ARRAY(sa.String(50)), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "ticket_number", name="uq_ticket_number"),
    )
    op.create_index("ix_ticket_project", "ticket", ["organization_id", "project_id"])
    op.create_index("ix_ticket_status", "ticket", ["organization_id", "status"])

    op.create_table(
        "ticket_event",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", UUID(as_uuid=True), sa.ForeignKey("ticket.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("from_status", sa.String(50), nullable=True),
        sa.Column("to_status", sa.String(50), nullable=True),
        sa.Column("metadata", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ticket_event_ticket", "ticket_event", ["ticket_id"])

    op.create_table(
        "visit",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", UUID(as_uuid=True), sa.ForeignKey("ticket.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("technician_user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, default="planned"),
        sa.Column("planned_date", sa.Date(), nullable=True),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("departed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("work_done_summary", sa.Text(), nullable=True),
        sa.Column("parts_used", JSONB(), nullable=False, server_default="[]"),
        sa.Column("geo_location", JSONB(), nullable=True),
        sa.Column("photo_storage_keys", ARRAY(sa.String(512)), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_visit_project", "visit", ["organization_id", "project_id"])

    # ── Telemetry ─────────────────────────────────────────────────────────────
    op.create_table(
        "inverter_device",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("asset.id", ondelete="SET NULL"), nullable=True),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("serial_number", sa.String(100), nullable=False),
        sa.Column("rated_capacity_kw", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("device_specs", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "serial_number", name="uq_inverter_serial"),
    )
    op.create_index("ix_inverter_project", "inverter_device", ["organization_id", "project_id"])

    op.create_table(
        "data_source_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("inverter_id", UUID(as_uuid=True), sa.ForeignKey("inverter_device.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("protocol", sa.String(50), nullable=False),
        sa.Column("host", sa.String(255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("poll_interval_seconds", sa.Integer(), nullable=False, default=300),
        sa.Column("connection_params", JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "generation_record",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("inverter_id", UUID(as_uuid=True), sa.ForeignKey("inverter_device.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False, default=15),
        sa.Column("energy_kwh", sa.Numeric(12, 4), nullable=False),
        sa.Column("peak_power_kw", sa.Numeric(10, 3), nullable=True),
        sa.Column("avg_power_kw", sa.Numeric(10, 3), nullable=True),
        sa.Column("grid_voltage_v", sa.Numeric(7, 2), nullable=True),
        sa.Column("grid_frequency_hz", sa.Numeric(6, 3), nullable=True),
        sa.Column("power_factor", sa.Numeric(5, 4), nullable=True),
        sa.Column("irradiance_wm2", sa.Numeric(8, 2), nullable=True),
        sa.Column("module_temp_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("ambient_temp_c", sa.Numeric(6, 2), nullable=True),
        sa.Column("raw_payload", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("inverter_id", "recorded_at", "interval_minutes", name="uq_gen_record"),
    )
    op.create_index("ix_gen_record_plant_time", "generation_record", ["plant_id", "recorded_at"])
    op.create_index("ix_gen_record_inverter_time", "generation_record", ["inverter_id", "recorded_at"])

    op.create_table(
        "telemetry_alarm",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("inverter_id", UUID(as_uuid=True), sa.ForeignKey("inverter_device.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("alarm_code", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, default="warning"),
        sa.Column("status", sa.String(50), nullable=False, default="active"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alarm_plant_time", "telemetry_alarm", ["plant_id", "occurred_at"])
    op.create_index("ix_alarm_status", "telemetry_alarm", ["organization_id", "status"])

    op.create_table(
        "outage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("plant_id", sa.String(50), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("outage_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outage_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_loss_kwh", sa.Numeric(12, 4), nullable=True),
        sa.Column("cause", sa.String(255), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, default=False),
        sa.Column("linked_ticket_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_outage_plant_time", "outage", ["plant_id", "outage_start"])

    # Convert generation_record to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable('generation_record', 'recorded_at', if_not_exists => TRUE)
    """)


def downgrade() -> None:
    tables = [
        "outage", "telemetry_alarm", "generation_record", "data_source_config", "inverter_device",
        "visit", "ticket_event", "ticket", "maintenance_task", "maintenance_plan", "sla_policy",
        "claim_event", "warranty_claim", "warranty",
        "commissioning_record", "wcr", "inspection_item", "inspection", "inspection_template", "meter",
        "source_snapshot", "reconciliation_comparison", "reconciliation_run",
        "compliance_waiver", "compliance_result", "compliance_run",
    ]
    for t in tables:
        op.drop_table(t)
