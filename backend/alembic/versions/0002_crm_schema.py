"""CRM and Sites schema with customer, contact, site, site_survey, site_photo and RLS

Revision ID: 0002_crm_schema
Revises: 0001_initial_schema
Create Date: 2026-10-01 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002_crm_schema'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Customer table
    op.create_table(
        'customer',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_type', sa.String(50), nullable=False, server_default='residential'),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('alternate_phone', sa.String(20), nullable=True),
        sa.Column('pan_number', sa.String(15), nullable=True),
        sa.Column('gst_number', sa.String(20), nullable=True),
        sa.Column('kyc_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('billing_address', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )
    op.create_index('ix_customer_org_phone', 'customer', ['organization_id', 'phone'])
    op.create_index('ix_customer_org_email', 'customer', ['organization_id', 'email'])
    op.create_index('ix_customer_org_name', 'customer', ['organization_id', 'name'])

    # 2. Contact table
    op.create_table(
        'contact',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customer.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('designation', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_contact_customer', 'contact', ['customer_id'])
    op.create_index('ix_contact_org', 'contact', ['organization_id'])

    # 3. Site table
    op.create_table(
        'site',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customer.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('address', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('state_code', sa.String(10), nullable=False),
        sa.Column('pincode', sa.String(10), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('discom_name', sa.String(100), nullable=False),
        sa.Column('consumer_number', sa.String(100), nullable=False),
        sa.Column('meter_number', sa.String(100), nullable=True),
        sa.Column('sanctioned_load_kw', sa.Numeric(10, 2), nullable=False),
        sa.Column('tariff_category', sa.String(50), nullable=True),
        sa.Column('transformer_capacity_kva', sa.Numeric(10, 2), nullable=True),
        sa.Column('supply_voltage_kv', sa.Numeric(6, 2), nullable=True, server_default='0.415'),
        sa.Column('roof_type', sa.String(50), nullable=False, server_default='rcc_flat'),
        sa.Column('usable_roof_area_sqft', sa.Numeric(10, 2), nullable=False),
        sa.Column('tilt_angle_degrees', sa.Numeric(5, 2), nullable=True),
        sa.Column('azimuth_degrees', sa.Numeric(5, 2), nullable=True, server_default='180.0'),
        sa.Column('shading_hazards', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )
    op.create_index('ix_site_org_customer', 'site', ['organization_id', 'customer_id'])
    op.create_index('ix_site_org_consumer_num', 'site', ['organization_id', 'consumer_number'])
    op.create_index('ix_site_org_state_pincode', 'site', ['organization_id', 'state_code', 'pincode'])

    # 4. SiteSurvey table
    op.create_table(
        'site_survey',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.id', ondelete='CASCADE'), nullable=False),
        sa.Column('surveyor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='scheduled'),
        sa.Column('survey_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('structural_viability', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('recommended_capacity_kw', sa.Numeric(10, 2), nullable=True),
        sa.Column('electrical_assessment', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('shadow_analysis', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('gps_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('survey_coordinates', postgresql.JSONB(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )
    op.create_index('ix_site_survey_site', 'site_survey', ['site_id'])
    op.create_index('ix_site_survey_org_status', 'site_survey', ['organization_id', 'status'])

    # 5. SitePhoto table
    op.create_table(
        'site_photo',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site.id', ondelete='CASCADE'), nullable=False),
        sa.Column('survey_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('site_survey.id', ondelete='SET NULL'), nullable=True),
        sa.Column('uploader_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='roof'),
        sa.Column('caption', sa.String(255), nullable=True),
        sa.Column('storage_key', sa.String(512), nullable=False),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False, server_default='image/jpeg'),
        sa.Column('exif_latitude', sa.Float(), nullable=True),
        sa.Column('exif_longitude', sa.Float(), nullable=True),
        sa.Column('exif_captured_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('compass_bearing_degrees', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_site_photo_site', 'site_photo', ['site_id'])
    op.create_index('ix_site_photo_sha256', 'site_photo', ['organization_id', 'sha256_hash'])

    # ─────────────────────────────────────────────────────────────────────────────
    # ROW LEVEL SECURITY (RLS) FOR CRM TABLES
    # ─────────────────────────────────────────────────────────────────────────────
    crm_tables = ['customer', 'contact', 'site', 'site_survey', 'site_photo']
    for table in crm_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_policy ON {table}
            USING (organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
            WITH CHECK (organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
        """)


def downgrade() -> None:
    tables = ['site_photo', 'site_survey', 'site', 'contact', 'customer']
    for table in tables:
        op.drop_table(table)
