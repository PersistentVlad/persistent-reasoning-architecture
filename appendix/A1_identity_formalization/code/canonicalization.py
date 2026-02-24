# persistent-reasoning-architecture/appendix/A1_identity_formalization/code/canonicalization.py

# IMPORTANT:
# This canonicalization assumes tree-like deterministic structures.
# Graphs with cycles or unordered references require external normalization.

from __future__ import annotations

from typing import Any, Mapping, Sequence
import json


class CanonicalizationError(ValueError):
    """Raised when an object cannot be canonicalized deterministically."""


def _is_primitive(x: Any) -> bool:
    return x is None or isinstance(x, (bool, int, float, str))


def _normalize_number(x: Any) -> Any:
    # Keep ints as ints. Normalize floats to a stable string representation.
    # NOTE: for identity anchoring, "0.1" vs "0.10" should not matter.
    if isinstance(x, bool):  # bool is a subclass of int
        return x
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        # Use JSON-like stable representation. Avoid scientific notation surprises.
        # 17 sig digits is enough for round-trip of IEEE-754 double.
        return float(f"{x:.17g}")
    return x


def canonicalize_payload(obj: Any) -> str:
    """
    Deterministically canonicalize an object to a JSON string.

    Allowed input types:
    - primitives: None, bool, int, float, str
    - mappings with string keys
    - sequences (list/tuple)
    - sets/frozensets (converted to sorted lists)
    - objects with __dict__ are NOT accepted (must be explicitly mapped)

    Rationale:
    - identity anchoring must be deterministic and explicit
    - implicit object serialization is a hidden semantics leak
    """
    normalized = _normalize(obj)
    try:
        # separators removes whitespace; sort_keys ensures stable key ordering.
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except TypeError as e:
        raise CanonicalizationError(f"cannot canonicalize: {e}") from e


def _normalize(obj: Any) -> Any:
    if _is_primitive(obj):
        return _normalize_number(obj)

    # Mapping
    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise CanonicalizationError("mapping keys must be strings")
            out[k] = _normalize(v)
        # key ordering will be handled by json.dumps(sort_keys=True)
        return out

    # Sequence (but not str/bytes which are primitives-ish)
    if isinstance(obj, (list, tuple)):
        return [_normalize(x) for x in obj]

    # Set-like: order is undefined, so we must sort.
    if isinstance(obj, (set, frozenset)):
        items = [_normalize(x) for x in obj]
        # Items might be dicts/lists; convert to canonical strings for sorting stability.
        sortable = [canonicalize_payload(x) for x in items]
        sortable.sort()
        return sortable  # already canonical strings

    # Bytes are not allowed (force explicit encoding upstream)
    if isinstance(obj, (bytes, bytearray, memoryview)):
        raise CanonicalizationError("bytes-like objects are not allowed; encode explicitly")

    # Anything else is rejected to avoid hidden/accidental semantics.
    raise CanonicalizationError(
        f"unsupported type for canonicalization: {type(obj).__name__}. "
        "Provide an explicit Mapping/Sequence representation."
    )
