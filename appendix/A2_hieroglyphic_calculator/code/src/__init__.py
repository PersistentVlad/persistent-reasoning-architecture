# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/src/__init__.py

"""
Appendix A2 — Hieroglyphic Calculator (Academic Boundary Case)

This package is intentionally minimal.
It demonstrates an invariant-bound transformation envelope.

Key properties:
- Explicit invariants (checked before commit)
- Whitelisted transformations
- Append-only lineage (no in-place mutation)
- Deterministic behavior (no randomness, no learning)

This is NOT a solver, CAS, or reasoning engine.
"""

from .invariants import (
    InvariantViolation,
    InvariantResult,
    Invariant,
    InvariantRegistry,
    require_all_invariants,
    NoNaNNoInfInvariant,
    ScopeBoundInvariant,
    ProvenanceRequiredInvariant,
)

__all__ = [
    "InvariantViolation",
    "InvariantResult",
    "Invariant",
    "InvariantRegistry",
    "require_all_invariants",
    "NoNaNNoInfInvariant",
    "ScopeBoundInvariant",
    "ProvenanceRequiredInvariant",
]