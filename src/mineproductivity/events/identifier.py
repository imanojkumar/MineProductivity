"""``EventID``: a globally unique, time-sortable identifier for one event instance."""

from __future__ import annotations

import dataclasses
import secrets
import time
from typing import Self

from mineproductivity.core import BaseIdentifier

__all__ = ["EventID"]

_CROCKFORD_BASE32_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_CHAR_LENGTH = 26
_TIMESTAMP_BYTES = 6
_RANDOMNESS_BYTES = 10


def _generate_ulid(*, _timestamp_ms: int | None = None) -> str:
    """Generate a 26-character, lexicographically time-sortable identifier
    in the shape of a ULID (48-bit millisecond timestamp + 80 bits of
    cryptographically strong randomness, Crockford Base32 encoded).

    ``_timestamp_ms`` is an injectable-for-testing seam; production
    callers never pass it.
    """
    timestamp_ms = _timestamp_ms if _timestamp_ms is not None else time.time_ns() // 1_000_000
    timestamp_bytes = timestamp_ms.to_bytes(_TIMESTAMP_BYTES, byteorder="big")
    randomness = secrets.token_bytes(_RANDOMNESS_BYTES)
    return _encode_crockford_base32(timestamp_bytes + randomness)


def _encode_crockford_base32(data: bytes) -> str:
    value = int.from_bytes(data, byteorder="big")
    characters: list[str] = []
    for _ in range(_ULID_CHAR_LENGTH):
        value, remainder = divmod(value, 32)
        characters.append(_CROCKFORD_BASE32_ALPHABET[remainder])
    return "".join(reversed(characters))


@dataclasses.dataclass(frozen=True, slots=True)
class EventID(BaseIdentifier[str]):
    """Globally unique identifier for one event instance.

    Generated values are 26-character, Crockford Base32-encoded,
    time-sortable identifiers (ULID-shaped): the leading characters
    encode a millisecond timestamp, so ``EventID`` values generated later
    sort lexicographically after ones generated earlier -- a property
    :class:`~mineproductivity.events.store.EventStore` range-scans can
    rely on. A caller may also construct an ``EventID`` directly from any
    string (e.g. ``EventID(value="csv-0001")``) when a source system
    supplies its own stable identifier.

    Examples
    --------
    >>> first = EventID.generate()
    >>> second = EventID.generate()
    >>> first != second
    True
    >>> len(first.value)
    26
    """

    @classmethod
    def generate(cls) -> Self:
        """Return a new, randomly generated, time-sortable identifier."""
        return cls(value=_generate_ulid())
