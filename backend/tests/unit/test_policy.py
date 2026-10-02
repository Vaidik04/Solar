import uuid
import pytest

from app.core.policy import (
    AuthzResource,
    DefaultRole,
    Permission,
    PolicyEngine,
    UserContext,
    DEFAULT_ROLE_PERMISSIONS,
)


@pytest.fixture
def policy_engine() -> PolicyEngine:
    return PolicyEngine()


@pytest.fixture
def sample_org_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_user_context(sample_org_id: uuid.UUID) -> UserContext:
    return UserContext(
        user_id=uuid.uuid4(),
        org_id=sample_org_id,
        session_id=uuid.uuid4(),
        email="engineer@example.com",
        is_active=True,
        is_platform_admin=False,
        permissions=set(DEFAULT_ROLE_PERMISSIONS[DefaultRole.SOLAR_ENGINEER]),
        branch_ids=set(),
        assigned_project_ids=set(),
        plan="professional",
        totp_verified=False,
    )


def test_rbac_allowed_permission(policy_engine: PolicyEngine, sample_user_context: UserContext, sample_org_id: uuid.UUID):
    resource = AuthzResource(org_id=sample_org_id)
    result = policy_engine.authorize(sample_user_context, Permission.ENGINEERING_DESIGN_MANAGE, resource)
    assert result.allowed is True


def test_rbac_denied_permission(policy_engine: PolicyEngine, sample_user_context: UserContext, sample_org_id: uuid.UUID):
    resource = AuthzResource(org_id=sample_org_id)
    # Solar engineer is not granted user creation (identity:user:create)
    result = policy_engine.authorize(sample_user_context, Permission.IDENTITY_USER_CREATE, resource)
    assert result.allowed is False
    assert "not granted" in result.reason


def test_tenant_isolation_denial(policy_engine: PolicyEngine, sample_user_context: UserContext):
    # Attempting to access resource belonging to a different tenant
    different_org_id = uuid.uuid4()
    resource = AuthzResource(org_id=different_org_id)

    result = policy_engine.authorize(sample_user_context, Permission.ENGINEERING_DESIGN_MANAGE, resource)
    assert result.allowed is False
    assert "different organization" in result.reason


def test_abac_branch_restriction(policy_engine: PolicyEngine, sample_org_id: uuid.UUID):
    branch_a = uuid.uuid4()
    branch_b = uuid.uuid4()

    user = UserContext(
        user_id=uuid.uuid4(),
        org_id=sample_org_id,
        session_id=uuid.uuid4(),
        email="tech@example.com",
        is_active=True,
        is_platform_admin=False,
        permissions={Permission.FIELD_INSPECTION_MANAGE},
        branch_ids={branch_a},  # Only has access to branch A
        assigned_project_ids=set(),
        plan="professional",
        totp_verified=False,
    )

    # Resource at branch A: Allowed
    res_a = AuthzResource(org_id=sample_org_id, branch_id=branch_a)
    assert policy_engine.authorize(user, Permission.FIELD_INSPECTION_MANAGE, res_a).allowed is True

    # Resource at branch B: Denied
    res_b = AuthzResource(org_id=sample_org_id, branch_id=branch_b)
    result = policy_engine.authorize(user, Permission.FIELD_INSPECTION_MANAGE, res_b)
    assert result.allowed is False
    assert "branch access" in result.reason


def test_inactive_user_denied(policy_engine: PolicyEngine, sample_user_context: UserContext, sample_org_id: uuid.UUID):
    sample_user_context.is_active = False
    resource = AuthzResource(org_id=sample_org_id)
    result = policy_engine.authorize(sample_user_context, Permission.ENGINEERING_DESIGN_MANAGE, resource)
    assert result.allowed is False
    assert "inactive" in result.reason


def test_plan_level_requirement(policy_engine: PolicyEngine, sample_org_id: uuid.UUID):
    user = UserContext(
        user_id=uuid.uuid4(),
        org_id=sample_org_id,
        session_id=uuid.uuid4(),
        email="starter@example.com",
        is_active=True,
        is_platform_admin=False,
        permissions={Permission.PLATFORM_EXPORT},
        branch_ids=set(),
        assigned_project_ids=set(),
        plan="starter",
        totp_verified=False,
    )

    enterprise_res = AuthzResource(org_id=sample_org_id, requires_plan="enterprise")
    result = policy_engine.authorize(user, Permission.PLATFORM_EXPORT, enterprise_res)
    assert result.allowed is False
    assert "requires plan" in result.reason
