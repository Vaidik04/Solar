import pytest
from app.core.plant_id import format_plant_id, parse_plant_id


def test_format_plant_id():
    pid1 = format_plant_id("MH", 1)
    assert pid1 == "SOL-MH-000001"

    pid2 = format_plant_id("ka", 124)
    assert pid2 == "SOL-KA-000124"

    pid3 = format_plant_id("GJ", 999999)
    assert pid3 == "SOL-GJ-999999"


def test_parse_valid_plant_id():
    parsed = parse_plant_id("SOL-MH-000124")
    assert parsed is not None
    state_code, seq_num = parsed
    assert state_code == "MH"
    assert seq_num == 124


def test_parse_invalid_plant_id():
    assert parse_plant_id("INVALID") is None
    assert parse_plant_id("SOL-M-000124") is None  # 1-letter state code
    assert parse_plant_id("SOL-MHH-000124") is None  # 3-letter state code
    assert parse_plant_id("SOL-MH-124") is None  # 3-digit sequence
    assert parse_plant_id("SOL-12-000124") is None  # Numeric state code
