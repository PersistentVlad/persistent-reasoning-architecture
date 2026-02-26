# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/src/invariants.py

"""
Invariant layer for Appendix A2 — Hieroglyphic Calculator.

This module defines:
- Invariant protocol / interface
- Registry for invariants
- A small set of intentionally boring, structural invariants

Important:
- These invariants are NOT "constraints to be solved".
- They are admissibility guards for transformations.
- They do not compute the "right answer".
- They only reject inadmissible state transitions.

The rest of A2 (state model, transformations, lineage) can treat this as a pure gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol, Sequence, Tuple


# ----------------------------
# Exceptions / Results
# ----------------------------

@dataclass(frozen=True)
class InvariantResult:
    """Result of checking a single invariant."""
    ok: bool
    name: str
    reason: str = ""
    details: Optional[Mapping[str, Any]] = None


class InvariantViolation(RuntimeError):
    """Raised when one or more invariants are violated."""
    def __init__(self, failures: Sequence[InvariantResult]):
        self.failures = list(failures)
        msg = "Invariant violation(s): " + "; ".join(
            f"{f.name}: {f.reason or 'failed'}" for f in self.failures
        )
        super().__init__(msg)


# ----------------------------
# Invariant protocol
# ----------------------------

class Invariant(Protocol):
    """
    Invariant interface.

    Invariants are checked against a candidate state BEFORE it can be appended to lineage.
    The invariant must be deterministic and side-effect free.
    """
    @property
    def name(self) -> str:
        ...

    def check(self, state: Mapping[str, Any]) -> InvariantResult:
        ...


# ----------------------------
# Registry / helpers
# ----------------------------

class InvariantRegistry:
    """
    Holds a set of invariants to be enforced as an admissibility envelope.

    Note: This registry does not decide *what to do* when invariants fail.
    It only reports failures. A commit gate decides policy.
    """
    def __init__(self, invariants: Optional[Iterable[Invariant]] = None):
        self._invariants: List[Invariant] = list(invariants) if invariants else []

    def add(self, invariant: Invariant) -> None:
        self._invariants.append(invariant)

    def list_names(self) -> List[str]:
        return [inv.name for inv in self._invariants]

    def check_all(self, state: Mapping[str, Any]) -> Tuple[bool, List[InvariantResult]]:
        results = [inv.check(state) for inv in self._invariants]
        failures = [r for r in results if not r.ok]
        return (len(failures) == 0, failures)


def require_all_invariants(registry: InvariantRegistry, state: Mapping[str, Any]) -> None:
    ok, failures = registry.check_all(state)
    if not ok:
        raise InvariantViolation(failures)


# ----------------------------
# Minimal “boring” invariants
# ----------------------------

class NoNaNNoInfInvariant:
    """
    Guards against numeric drift artifacts: NaN / Inf values appearing in the state payload.

    This is intentionally shallow:
    - It does not validate correctness.
    - It only rejects "poisoned" numeric states that make continuity meaningless.
    """
    @property
    def name(self) -> str:
        return "no_nan_no_inf"

    def check(self, state: Mapping[str, Any]) -> InvariantResult:
        payload = state.get("payload", None)

        def is_bad_number(x: Any) -> bool:
            # Avoid importing math unless needed; keep it simple.
            try:
                # float('nan') is not equal to itself
                if isinstance(x, float) and (x != x):
                    return True
                # inf checks
                if isinstance(x, float) and (x in (float("inf"), float("-inf"))):
                    return True
            except Exception:
                return False
            return False

        bad_paths: List[str] = []

        def walk(obj: Any, path: str) -> None:
            if is_bad_number(obj):
                bad_paths.append(path)
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk(v, f"{path}.{k}" if path else str(k))
            elif isinstance(obj, (list, tuple)):
                for i, v in enumerate(obj):
                    walk(v, f"{path}[{i}]")

        walk(payload, "payload")

        if bad_paths:
            return InvariantResult(
                ok=False,
                name=self.name,
                reason="Payload contains NaN/Inf",
                details={"bad_paths": bad_paths[:50]},  # cap to keep logs sane
            )
        return InvariantResult(ok=True, name=self.name)


class ScopeBoundInvariant:
    """
    Ensures the state carries an explicit scope marker.

    This protects A2 from being misread as a general solver:
    every committed state must declare its domain boundary.
    """
    @property
    def name(self) -> str:
        return "scope_bound"

    def check(self, state: Mapping[str, Any]) -> InvariantResult:
        scope = state.get("scope", None)
        if not scope or not isinstance(scope, str):
            return InvariantResult(
                ok=False,
                name=self.name,
                reason="Missing or invalid scope",
                details={"expected": "non-empty string", "found": repr(scope)},
            )
        # Optional: enforce an "A2:" prefix to make scope explicit and non-accidental.
        if not scope.startswith("A2:"):
            return InvariantResult(
                ok=False,
                name=self.name,
                reason="Scope must start with 'A2:'",
                details={"scope": scope},
            )
        return InvariantResult(ok=True, name=self.name)


class ProvenanceRequiredInvariant:
    """
    Requires minimal provenance metadata for each committed state.

    This is not about truth.
    It's about auditability of how a state entered lineage:
    - what transformation produced it
    - what parent it came from
    """
    @property
    def name(self) -> str:
        return "provenance_required"

    def check(self, state: Mapping[str, Any]) -> InvariantResult:
        meta = state.get("meta", None)
        if not isinstance(meta, dict):
            return InvariantResult(
                ok=False,
                name=self.name,
                reason="Missing meta dict",
                details={"expected": "meta: dict", "found": repr(meta)},
            )

        required = ["parent_id", "transform_id"]
        missing = [k for k in required if not meta.get(k)]
        if missing:
            return InvariantResult(
                ok=False,
                name=self.name,
                reason="Missing provenance fields",
                details={"missing": missing},
            )

        # Parent id must be a stable string handle in this toy model.
        if not isinstance(meta.get("parent_id"), str):
            return InvariantResult(
                ok=False,
                name=self.name,
                reason="parent_id must be a string",
                details={"parent_id": repr(meta.get("parent_id"))},
            )

        if not isinstance(meta.get("transform_id"), str):
            return InvariantResult(
                ok=False,
                name=self.name,
                reason="transform_id must be a string",
                details={"transform_id": repr(meta.get("transform_id"))},
            )

        return InvariantResult(ok=True, name=self.name)