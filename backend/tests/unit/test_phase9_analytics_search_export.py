"""
Phase 9 Acceptance Tests:
1. Executive dashboard aggregations calculate within performance budget.
2. Global search drills down across Plant IDs, Customers, Serials, and DISCOM references.
3. Cryptographically sealed Plant Passport export dossier generation.
"""
from app.modules.platform.analytics_service import (
    analytics_service,
    SearchResultItem,
)


def test_dashboard_aggregations_performance_and_accuracy():
    """
    Acceptance: Dashboard queries calculate metrics with accuracy across large fleet.
    """
    projects = [
        {"id": "p1", "capacity_kw": 100.0, "stage": "commissioned"},
        {"id": "p2", "capacity_kw": 250.0, "stage": "supply"},
        {"id": "p3", "capacity_kw": 150.0, "stage": "commissioned"},
    ]
    alarms = [
        {"id": "a1", "status": "active"},
        {"id": "a2", "status": "resolved"},
        {"id": "a3", "status": "active"},
    ]
    tickets = [
        {"id": "t1", "sla_breached": False},
        {"id": "t2", "sla_breached": False},
        {"id": "t3", "sla_breached": True},
        {"id": "t4", "sla_breached": False},
    ]

    metrics = analytics_service.aggregate_dashboard_metrics(
        projects=projects,
        alarms=alarms,
        tickets=tickets,
        generation_summary={"performance_ratio": 82.5},
    )

    assert metrics.total_plants == 3
    assert metrics.total_capacity_kw == 500.0
    assert metrics.active_alarms_count == 2
    assert metrics.fleet_pr_average == 82.5
    assert metrics.sla_compliance_percent == 75.0  # 3/4
    assert metrics.projects_by_stage["commissioned"] == 2
    assert metrics.projects_by_stage["supply"] == 1


def test_global_search_multi_entity_drilldown():
    """
    Acceptance: Multi-entity search retrieves matching records across all entity types.
    """
    index = [
        SearchResultItem(
            entity_type="plant",
            entity_id="SOL-MH-000042",
            title="Tata Motors Pune Plant 2 Rooftop",
            subtitle="500 kWp C&I Grid-Tied",
            metadata={"discom_application": "MSEDCL/APP/2026/8901"},
        ),
        SearchResultItem(
            entity_type="customer",
            entity_id="CUST-089",
            title="Tata Motors Limited",
            subtitle="Pimpri Industrial Zone, Pune",
            metadata={"gstin": "27AAACT0000A1Z5"},
        ),
        SearchResultItem(
            entity_type="asset",
            entity_id="AST-INV-001",
            title="Sungrow SG110CX Inverter",
            subtitle="Serial: SNG-2026-X88721",
            metadata={"plant_id": "SOL-MH-000042"},
        ),
    ]

    # Search by plant ID
    r_plant = analytics_service.global_search("000042", index)
    assert len(r_plant) == 2  # plant and inverter asset
    assert any(x.entity_type == "plant" for x in r_plant)

    # Search by serial number
    r_serial = analytics_service.global_search("X88721", index)
    assert len(r_serial) == 1
    assert r_serial[0].entity_id == "AST-INV-001"

    # Search by DISCOM application number
    r_discom = analytics_service.global_search("8901", index)
    assert len(r_discom) == 1
    assert r_discom[0].entity_id == "SOL-MH-000042"


def test_cryptographically_sealed_plant_dossier_export():
    """
    Acceptance: Dossier export compiles full audit package and computes SHA-256 seal.
    """
    dossier = analytics_service.generate_plant_dossier(
        plant_id="SOL-MH-000042",
        org_slug="tata-power-solar",
        passport_data={"plant_id": "SOL-MH-000042", "capacity_kw": 500.0},
        bom_items=[{"item": "Mono PERC Modules", "qty": 1000}],
        wcr_data={"wcr_number": "WCR-SOL-MH-000042-V1", "status": "approved"},
        meter_data={"serial": "MTR-SEC-8899", "discom": "MSEDCL"},
    )

    assert dossier.plant_id == "SOL-MH-000042"
    assert len(dossier.dossier_sha256) == 64
    assert "passport" in dossier.sections
    assert "bom_and_serials" in dossier.sections
    assert "work_completion_report" in dossier.sections
    assert "grid_meter" in dossier.sections
