"""Engineering & Design and Asset Registry tables with RLS

Revision ID: 0004_engineering_and_assets
Revises: 0003_project_schema
Create Date: 2026-10-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0004_engineering_and_assets'
down_revision: Union[str, None] = '0003_project_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Design table
    op.create_table(
        'design',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column('design_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('name', sa.String(100), nullable=False, server_default='Preliminary Design'),
        sa.Column('system_type', sa.String(50), nullable=False, server_default='grid_tied'),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('capacity_kw_dc', sa.Numeric(10, 2), nullable=False),
        sa.Column('capacity_kw_ac', sa.Numeric(10, 2), nullable=False),
        sa.Column('panel_make', sa.String(100), nullable=False),
        sa.Column('panel_model', sa.String(100), nullable=False),
        sa.Column('panel_wattage', sa.Numeric(6, 1), nullable=False),
        sa.Column('panel_count', sa.Integer(), nullable=False),
        sa.Column('inverter_make', sa.String(100), nullable=False),
        sa.Column('inverter_model', sa.String(100), nullable=False),
        sa.Column('inverter_count', sa.Integer(), nullable=False),
        sa.Column('tilt_degrees', sa.Numeric(5, 2), nullable=False, server_default='15.0'),
        sa.Column('azimuth_degrees', sa.Numeric(5, 2), nullable=False, server_default='180.0'),
        sa.Column('expected_annual_generation_kwh', sa.Numeric(12, 2), nullable=True),
        sa.Column('performance_ratio_percent', sa.Numeric(5, 2), nullable=True, server_default='78.5'),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('organization_id', 'project_id', 'design_version', name='uq_design_project_ver'),
    )
    op.create_index('ix_design_project', 'design', ['project_id'])

    # 2. String Configuration table
    op.create_table(
        'string_configuration',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('design_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('design.id', ondelete='CASCADE'), nullable=False),
        sa.Column('string_number', sa.Integer(), nullable=False),
        sa.Column('inverter_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('mppt_tracker_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('panels_count', sa.Integer(), nullable=False),
        sa.Column('vmp_volts', sa.Numeric(6, 2), nullable=True),
        sa.Column('voc_volts', sa.Numeric(6, 2), nullable=True),
        sa.Column('imp_amps', sa.Numeric(6, 2), nullable=True),
        sa.Column('isc_amps', sa.Numeric(6, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('design_id', 'string_number', name='uq_string_config_num'),
    )

    # 3. BOM table
    op.create_table(
        'bom',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column('design_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('design.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bom_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finalized_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('organization_id', 'project_id', 'bom_version', name='uq_bom_project_ver'),
    )

    # 4. BOM Item table
    op.create_table(
        'bom_item',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bom_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bom.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('item_code', sa.String(100), nullable=True),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('make', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('specifications', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit_of_measure', sa.String(20), nullable=False, server_default='NOS'),
        sa.Column('is_serialized', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_bom_item_bom', 'bom_item', ['bom_id'])
    op.create_index('ix_bom_item_category', 'bom_item', ['bom_id', 'category'])

    # 5. Asset Type table
    op.create_table(
        'asset_type',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('make', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('nominal_rating_kw', sa.Numeric(10, 2), nullable=True),
        sa.Column('warranty_months', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('is_serialized', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('specifications', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('organization_id', 'category', 'make', 'model', name='uq_asset_type_make_model'),
    )
    op.create_index('ix_asset_type_category', 'asset_type', ['organization_id', 'category'])

    # 6. Asset table
    op.create_table(
        'asset',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('asset_type.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project.id', ondelete='SET NULL'), nullable=True),
        sa.Column('plant_id', sa.String(50), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=False),
        sa.Column('normalized_serial', sa.String(100), nullable=False),
        sa.Column('qr_token', sa.String(128), nullable=False, unique=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='in_stock'),
        sa.Column('location_tag', sa.String(100), nullable=True),
        sa.Column('installed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('commissioned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_fields', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('organization_id', 'normalized_serial', name='uq_asset_org_normalized_serial'),
    )
    op.create_index('ix_asset_project', 'asset', ['organization_id', 'project_id'])
    op.create_index('ix_asset_plant', 'asset', ['organization_id', 'plant_id'])
    op.create_index('ix_asset_status', 'asset', ['organization_id', 'status'])

    # 7. Asset Event table
    op.create_table(
        'asset_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('event_payload', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_asset_event_asset', 'asset_event', ['asset_id'])
    op.create_index('ix_asset_event_org_type', 'asset_event', ['organization_id', 'event_type'])

    # 8. Asset Relationship table
    op.create_table(
        'asset_relationship',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('child_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('parent_asset_id', 'child_asset_id', name='uq_asset_parent_child'),
    )

    # ─────────────────────────────────────────────────────────────────────────────
    # ROW LEVEL SECURITY (RLS)
    # ─────────────────────────────────────────────────────────────────────────────
    tables = [
        'design',
        'string_configuration',
        'bom',
        'bom_item',
        'asset_type',
        'asset',
        'asset_event',
        'asset_relationship',
    ]
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_policy ON {table}
            USING (organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
            WITH CHECK (organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
        """)


def downgrade() -> None:
    tables = [
        'asset_relationship',
        'asset_event',
        'asset',
        'asset_type',
        'bom_item',
        'bom',
        'string_configuration',
        'design',
    ]
    for table in tables:
        op.drop_table(table)
