# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/src/checker.py

"""
Invariant checker for Appendix A2 — Hieroglyphic Calculator.

This module is intentionally small and strict.

Key rule:
- We validate invariants on *candidate* states BEFORE commit.
- We do not "solve", "evaluate", or "query for satisfaction".
- Checks are structural + scoped (academic boundary case: integer arithmetic forms).

Think of this as an invariant envelope:
it rejects obviously invalid drift (e.g., "2+2 -> 5") without turning the system
into a solver.

If you extend this into a general-purpose CAS, you are leaving Appendix A2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    reasons: Tuple[str, ...] = ()

    @staticmethod
    def pass_() -> "CheckResult":
        return CheckResult(True, ())

    @staticmethod
    def fail(*reasons: str) -> "CheckResult":
        return CheckResult(False, tuple(r for r in reasons if r))


# ----------------------------
# Payload structural checks
# ----------------------------

def _is_const(expr: Mapping[str, Any]) -> bool:
    return expr.get("kind") == "const" and isinstance(expr.get("value"), int)

def _is_add(expr: Mapping[str, Any]) -> bool:
    return expr.get("kind") == "add" and isinstance(expr.get("args"), list)

def _is_mul(expr: Mapping[str, Any]) -> bool:
    return expr.get("kind") == "mul" and isinstance(expr.get("args"), list)

def _args(expr: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    return list(expr.get("args", []))


def _walk(expr: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """
    Return a flat list of all nodes (preorder).
    """
    nodes: List[Mapping[str, Any]] = [expr]
    kind = expr.get("kind")
    if kind in ("add", "mul"):
        for a in _args(expr):
            nodes.extend(_walk(a))
    return nodes


def _is_well_formed(expr: Mapping[str, Any]) -> bool:
    """
    Minimal structural validity.
    """
    kind = expr.get("kind")
    if kind == "const":
        return isinstance(expr.get("value"), int)
    if kind in ("add", "mul"):
        args = expr.get("args")
        if not isinstance(args, list) or len(args) < 2:
            return False
        return all(isinstance(a, dict) and _is_well_formed(a) for a in args)
    return False


def _scope_allowed(scope: str) -> bool:
    """
    A2 scope guard. Keep it explicit.
    """
    return scope.startswith("A2:") and ("arithmetic" in scope)


# ----------------------------
# Invariants (academic boundary)
# ----------------------------

def check_candidate(candidate: Mapping[str, Any]) -> CheckResult:
    """
    Validate candidate state dict (no state_id yet).

    Candidate shape:
      {
        "scope": str,
        "payload": {...expr...},
        "meta": {"parent_id": "...", "transform_id": "...", ...}
      }
    """
    reasons: List[str] = []

    scope = candidate.get("scope", "")
    if not isinstance(scope, str) or not scope:
        reasons.append("missing_or_invalid_scope")
    elif not _scope_allowed(scope):
        reasons.append("scope_out_of_bounds")

    payload = candidate.get("payload")
    if not isinstance(payload, dict):
        reasons.append("missing_or_invalid_payload")
        return CheckResult.fail(*reasons)

    if not _is_well_formed(payload):
        reasons.append("payload_not_well_formed")

    meta = candidate.get("meta", {})
    if not isinstance(meta, dict):
        reasons.append("missing_or_invalid_meta")
    else:
        if not isinstance(meta.get("parent_id"), str) or not meta.get("parent_id"):
            reasons.append("missing_parent_id")
        if not isinstance(meta.get("transform_id"), str) or not meta.get("transform_id"):
            reasons.append("missing_transform_id")

    # A2-specific drift protection:
    # - No negative constants (keep domain tiny; this is a boundary case).
    # - No huge integers (avoid overflow discussions; boundary only).
    # - No "single-arg" add/mul (already in well_formed, but keep explicit).
    nodes = _walk(payload)
    for n in nodes:
        if _is_const(n):
            v = int(n["value"])
            if v < 0:
                reasons.append("negative_const_forbidden")
            if abs(v) > 10_000_000:
                reasons.append("const_out_of_range")

    # Forbidden-path hint (soft):
    # If someone adds an "eval" transform id, treat as fatal.
    # (We keep enforcement at policy level too, but this is a guardrail.)
    if isinstance(meta, dict):
        tid = meta.get("transform_id", "")
        if isinstance(tid, str) and ("eval" in tid or "solve" in tid):
            reasons.append("solver_like_transform_forbidden")

    return CheckResult.pass_() if not reasons else CheckResult.fail(*reasons)