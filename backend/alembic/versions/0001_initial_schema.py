"""Initial schema for Identity and Platform modules with RLS policies

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-01 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # 2. Organization table
    op.create_table(
        'organization',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('state_code', sa.String(10), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False, server_default='starter'),
        sa.Column('status', sa.String(50), nullable=False, server_default='trial'),
        sa.Column('sso_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('sso_provider', sa.String(50), nullable=True),
        sa.Column('sso_config', postgresql.JSONB(), nullable=True),
        sa.Column('feature_flags', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('gst_number', sa.String(20), nullable=True),
        sa.Column('pan_number', sa.String(15), nullable=True),
        sa.Column('address', postgresql.JSONB(), nullable=True),
        sa.Column('plant_id_sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('audit_chain_head_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )
    op.create_index('ix_organization_slug', 'organization', ['slug'])
    op.create_index('ix_organization_status', 'organization', ['status'])

    # 3. Branch table
    op.create_table(
        'branch',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('state_code', sa.String(10), nullable=False),
        sa.Column('address', postgresql.JSONB(), nullable=True),
        sa.Column('is_headquarters', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('organization_id', 'code', name='uq_branch_org_code'),
    )
    op.create_index('ix_branch_org', 'branch', ['organization_id'])

    # 4. Role table
    op.create_table(
        'role',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_role_org', 'role', ['organization_id'])

    # 5. Permission table
    op.create_table(
        'permission',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
    )
    op.create_index('ix_permission_code', 'permission', ['code'])

    # 6. Role-Permission junction
    op.create_table(
        'role_permission',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('role.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permission.id', ondelete='CASCADE'), primary_key=True),
    )

    # 7. User table
    op.create_table(
        'user',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('totp_secret', sa.String(64), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('organization_id', 'email', name='uq_user_org_email'),
    )
    op.create_index('ix_user_org', 'user', ['organization_id'])
    op.create_index('ix_user_email', 'user', ['email'])

    # 8. Membership table
    op.create_table(
        'membership',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('role.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branch.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('organization_id', 'user_id', 'role_id', 'branch_id', name='uq_membership'),
    )
    op.create_index('ix_membership_user', 'membership', ['user_id'])
    op.create_index('ix_membership_org', 'membership', ['organization_id'])

    # 9. Session table
    op.create_table(
        'session',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('refresh_token_hash', sa.String(64), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_session_token_hash', 'session', ['token_hash'])
    op.create_index('ix_session_user', 'session', ['user_id'])

    # 10. Device table
    op.create_table(
        'device',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_fingerprint', sa.String(128), nullable=False),
        sa.Column('device_name', sa.String(100), nullable=False),
        sa.Column('fcm_token', sa.String(255), nullable=True),
        sa.Column('is_trusted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_device_fingerprint', 'device', ['organization_id', 'device_fingerprint'])

    # 11. ApiKey table
    op.create_table(
        'api_key',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(16), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String(100)), nullable=False, server_default='{}'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_api_key_hash', 'api_key', ['key_hash'])

    # 12. AuditEvent table
    op.create_table(
        'audit_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('sequence_num', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_api_key_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('subject_type', sa.String(100), nullable=False),
        sa.Column('subject_id', sa.String(100), nullable=True),
        sa.Column('payload', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('event_hash', sa.String(64), nullable=False),
        sa.Column('prev_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('organization_id', 'sequence_num', name='uq_audit_org_sequence'),
    )
    op.create_index('ix_audit_org_seq', 'audit_event', ['organization_id', 'sequence_num'])
    op.create_index('ix_audit_subject', 'audit_event', ['organization_id', 'subject_type', 'subject_id'])
    op.create_index('ix_audit_actor', 'audit_event', ['organization_id', 'actor_user_id'])
    op.create_index('ix_audit_event_type', 'audit_event', ['organization_id', 'event_type'])

    # 13. AuditCheckpoint table
    op.create_table(
        'audit_checkpoint',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('up_to_sequence_num', sa.BigInteger(), nullable=False),
        sa.Column('head_hash', sa.String(64), nullable=False),
        sa.Column('signature_hmac', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_audit_checkpoint_org', 'audit_checkpoint', ['organization_id', 'up_to_sequence_num'])

    # 14. OutboxEvent table
    op.create_table(
        'outbox_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_outbox_pending', 'outbox_event', ['status', 'next_retry_at'])

    # 15. Job table
    op.create_table(
        'job',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_job_status', 'job', ['organization_id', 'status'])

    # 16. FeatureFlag table
    op.create_table(
        'feature_flag',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled_globally', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('plans_allowed', postgresql.ARRAY(sa.String(50)), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # 17. Notification table
    op.create_table(
        'notification',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False, server_default='in_app'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_notification_user', 'notification', ['user_id', 'status'])

    # 18. ExportJob table
    op.create_table(
        'export_job',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('export_type', sa.String(50), nullable=False),
        sa.Column('file_format', sa.String(20), nullable=False),
        sa.Column('download_url', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='queued'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # 19. IdempotencyKey table
    op.create_table(
        'idempotency_key',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('idempotency_key', sa.String(255), nullable=False),
        sa.Column('request_method', sa.String(10), nullable=False),
        sa.Column('request_path', sa.String(255), nullable=False),
        sa.Column('request_body_hash', sa.String(64), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_headers', postgresql.JSONB(), nullable=True),
        sa.Column('response_body', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('organization_id', 'idempotency_key', name='uq_idempotency_org_key'),
    )
    op.create_index('ix_idempotency_org_key', 'idempotency_key', ['organization_id', 'idempotency_key'])

    # ─────────────────────────────────────────────────────────────────────────────
    # ROW LEVEL SECURITY (ADR-002)
    # ─────────────────────────────────────────────────────────────────────────────
    # Enable and Force RLS on all tenant-scoped tables
    tenant_tables = [
        'branch',
        'user',
        'membership',
        'session',
        'device',
        'api_key',
        'audit_event',
        'audit_checkpoint',
        'outbox_event',
        'job',
        'notification',
        'export_job',
        'idempotency_key',
    ]

    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            USING (organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
            WITH CHECK (organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
        """)

    # Organization table has self-referential RLS (id = current_tenant)
    op.execute("ALTER TABLE organization ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE organization FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY org_isolation_policy ON organization
        USING (id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
        WITH CHECK (id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
    """)

    # Role table policy: can see system roles (org_id is null) OR roles belonging to tenant
    op.execute("ALTER TABLE role ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE role FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY role_isolation_policy ON role
        USING (
            organization_id IS NULL 
            OR organization_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid
        )
    """)

    # Tamper-evident protection: Prevent UPDATE or DELETE on audit_event
    op.execute("REVOKE UPDATE, DELETE ON audit_event FROM PUBLIC")


def downgrade() -> None:
    tables = [
        'idempotency_key',
        'export_job',
        'notification',
        'feature_flag',
        'job',
        'outbox_event',
        'audit_checkpoint',
        'audit_event',
        'api_key',
        'device',
        'session',
        'membership',
        'user',
        'role_permission',
        'permission',
        'role',
        'branch',
        'organization',
    ]
    for table in tables:
        op.drop_table(table)
