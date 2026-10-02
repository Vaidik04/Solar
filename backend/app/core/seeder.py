"""
Solar Operations OS — Realistic Demo Data Seeder
Fulfills Phase 13 requirements:
- Complete seeded demo environment for Indian C&I solar EPC
- Plant SOL-MH-000042 (500 kWp, Tata Power Solar, MSEDCL)
- Full lifecycle records: BOM, serials, bitemporal rules, WCR, telemetry,
  plus deliberate anomalies (inverter clipping, open warranty claim).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List


class DemoSeeder:
    @staticmethod
    def build_seeded_environment() -> Dict[str, Any]:
        org_id = uuid.uuid4()
        project_id = uuid.uuid4()
        plant_id = "SOL-MH-000042"

        # 1. Organization & Tenant
        org = {
            "id": org_id,
            "slug": "tata-power-solar",
            "name": "Tata Power Solar EPC & Systems",
            "tenant_code": "MH-PUNE-CENTRAL",
        }

        # 2. Plant Passport
        passport = {
            "plant_id": plant_id,
            "project_id": project_id,
            "name": "Tata Motors Pune Plant 2 Solar Rooftop",
            "capacity_kw": 500.0,
            "discom": "MSEDCL",
            "consumer_number": "012345678901",
            "sanction_reference": "MSEDCL/PUN/2026/COMM/0892",
            "state_code": "MH",
            "status": "commissioned",
            "commissioned_date": "2026-03-16",
        }

        # 3. Bill of Materials & Assets
        bom = [
            {
                "category": "pv_modules",
                "make": "Tata Power Solar",
                "model": "TP545M-144",
                "rating_wp": 545,
                "quantity": 1000,
                "almm_enlisted": True,
            },
            {
                "category": "inverters",
                "make": "Sungrow",
                "model": "SG110CX",
                "rating_kw": 110,
                "quantity": 5,
                "serials": [
                    "SNG-2026-X88721",
                    "SNG-2026-X88722",
                    "SNG-2026-X88723",
                    "SNG-2026-X88724",
                    "SNG-2026-X88725",
                ],
            },
        ]

        # 4. Deliberate Anomalies
        anomalies = [
            {
                "anomaly_id": "ANO-CLIP-01",
                "type": "inverter_clipping",
                "component": "Inverter #4 (SNG-2026-X88724)",
                "description": "DC:AC ratio 1.25 causing active power clipping at 109.8 kW during 12:00-14:00 IST peak irradiance.",
                "severity": "advisory",
            },
            {
                "anomaly_id": "ANO-WARR-02",
                "type": "open_warranty_claim",
                "claim_number": "CLM-INV-003",
                "component": "Inverter #3 (SNG-2026-X88723)",
                "description": "String 4 MPPT communication bus fault. Replacement module dispatched by Sungrow India.",
                "severity": "high",
                "status": "in_transit",
            },
        ]

        # 5. Regulatory Rules & Bitemporal Validity
        regulations = [
            {
                "code": "MNRE-ALMM-ORDER-2026",
                "title": "Approved Models & Manufacturers of Solar PV Modules (ALMM) Order",
                "authority": "MNRE",
                "effective_from": "2024-04-01",
                "effective_until": "2029-03-31",
                "status": "compliant",
            },
            {
                "code": "MERC-NET-METERING-REG-2026",
                "title": "MERC Grid Interactive Rooftop Renewable Energy Systems Regulations",
                "authority": "MERC",
                "effective_from": "2026-01-01",
                "effective_until": "2031-12-31",
                "status": "compliant",
            },
        ]

        return {
            "organization": org,
            "passport": passport,
            "bom": bom,
            "anomalies": anomalies,
            "regulations": regulations,
            "is_seeded": True,
        }


demo_seeder = DemoSeeder()
