"""
Solar Operations OS — Digital Plant Passport ID Allocator
Generates unique, uniform identifiers: SOL-{STATE}-{SEQUENCE:06d}
Example: SOL-MH-000124, SOL-GJ-000002

Guarantee:
- Gapless sequential numbers per organization
- Collision-free across concurrent worker threads and processes
"""
from __future__ import annotations

import re
import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Organization

PLANT_ID_PATTERN = re.compile(r"^SOL-([A-Z]{2})-([0-9]{6})$")


def format_plant_id(state_code: str, sequence_num: int) -> str:
    """Formats state code and sequential integer into standard Plant ID."""
    clean_state = state_code.strip().upper()[:2]
    return f"SOL-{clean_state}-{sequence_num:06d}"


def parse_plant_id(plant_id: str) -> Optional[tuple[str, int]]:
    """Parses and validates a Plant ID. Returns (state_code, sequence_num) or None."""
    match = PLANT_ID_PATTERN.match(plant_id.strip().upper())
    if not match:
        return None
    state_code = match.group(1)
    sequence_num = int(match.group(2))
    return state_code, sequence_num


async def allocate_plant_id(
    session: AsyncSession,
    organization_id: uuid.UUID,
    state_code: Optional[str] = None,
) -> str:
    """
    Allocates the next sequential Plant ID for an organization.
    Uses row-level locking on the Organization row (SELECT FOR UPDATE)
    to guarantee atomic increment without race conditions or duplicate IDs.
    """
    stmt = (
        select(Organization)
        .where(Organization.id == organization_id)
        .with_for_update()
    )
    result = await session.execute(stmt)
    org = result.scalar_one_or_none()
    if org is None:
        raise ValueError(f"Organization {organization_id} not found for Plant ID allocation")

    # Increment sequence counter
    next_seq = org.plant_id_sequence + 1
    org.plant_id_sequence = next_seq

    actual_state = state_code.upper() if state_code else org.state_code.upper()
    return format_plant_id(actual_state, next_seq)
