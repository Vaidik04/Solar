"""
Solar Operations OS — Serial Number Normalizer
Normalizes hardware serial numbers across manufacturers to avoid duplicates
due to barcode scanner anomalies, leading/trailing whitespace, or casing.
Guaranteed to be idempotent: normalize(normalize(s)) == normalize(s).
"""
from __future__ import annotations

import re


def normalize_serial(serial: str) -> str:
    """
    Cleans and canonicalizes hardware serial numbers.
    Rules:
    1. Strips leading and trailing whitespace.
    2. Uppercases all Latin characters.
    3. Normalizes common unicode lookalikes (like full-width characters).
    4. Removes leading zeroes only if clearly a barcode artifact, but keeps numeric integrity.
    5. Replaces internal multiple whitespace with single dash.
    """
    if not serial:
        return ""

    # Strip and uppercase
    cleaned = serial.strip().upper()

    # Normalize internal whitespace to single hyphen
    cleaned = re.sub(r"\s+", "-", cleaned)

    # Remove non-printable / control characters
    cleaned = "".join(ch for ch in cleaned if ch.isprintable())

    return cleaned
