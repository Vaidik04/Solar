"""
Phase 11 Acceptance Tests:
1. Connector framework parses mock format and real Sungrow Modbus TCP register blocks.
2. Continuous aggregate calculations: Performance Ratio (PR) & Capacity Utilization Factor (CUF).
3. Anomaly detection: Inverter clipping detection and Zero-generation during daylight alarm.
"""
from app.modules.telemetry_data.analytics import (
    MockInverterAdapter,
    SungrowModbusAdapter,
    telemetry_analytics,
)


def test_telemetry_connectors_mock_and_sungrow_modbus():
    """
    Acceptance: Connector framework with at least one mock adapter and one real-format adapter.
    """
    # 1. Mock adapter
    mock_adapter = MockInverterAdapter()
    r_mock = mock_adapter.parse_payload({"kw": 50.0, "kwh": 300.0, "temp": 38.0})
    assert r_mock.active_power_kw == 50.0
    assert r_mock.daily_energy_kwh == 300.0

    # 2. Sungrow real Modbus register adapter
    sungrow_adapter = SungrowModbusAdapter()
    modbus_payload = {
        "timestamp": "2026-03-15T13:30:00Z",
        "irradiance_w_per_m2": 890.0,
        "registers": {
            5016: 1050,  # 105.0 kW active power
            5003: 4520,  # 452.0 kWh daily generation
            5011: 6725,  # 672.5 Vdc
            5012: 1560,  # 156.0 Idc
            5007: 485,   # 48.5 °C internal temp
        },
    }
    r_sungrow = sungrow_adapter.parse_payload(modbus_payload)
    assert r_sungrow.active_power_kw == 105.0
    assert r_sungrow.daily_energy_kwh == 452.0
    assert r_sungrow.dc_voltage_v == 672.5
    assert r_sungrow.dc_current_a == 156.0
    assert r_sungrow.inverter_temp_c == 48.5


def test_pr_and_cuf_analytics_calculations():
    """
    Acceptance: Performance analytics PR and CUF formulas.
    """
    # 100 kW plant, 5.5 kWh/m2 insolation, generated 450 kWh
    # Theoretical = 100 * 5.5 = 550 kWh. PR = 450/550 * 100 = 81.82%
    pr = telemetry_analytics.calculate_performance_ratio(
        actual_kwh=450.0,
        installed_capacity_kw=100.0,
        poa_irradiance_kwh_per_m2=5.5,
    )
    assert pr == 81.82

    # 100 kW plant, 24 hours, generated 480 kWh.
    # CUF = 480 / (100 * 24) * 100 = 20.0%
    cuf = telemetry_analytics.calculate_cuf(
        total_kwh=480.0,
        rated_capacity_kw=100.0,
        period_days=1,
    )
    assert cuf == 20.0


def test_inverter_clipping_and_zero_daylight_anomalies():
    """
    Acceptance: Anomaly detection triggers for clipping and zero daylight generation.
    """
    sungrow = SungrowModbusAdapter()

    # Case A: Inverter Clipping (110 kW inverter running at 109.5 kW under 950 W/m2 sun)
    clipping_payload = {
        "irradiance_w_per_m2": 950.0,
        "registers": {5016: 1095, 5003: 5000, 5011: 7000, 5012: 1560, 5007: 520},
    }
    r_clip = sungrow.parse_payload(clipping_payload)
    anomalies_clip = telemetry_analytics.detect_anomalies(r_clip, rated_capacity_kw=110.0)
    assert "INVERTER_CLIPPING_DETECTED" in anomalies_clip

    # Case B: Zero Generation during midday sun (tripped breaker or blown fuse)
    zero_payload = {
        "irradiance_w_per_m2": 750.0,
        "registers": {5016: 0, 5003: 0, 5011: 0, 5012: 0, 5007: 300},
    }
    r_zero = sungrow.parse_payload(zero_payload)
    anomalies_zero = telemetry_analytics.detect_anomalies(r_zero, rated_capacity_kw=110.0)
    assert "ZERO_GENERATION_IN_DAYLIGHT" in anomalies_zero
