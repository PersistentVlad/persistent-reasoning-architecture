# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/src/transforms.py
"""
Transformations for Appendix A2 — Hieroglyphic Calculator.

Key principle:
- Transformations are whitelisted, explicit, and deterministic.
- They do not "solve" problems. They only apply local rewrite steps.
- Every transform produces a *candidate* state, then invariants decide admissibility.

Payload format (intentionally tiny):
An expression is a nested dict:
- {"kind": "const", "value": 2}
- {"kind": "add", "args": [expr, expr, ...]}
- {"kind": "mul", "args": [expr, expr, ...]}

This is an academic boundary case.
Real systems should delegate arithmetic to dedicated tools;
A2 exists to prove the invariant-preservation boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Protocol, Tuple

from .state import make_candidate_state


# ----------------------------
# Payload helpers
# ----------------------------

def _is_const(expr: Mapping[str, Any]) -> bool:
    return expr.get("kind") == "const" and isinstance(expr.get("value"), int)

def _const(value: int) -> Dict[str, Any]:
    return {"kind": "const", "value": int(value)}

def _is_add(expr: Mapping[str, Any]) -> bool:
    return expr.get("kind") == "add" and isinstance(expr.get("args"), list)

def _is_mul(expr: Mapping[str, Any]) -> bool:
    return expr.get("kind") == "mul" and isinstance(expr.get("args"), list)

def _args(expr: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    return list(expr.get("args", []))

def _rebuild(kind: str, args: List[Mapping[str, Any]]) -> Dict[str, Any]:
    return {"kind": kind, "args": [dict(a) for a in args]}

def _flatten(kind: str, expr: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Flatten nested associative nodes:
    add(add(a,b),c) -> add(a,b,c)
    mul(mul(a,b),c) -> mul(a,b,c)
    """
    if expr.get("kind") != kind:
        return expr
    flat: List[Mapping[str, Any]] = []
    for a in _args(expr):
        if a.get("kind") == kind:
            flat.extend(_args(a))
        else:
            flat.append(a)
    return _rebuild(kind, flat)

def _sort_consts_last(args: List[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    # Deterministic ordering rule: non-consts first, consts last, preserve relative order within groups.
    non_consts = [a for a in args if not _is_const(a)]
    consts = [a for a in args if _is_const(a)]
    return non_consts + consts


# ----------------------------
# Transform interface
# ----------------------------

class Transform(Protocol):
    @property
    def transform_id(self) -> str:
        ...

    def apply(self, payload: Mapping[str, Any]) -> Tuple[Mapping[str, Any], str]:
        """
        Apply rewrite and return (new_payload, note).
        Must be deterministic, side-effect free.
        """
        ...


@dataclass(frozen=True)
class TransformSpec:
    transform_id: str
    description: str


# ----------------------------
# Concrete transforms (whitelisted)
# ----------------------------

class FlattenAssociative:
    """
    Flatten nested add/mul nodes.
    """
    def __init__(self, kind: str):
        if kind not in ("add", "mul"):
            raise ValueError("kind must be 'add' or 'mul'")
        self._kind = kind

    @property
    def transform_id(self) -> str:
        return f"flatten:{self._kind}"

    def apply(self, payload: Mapping[str, Any]) -> Tuple[Mapping[str, Any], str]:
        before = payload
        after = _flatten(self._kind, before)
        note = "no-op" if after == before else f"flattened {self._kind}"
        return after, note


class CombineConstantsAdd:
    """
    add(..., const a, const b, ...) -> add(..., const (a+b), ...)
    Only combines if there are >=2 constants.
    """
    @property
    def transform_id(self) -> str:
        return "combine_consts:add"

    def apply(self, payload: Mapping[str, Any]) -> Tuple[Mapping[str, Any], str]:
        if not _is_add(payload):
            return payload, "no-op (not add)"
        args = _args(payload)
        consts = [a for a in args if _is_const(a)]
        if len(consts) < 2:
            return payload, "no-op (need >=2 consts)"
        non_consts = [a for a in args if not _is_const(a)]
        total = sum(int(a["value"]) for a in consts)
        new_args = non_consts + [_const(total)]
        if len(new_args) == 1:
            return new_args[0], f"combined {len(consts)} consts into {total} (collapsed)"
        new_payload = _rebuild("add", new_args)
        return new_payload, f"combined {len(consts)} consts into {total}"


class CombineConstantsMul:
    """
    mul(..., const a, const b, ...) -> mul(..., const (a*b), ...)
    Only combines if there are >=2 constants.
    """
    @property
    def transform_id(self) -> str:
        return "combine_consts:mul"

    def apply(self, payload: Mapping[str, Any]) -> Tuple[Mapping[str, Any], str]:
        if not _is_mul(payload):
            return payload, "no-op (not mul)"
        args = _args(payload)
        consts = [a for a in args if _is_const(a)]
        if len(consts) < 2:
            return payload, "no-op (need >=2 consts)"
        non_consts = [a for a in args if not _is_const(a)]
        prod = 1
        for a in consts:
            prod *= int(a["value"])
        new_args = non_consts + [_const(prod)]
        if len(new_args) == 1:
            return new_args[0], f"combined {len(consts)} consts into {prod} (collapsed)"
        new_payload = _rebuild("mul", new_args)
        return new_payload, f"combined {len(consts)} consts into {prod}"


class NormalizeOrdering:
    """
    Deterministic ordering normalization:
    - For add/mul, move constants to the end (stable within groups).
    This is not "canonical math". It's a minimal determinism device.
    """
    @property
    def transform_id(self) -> str:
        return "normalize:consts_last"

    def apply(self, payload: Mapping[str, Any]) -> Tuple[Mapping[str, Any], str]:
        kind = payload.get("kind")
        if kind not in ("add", "mul"):
            return payload, "no-op (not add/mul)"
        args = _args(payload)
        new_args = _sort_consts_last(args)
        new_payload = _rebuild(kind, new_args)
        note = "no-op" if new_payload == payload else "moved consts last"
        return new_payload, note


# ----------------------------
# Orchestrated application helper
# ----------------------------

def apply_transform_to_candidate(
    *,
    transform: Transform,
    scope: str,
    payload: Mapping[str, Any],
    parent_id: str,
) -> Dict[str, Any]:
    """
    Apply a transform to payload and return a candidate state dict (no state_id).
    Invariants + commit gate decide whether this becomes a committed state.
    """
    new_payload, note = transform.apply(payload)
    return make_candidate_state(
        scope=scope,
        payload=new_payload,
        parent_id=parent_id,
        transform_id=transform.transform_id,
        note=note,
    )


def list_default_transforms() -> List[TransformSpec]:
    """
    Human-facing list of default transforms (for docs / UI), not used by logic.
    """
    return [
        TransformSpec("flatten:add", "Flatten nested additions: add(add(a,b),c) -> add(a,b,c)"),
        TransformSpec("flatten:mul", "Flatten nested multiplications: mul(mul(a,b),c) -> mul(a,b,c)"),
        TransformSpec("normalize:consts_last", "Move constants to the end of add/mul argument lists"),
        TransformSpec("combine_consts:add", "Combine multiple integer constants inside add"),
        TransformSpec("combine_consts:mul", "Combine multiple integer constants inside mul"),
    ]