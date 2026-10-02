import uuid
from datetime import datetime, timezone
import pytest

from app.core.security import sign_qr_token, verify_qr_token
from app.modules.assets.models import AssetCategory, AssetEventType, AssetStatus
from app.modules.assets.normalizer import normalize_serial
from app.modules.assets.events import AssetAllocated, AssetInstalled, AssetRegistered
from app.modules.engineering.models import BOMCategory, BOMStatus, DesignStatus, SystemType


def test_serial_normalizer_idempotence():
    raw_serials = [
        "  tp-550w-2026-000123  ",
        "INV_SUNGROW_SG100CX_987",
        "JKM-540M-72HL4-V",
        "  SN  123 456  ",
    ]
    for s in raw_serials:
        norm1 = normalize_serial(s)
        norm2 = normalize_serial(norm1)
        assert norm1 == norm2  # Idempotency rule
        assert norm1 == norm1.upper()
        assert not norm1.startswith(" ")
        assert not norm1.endswith(" ")


def test_qr_token_signing_roundtrip():
    asset_id = uuid.uuid4()
    org_id = uuid.uuid4()

    token = sign_qr_token(asset_id, org_id)
    assert isinstance(token, str)

    extracted = verify_qr_token(token)
    assert extracted is not None
    ext_asset_id, ext_org_id = extracted
    assert ext_asset_id == asset_id
    assert ext_org_id == org_id


def test_asset_domain_events():
    org_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    proj_id = uuid.uuid4()

    reg_event = AssetRegistered(
        organization_id=org_id,
        asset_id=asset_id,
        serial_number="TP550-00123",
        category="solar_panel",
        asset_type_id=uuid.uuid4(),
    )
    payload = reg_event.to_dict()
    assert payload["serial_number"] == "TP550-00123"
    assert reg_event.event_type == "AssetRegistered"

    alloc_event = AssetAllocated(
        organization_id=org_id,
        asset_id=asset_id,
        project_id=proj_id,
        plant_id="SOL-MH-000001",
    )
    assert alloc_event.event_type == "AssetAllocated"
    assert alloc_event.plant_id == "SOL-MH-000001"

    install_event = AssetInstalled(
        organization_id=org_id,
        asset_id=asset_id,
        project_id=proj_id,
        plant_id="SOL-MH-000001",
        location_tag="Roof-South-String-1",
    )
    assert install_event.location_tag == "Roof-South-String-1"


def test_engineering_enums():
    assert SystemType.GRID_TIED == "grid_tied"
    assert BOMCategory.SOLAR_MODULE == "solar_module"
    assert BOMCategory.INVERTER == "inverter"
    assert BOMStatus.FINALIZED == "finalized"
    assert DesignStatus.APPROVED == "approved"
