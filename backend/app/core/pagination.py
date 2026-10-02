"""
Solar Operations OS — Cursor-Based Pagination
Consistent pagination across all list endpoints.
"""
from __future__ import annotations

import base64
import json
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

_MAX_LIMIT = 200
_DEFAULT_LIMIT = 50


class PaginationMeta(BaseModel):
    limit: int
    next_cursor: str | None = None
    prev_cursor: str | None = None
    has_next: bool
    has_prev: bool
    total_count: int | None = None  # approximate; only included when requested


class PaginatedResult(BaseModel, Generic[T]):
    data: list[T]
    pagination: PaginationMeta


def encode_cursor(values: dict[str, Any]) -> str:
    """Encode a keyset cursor to an opaque base64 string."""
    raw = json.dumps(values, default=str, sort_keys=True)
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode a cursor back to its keyset values."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode() + b"==")
        return json.loads(raw)
    except Exception as exc:
        from app.core.errors import ValidationError

        raise ValidationError(f"Invalid pagination cursor: {cursor}") from exc


def parse_limit(limit: int | None) -> int:
    """Clamp and default the limit parameter."""
    if limit is None:
        return _DEFAULT_LIMIT
    return max(1, min(limit, _MAX_LIMIT))


def build_paginated_result(
    items: list[T],
    limit: int,
    cursor_fields: list[str],
    has_prev: bool = False,
    total_count: int | None = None,
) -> PaginatedResult[T]:
    """
    Build a PaginatedResult from a list of items.

    items: should contain limit+1 items (to detect has_next); the extra item is trimmed.
    cursor_fields: attribute names on the item used to build the cursor.
    """
    has_next = len(items) > limit
    if has_next:
        items = items[:limit]

    next_cursor = None
    if has_next and items:
        last = items[-1]
        cursor_values = {
            field: getattr(last, field, None) for field in cursor_fields
        }
        next_cursor = encode_cursor(cursor_values)

    prev_cursor = None
    if has_prev and items:
        first = items[0]
        cursor_values = {
            field: getattr(first, field, None) for field in cursor_fields
        }
        prev_cursor = encode_cursor(cursor_values)

    return PaginatedResult(
        data=items,
        pagination=PaginationMeta(
            limit=limit,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_next,
            has_prev=has_prev,
            total_count=total_count,
        ),
    )
