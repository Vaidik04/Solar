"""
Solar Operations OS — RBAC + ABAC Central Policy Module (ADR-005)
All authorization decisions go through this module.
No other module may query role/permission tables directly.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


# ── Permission Strings ────────────────────────────────────────────────────────
class Permission(StrEnum):
    # Identity
    IDENTITY_USER_CREATE = "identity:user:create"
    IDENTITY_USER_READ = "identity:user:read"
    IDENTITY_USER_DEACTIVATE = "identity:user:deactivate"
    IDENTITY_ROLE_MANAGE = "identity:role:manage"
    IDENTITY_ORG_SETTINGS = "identity:org:settings"
    IDENTITY_API_KEY_MANAGE = "identity:apikey:manage"

    # CRM
    CRM_CUSTOMER_CREATE = "crm:customer:create"
    CRM_CUSTOMER_READ = "crm:customer:read"
    CRM_CUSTOMER_UPDATE = "crm:customer:update"
    CRM_SITE_CREATE = "crm:site:create"
    CRM_SITE_READ = "crm:site:read"
    CRM_SITE_UPDATE = "crm:site:update"

    # Projects
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_TRANSITION = "project:transition"
    PROJECT_TRANSITION_OVERRIDE = "project:transition:override"
    PROJECT_DELETE = "project:delete"
    PROJECT_ASSIGN = "project:assign"

    # Engineering
    ENGINEERING_DESIGN_MANAGE = "engineering:design:manage"
    ENGINEERING_BOM_MANAGE = "engineering:bom:manage"

    # Assets
    ASSETS_READ = "assets:read"
    ASSETS_REGISTER = "assets:register"
    ASSETS_BULK_IMPORT = "assets:bulk_import"
    ASSETS_ALLOCATE = "assets:allocate"
    ASSETS_EVENT_RECORD = "assets:event:record"
    ASSETS_RETIRE = "assets:retire"
    ASSETS_LABEL_PRINT = "assets:label:print"

    # Supply
    SUPPLY_PO_CREATE = "supply:po:create"
    SUPPLY_PO_READ = "supply:po:read"
    SUPPLY_RECEIVE = "supply:receive"
    SUPPLY_STOCK_ADJUST = "supply:stock:adjust"

    # Documents
    DOCUMENTS_UPLOAD = "documents:upload"
    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_VERIFY = "documents:verify"
    DOCUMENTS_REJECT = "documents:reject"
    DOCUMENTS_TYPE_MANAGE = "documents:type:manage"

    # Regulations
    REGULATIONS_READ = "regulations:read"
    REGULATIONS_MANAGE = "regulations:manage"
    REGULATIONS_RULE_PUBLISH = "regulations:rule:publish"

    # Compliance
    COMPLIANCE_RUN = "compliance:run"
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_WAIVE = "compliance:waive"

    # Reconciliation
    RECONCILIATION_RUN = "reconciliation:run"
    RECONCILIATION_READ = "reconciliation:read"

    # Field
    FIELD_METER_MANAGE = "field:meter:manage"
    FIELD_INSPECTION_MANAGE = "field:inspection:manage"
    FIELD_WCR_GENERATE = "field:wcr:generate"
    FIELD_COMMISSION = "field:commission"

    # Warranty
    WARRANTY_READ = "warranty:read"
    WARRANTY_MANAGE = "warranty:manage"
    WARRANTY_CLAIM = "warranty:claim"

    # O&M
    OAM_PLAN_MANAGE = "oam:plan:manage"
    OAM_VISIT_MANAGE = "oam:visit:manage"
    OAM_TICKET_CREATE = "oam:ticket:create"
    OAM_TICKET_ASSIGN = "oam:ticket:assign"
    OAM_TICKET_RESOLVE = "oam:ticket:resolve"

    # Telemetry
    TELEMETRY_READ = "telemetry:read"
    TELEMETRY_CONNECTOR_MANAGE = "telemetry:connector:manage"

    # Platform
    PLATFORM_AUDIT_READ = "platform:audit:read"
    PLATFORM_AUDIT_VERIFY = "platform:audit:verify"
    PLATFORM_EXPORT = "platform:export"
    PLATFORM_ADMIN = "platform:admin"

    # Archive / soft-delete
    ARCHIVAL_READ = "archival:read"


# ── Default Role Definitions ──────────────────────────────────────────────────
class DefaultRole(StrEnum):
    OWNER = "owner"
    PROJECT_MANAGER = "project_manager"
    SOLAR_ENGINEER = "solar_engineer"
    SITE_ENGINEER = "site_engineer"
    COMPLIANCE_OFFICER = "compliance_officer"
    PROCUREMENT = "procurement"
    TECHNICIAN = "technician"
    OAM_MANAGER = "oam_manager"
    CUSTOMER = "customer"
    VIEWER = "viewer"


# Default permissions for each built-in role
DEFAULT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    DefaultRole.OWNER: {p for p in Permission},  # all permissions
    DefaultRole.PROJECT_MANAGER: {
        Permission.CRM_CUSTOMER_CREATE,
        Permission.CRM_CUSTOMER_READ,
        Permission.CRM_CUSTOMER_UPDATE,
        Permission.CRM_SITE_CREATE,
        Permission.CRM_SITE_READ,
        Permission.CRM_SITE_UPDATE,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_TRANSITION,
        Permission.PROJECT_ASSIGN,
        Permission.ENGINEERING_DESIGN_MANAGE,
        Permission.ENGINEERING_BOM_MANAGE,
        Permission.ASSETS_READ,
        Permission.ASSETS_ALLOCATE,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_UPLOAD,
        Permission.COMPLIANCE_READ,
        Permission.COMPLIANCE_RUN,
        Permission.RECONCILIATION_READ,
        Permission.RECONCILIATION_RUN,
        Permission.SUPPLY_PO_READ,
        Permission.WARRANTY_READ,
        Permission.OAM_PLAN_MANAGE,
        Permission.OAM_TICKET_CREATE,
        Permission.OAM_TICKET_ASSIGN,
        Permission.TELEMETRY_READ,
        Permission.PLATFORM_EXPORT,
    },
    DefaultRole.SOLAR_ENGINEER: {
        Permission.PROJECT_READ,
        Permission.ENGINEERING_DESIGN_MANAGE,
        Permission.ENGINEERING_BOM_MANAGE,
        Permission.ASSETS_READ,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_UPLOAD,
        Permission.COMPLIANCE_READ,
        Permission.COMPLIANCE_RUN,
        Permission.RECONCILIATION_READ,
        Permission.RECONCILIATION_RUN,
        Permission.FIELD_METER_MANAGE,
        Permission.FIELD_INSPECTION_MANAGE,
        Permission.FIELD_WCR_GENERATE,
        Permission.TELEMETRY_READ,
    },
    DefaultRole.SITE_ENGINEER: {
        Permission.PROJECT_READ,
        Permission.ASSETS_READ,
        Permission.ASSETS_EVENT_RECORD,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_UPLOAD,
        Permission.FIELD_METER_MANAGE,
        Permission.FIELD_INSPECTION_MANAGE,
        Permission.FIELD_WCR_GENERATE,
        Permission.FIELD_COMMISSION,
        Permission.OAM_VISIT_MANAGE,
        Permission.OAM_TICKET_CREATE,
    },
    DefaultRole.COMPLIANCE_OFFICER: {
        Permission.PROJECT_READ,
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_VERIFY,
        Permission.DOCUMENTS_REJECT,
        Permission.COMPLIANCE_READ,
        Permission.COMPLIANCE_RUN,
        Permission.COMPLIANCE_WAIVE,
        Permission.REGULATIONS_READ,
        Permission.RECONCILIATION_READ,
        Permission.PLATFORM_AUDIT_READ,
        Permission.PLATFORM_AUDIT_VERIFY,
    },
    DefaultRole.PROCUREMENT: {
        Permission.SUPPLY_PO_CREATE,
        Permission.SUPPLY_PO_READ,
        Permission.SUPPLY_RECEIVE,
        Permission.SUPPLY_STOCK_ADJUST,
        Permission.ASSETS_REGISTER,
        Permission.ASSETS_BULK_IMPORT,
        Permission.ASSETS_LABEL_PRINT,
        Permission.DOCUMENTS_UPLOAD,
        Permission.DOCUMENTS_READ,
    },
    DefaultRole.TECHNICIAN: {
        Permission.PROJECT_READ,
        Permission.ASSETS_READ,
        Permission.ASSETS_EVENT_RECORD,
        Permission.DOCUMENTS_READ,
        Permission.FIELD_INSPECTION_MANAGE,
        Permission.OAM_VISIT_MANAGE,
        Permission.OAM_TICKET_CREATE,
        Permission.WARRANTY_READ,
    },
    DefaultRole.OAM_MANAGER: {
        Permission.PROJECT_READ,
        Permission.ASSETS_READ,
        Permission.DOCUMENTS_READ,
        Permission.WARRANTY_READ,
        Permission.WARRANTY_MANAGE,
        Permission.WARRANTY_CLAIM,
        Permission.OAM_PLAN_MANAGE,
        Permission.OAM_VISIT_MANAGE,
        Permission.OAM_TICKET_CREATE,
        Permission.OAM_TICKET_ASSIGN,
        Permission.OAM_TICKET_RESOLVE,
        Permission.TELEMETRY_READ,
    },
    DefaultRole.CUSTOMER: {
        # Customer portal: read their own projects only (enforced by ABAC)
        Permission.PROJECT_READ,
        Permission.DOCUMENTS_READ,
        Permission.TELEMETRY_READ,
        Permission.WARRANTY_READ,
        Permission.OAM_TICKET_CREATE,
    },
    DefaultRole.VIEWER: {
        Permission.PROJECT_READ,
        Permission.ASSETS_READ,
        Permission.DOCUMENTS_READ,
        Permission.COMPLIANCE_READ,
        Permission.RECONCILIATION_READ,
        Permission.TELEMETRY_READ,
    },
}


# ── Auth Context ──────────────────────────────────────────────────────────────
@dataclass
class UserContext:
    """
    Loaded once per request from the JWT + DB, passed as a dependency.
    Permissions are resolved from role membership and cached here.
    All authorization decisions use this — no further DB queries.
    """

    user_id: uuid.UUID
    org_id: uuid.UUID
    session_id: uuid.UUID
    email: str
    is_active: bool
    is_platform_admin: bool  # platform-level super-admin
    permissions: set[str]  # resolved from roles
    branch_ids: set[uuid.UUID]  # branches this user belongs to
    assigned_project_ids: set[uuid.UUID]  # explicit project assignments
    plan: str  # organization subscription plan
    totp_verified: bool  # was TOTP verified in this session?

    @property
    def organization_id(self) -> uuid.UUID:
        return self.org_id

    @property
    def id(self) -> uuid.UUID:
        return self.user_id


@dataclass
class AuthzResource:
    """Subject of an authorization check."""

    org_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    owner_id: uuid.UUID | None = None  # user who created the resource
    assignees: set[uuid.UUID] = field(default_factory=set)
    requires_plan: str | None = None  # minimum plan required
    requires_totp: bool = False  # true for high-security operations


@dataclass
class AuthzResult:
    allowed: bool
    reason: str | None = None  # human-readable explanation for denials


# ── Policy Evaluator ──────────────────────────────────────────────────────────
class PolicyEngine:
    """
    Central policy evaluator (ADR-005).
    Pure computation — no database access during evaluation.
    """

    def authorize(
        self,
        user: UserContext,
        permission: str,
        resource: AuthzResource,
        action_context: dict[str, Any] | None = None,
    ) -> AuthzResult:
        # 1. Basic checks
        if not user.is_active:
            return AuthzResult(False, "User account is inactive")

        # 2. Platform admin bypass (platform-level only)
        if user.is_platform_admin and permission == Permission.PLATFORM_ADMIN:
            return AuthzResult(True)

        # 3. Tenant isolation (belt-and-suspenders — RLS is primary)
        if user.org_id != resource.org_id:
            return AuthzResult(False, "Resource belongs to a different organization")

        # 4. RBAC: check permission in resolved set
        if permission not in user.permissions:
            return AuthzResult(False, f"Permission '{permission}' not granted to any of user's roles")

        # 5. ABAC constraints
        abac_result = self._evaluate_abac(user, resource, permission, action_context or {})
        if not abac_result.allowed:
            return abac_result

        # 6. Plan constraint
        if resource.requires_plan is not None:
            if not self._plan_satisfies(user.plan, resource.requires_plan):
                return AuthzResult(
                    False,
                    f"Feature requires plan '{resource.requires_plan}', current plan is '{user.plan}'",
                )

        # 7. TOTP constraint for sensitive operations
        if resource.requires_totp and not user.totp_verified:
            return AuthzResult(False, "This operation requires TOTP verification in the current session")

        return AuthzResult(True)

    def _evaluate_abac(
        self,
        user: UserContext,
        resource: AuthzResource,
        permission: str,
        ctx: dict[str, Any],
    ) -> AuthzResult:
        """Attribute-based constraints evaluated after RBAC grants the permission type."""

        # Branch constraint: users with branch_ids can only see their branches
        if user.branch_ids and resource.branch_id is not None:
            if resource.branch_id not in user.branch_ids:
                return AuthzResult(
                    False,
                    f"User's branch access does not include branch {resource.branch_id}",
                )

        # Assignment constraint: for VIEW operations on projects, check assignment
        # (Owner, PM and platform_admin are exempt — they have no branch restriction)
        # This is opt-in via context flag
        if ctx.get("check_assignment") and resource.assignees:
            if user.user_id not in resource.assignees:
                return AuthzResult(False, "User is not assigned to this project")

        # Ownership constraint: for DELETE/OVERRIDE, may require ownership
        if ctx.get("require_ownership") and resource.owner_id is not None:
            if user.user_id != resource.owner_id and not user.is_platform_admin:
                return AuthzResult(False, "Operation requires ownership of the resource")

        return AuthzResult(True)

    def _plan_satisfies(self, user_plan: str, required_plan: str) -> bool:
        """Simple plan hierarchy check."""
        hierarchy = ["starter", "professional", "enterprise"]
        try:
            return hierarchy.index(user_plan) >= hierarchy.index(required_plan)
        except ValueError:
            return False  # Unknown plan names → deny


# Singleton
policy_engine = PolicyEngine()
