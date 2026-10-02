"""Project and Workflow Engine schema with project, application, workflow_definition, stage_history, workflow_transition_override and RLS

Revision ID: 0003_project_schema
Revises: 0002_crm_schema
Create Date: 2026-10-01 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0003_project_schema'
down_revision: Union[str, None] = '0002_crm_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Project table
    op.create_table(
        'project',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plant_id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customer.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('manager_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('capacity_kw_dc', sa.Numeric(10, 2), nullable=False),
        sa.Column('capacity_kw_ac', sa.Numeric(10, 2), nullable=False),
        sa.Column('estimated_annual_kwh', sa.Numeric(12, 2), nullable=True),
        sa.Column('current_stage', sa.String(50), nullable=False, server_default='lead'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('stage_entered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('target_commissioning_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_commissioning_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('project_metadata', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('organization_id', 'plant_id', name='uq_project_org_plant_id'),
    )
    op.create_index('ix_project_org_stage', 'project', ['organization_id', 'current_stage'])
    op.create_index('ix_project_org_customer', 'project', ['organization_id', 'customer_id'])
    op.create_index('ix_project_org_site', 'project', ['organization_id', 'site_id'])

    # 2. Application table (DISCOM Interconnection)
    op.create_table(
        'application',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column('discom_name', sa.String(100), nullable=False),
        sa.Column('application_number', sa.String(100), nullable=False),
        sa.Column('consumer_number', sa.String(100), nullable=False),
        sa.Column('feeder_code', sa.String(100), nullable=True),
        sa.Column('dt_code', sa.String(100), nullable=True),
        sa.Column('applied_capacity_kw', sa.Numeric(10, 2), nullable=False),
        sa.Column('sanctioned_capacity_kw', sa.Numeric(10, 2), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('submission_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discom_fee_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('discom_fee_receipt_ref', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )
    op.create_index('ix_app_project', 'application', ['project_id'])
    op.create_index('ix_app_org_status', 'application', ['organization_id', 'status'])
    op.create_index('ix_app_discom_app_num', 'application', ['organization_id', 'discom_name', 'application_number'])

    # 3. WorkflowDefinition table
    op.create_table(
        'workflow_definition',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('definition_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('stages_config', postgresql.JSONB(), nullable=False),
        sa.Column('transitions_config', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('organization_id', 'code', 'definition_version', name='uq_workflow_org_code_ver'),
    )

    # 4. StageHistory table
    op.create_table(
        'stage_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_stage', sa.String(50), nullable=False),
        sa.Column('to_stage', sa.String(50), nullable=False),
        sa.Column('transitioned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('duration_in_stage_seconds', sa.Integer(), nullable=True),
        sa.Column('transition_reason', sa.Text(), nullable=True),
        sa.Column('guard_results', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_stage_hist_project', 'stage_history', ['project_id'])
    op.create_index('ix_stage_hist_org_transition', 'stage_history', ['organization_id', 'to_stage'])

    # 5. WorkflowTransitionOverride table
    op.create_table(
        'workflow_transition_override',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_stage', sa.String(50), nullable=False),
        sa.Column('to_stage', sa.String(50), nullable=False),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('failed_guards', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # ─────────────────────────────────────────────────────────────────────────────
    # ROW LEVEL SECURITY (RLS) FOR PROJECT TABLES
    # ─────────────────────────────────────────────────────────────────────────────
    project_tables = [
        'project',
        'application',
        'workflow_definition',
        'stage_history',
        'workflow_transition_override',
    ]
    for table in project_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_policy ON {table}
            USING (organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
            WITH CHECK (organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
        """)


def downgrade() -> None:
    tables = [
        'workflow_transition_override',
        'stage_history',
        'workflow_definition',
        'application',
        'project',
    ]
    for table in tables:
        op.drop_table(table)
