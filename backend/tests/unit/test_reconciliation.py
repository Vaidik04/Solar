"""
Unit tests for Reconciliation Engine & Snapshot Hashing
"""
import uuid
import pytest

from app.modules.reconciliation.service import reconciliation_service
from app.modules.reconciliation.models import ComparisonResult, ReconciliationScope
from app.modules.reconciliation.public import (
    ReconciliationRunCreate,
    ResolveDiscrepancyRequest,
)


def test_snapshot_sha256_cryptographic_integrity():
    payload_a = [{"category": "solar_panel", "make": "Waaree", "quantity": 100}]
    payload_b = [{"category": "solar_panel", "make": "Waaree", "quantity": 100}]
    payload_c = [{"category": "solar_panel", "make": "Waaree", "quantity": 101}]

    hash_a = reconciliation_service._compute_sha256(payload_a)
    hash_b = reconciliation_service._compute_sha256(payload_b)
    hash_c = reconciliation_service._compute_sha256(payload_c)

    assert len(hash_a) == 64
    assert hash_a == hash_b  # Deterministic
    assert hash_a != hash_c  # Tamper evidence


def test_reconciliation_dtos():
    proj_id = uuid.uuid4()
    req = ReconciliationRunCreate(
        project_id=proj_id,
        scope=ReconciliationScope.BOM_VS_INSTALLED,
    )
    assert req.scope == "bom_vs_installed"

    resolve = ResolveDiscrepancyRequest(
        resolution_notes="Authorized panel substitution approved by client",
        override_result=ComparisonResult.WAIVED,
    )
    assert resolve.override_result == "waived"
