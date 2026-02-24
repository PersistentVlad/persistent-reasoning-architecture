# persistent-reasoning-architecture/appendix/A1_identity_formalization/code/__init__.py
"""
Appendix A1 — Identity Formalization & Merge Scenarios (code)

This package provides minimal, dependency-light scaffolding for:
- identity anchors (collision-resistant IDs),
- an append-only lineage model,
- merge scenario helpers (explicit parent preservation),
- collision detection hooks.

It is intentionally NOT a framework.
It exists to make the A1 boundary claims executable as small experiments.
"""

from .identity import IdentityAnchor, IdentityError, canonical_fingerprint
from .lineage_store import Commit, LineageStore, LineageError
from .merge_engine import MergeDecision, three_way_merge_analysis, commit_merge, detect_identity_collision
from .canonicalization import canonicalize_payload, CanonicalizationError

__all__ = [
    "IdentityAnchor",
    "IdentityError",
    "canonical_fingerprint",
    "Commit",
    "LineageStore",
    "LineageError",
    "MergeDecision",
    "three_way_merge_analysis",
    "commit_merge",
    "detect_identity_collision",
    "canonicalize_payload",
    "CanonicalizationError",
]
