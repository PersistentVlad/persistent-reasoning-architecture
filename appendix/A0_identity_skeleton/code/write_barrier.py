# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A0_identity_skeleton/code/write_barrier.py

"""
Appendix A0 — Identity Skeleton (code)

The write barrier is the single architectural choke point where persistent
structures may change.

Responsibilities:
- Enforce "Singular Write Authority": only this module can mutate the store.
- Validate *structural* invariants (not semantic correctness).
- Prevent forbidden operations from leaking into persistence (queries, solvers).
- Ensure append-only lineage and explicit revision semantics.

Important:
- This is NOT a rule engine.
- This is NOT a solver.
- Invariants here are placeholders for architectural constraints, not "logic".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .persistent_store import PersistentStore, MotifVersion, StoreInvariantViolation


class WriteAuthorityViolation(RuntimeError):
    """Raised when a caller tries to bypass write authority semantics."""


class RevisionRejected(RuntimeError):
    """Raised when a proposed revision fails structural validation."""


@dataclass(frozen=True)
class RevisionProposal:
    """
    A proposal to revise a motif.

    The proposal is intentionally minimal:
    - motif_id identifies the structure namespace
    - base_version_id is the version being revised
    - proposed_payload is the candidate structure (JSON-like)
    - rationale is optional and treated as metadata (projection), not logic
    """
    motif_id: str
    base_version_id: str
    proposed_payload: Dict
    rationale: str = ""


@dataclass(frozen=True)
class WriteBarrierResult:
    accepted: bool
    reason: str
    new_version: Optional[MotifVersion] = None


class WriteBarrier:
    """
    Enforces that persistence is a policy decision, not a placement detail.

    The barrier only checks structural invariants necessary to preserve identity.
    It does not check "truth", "satisfaction" or "optimality".
    """

    def __init__(self, store: PersistentStore) -> None:
        self._store = store

    # -----------------------------
    # Public API (the only write path)
    # -----------------------------

    def validate(self, proposal: RevisionProposal) -> WriteBarrierResult:
        """
        Validate a proposal WITHOUT committing it.

        This exists to preserve proposal/commit separation:
        inference can test whether a revision is even admissible,
        without gaining commit authority.
        """
        try:
            self._validate_structural_invariants(proposal)
        except RevisionRejected as e:
            return WriteBarrierResult(accepted=False, reason=str(e), new_version=None)

        return WriteBarrierResult(accepted=True, reason="ok", new_version=None)

    def commit(
        self,
        proposal: RevisionProposal,
        *,
        actor: str,
        commit_message: str,
    ) -> WriteBarrierResult:
        """
        Commit a proposal as a new motif version.

        NOTE:
        - This should be called by a Commit Gate (governance role),
          not directly by inference code.
        """
        # Validate first (must remain explicit).
        try:
            self._validate_structural_invariants(proposal)
        except RevisionRejected as e:
            return WriteBarrierResult(accepted=False, reason=str(e), new_version=None)

        # Append-only commit.
        meta = {
            "actor": actor,
            "commit_message": commit_message,
            "rationale": proposal.rationale,
            "base_version": proposal.base_version_id,
        }
        try:
            new_v = self._store.append_version(
                proposal.motif_id,
                proposal.proposed_payload,
                parent_version_id=proposal.base_version_id,
                meta=meta,
            )
        except StoreInvariantViolation as e:
            return WriteBarrierResult(accepted=False, reason=f"store_invariant_violation: {e}", new_version=None)

        return WriteBarrierResult(accepted=True, reason="committed", new_version=new_v)

    # -----------------------------
    # Structural invariants (minimal set)
    # -----------------------------

    def _validate_structural_invariants(self, proposal: RevisionProposal) -> None:
        """
        Validate ONLY what is required to preserve identity and prevent collapse.

        This is intentionally conservative and intentionally incomplete.
        """
        # Ensure proposal references latest base version (prototype keeps single linear lineage).
        latest = self._store.latest_version(proposal.motif_id)
        if proposal.base_version_id != latest.version_id:
            raise RevisionRejected(
                "base_version_id must be the latest version in this prototype "
                "(non-linear revisions are forbidden)."
            )

        # Ensure payload is JSON-like dict.
        if not isinstance(proposal.proposed_payload, dict):
            raise RevisionRejected("proposed_payload must be a JSON-like dict.")

        # Invariant: presence and type of required fields.
        self._require_fields(
            proposal.proposed_payload,
            required=[("tensions", list), ("relations", list), ("notes", str)],
        )

        # Invariant: tensions must be non-empty strings, uniqueness required.
        tensions = proposal.proposed_payload.get("tensions", [])
        if len(tensions) == 0:
            raise RevisionRejected("tensions must not be empty (a motif must preserve at least one tension).")

        normalized: List[str] = []
        for t in tensions:
            if not isinstance(t, str) or not t.strip():
                raise RevisionRejected("each tension must be a non-empty string.")
            normalized.append(t.strip())

        if len(set(normalized)) != len(normalized):
            raise RevisionRejected("tensions must be unique (duplicates collapse identity).")

        # Invariant: relations are purely structural edges and must not encode executable ops.
        # Allowed relation format: {"from": str, "to": str, "type": str}
        for rel in proposal.proposed_payload.get("relations", []):
            if not isinstance(rel, dict):
                raise RevisionRejected("each relation must be a dict.")
            self._require_fields(rel, required=[("from", str), ("to", str), ("type", str)])
            if not rel["from"].strip() or not rel["to"].strip() or not rel["type"].strip():
                raise RevisionRejected("relation fields must be non-empty strings.")

            # Forbidden: embedding query-like or solver-like keywords into structure "types".
            # This is a cheap guardrail to prevent readers from using relations as executable rules.
            forbidden_markers = ("query", "solve", "satisfy", "eval", "optimize", "reward", "loss")
            rel_type = rel["type"].lower()
            if any(m in rel_type for m in forbidden_markers):
                raise RevisionRejected(
                    "relation types must remain non-executable; "
                    "query/solve/eval/optimize markers are forbidden."
                )

        # Invariant: notes must remain a passive projection string.
        notes = proposal.proposed_payload.get("notes", "")
        if not isinstance(notes, str):
            raise RevisionRejected("notes must be a string.")

        # Invariant: forbid adding any field that looks like a query interface.
        forbidden_top_level = {"query", "search", "evaluate", "objective", "reward", "loss", "solver"}
        for k in proposal.proposed_payload.keys():
            if k.lower() in forbidden_top_level:
                raise RevisionRejected(f"top-level field '{k}' is forbidden (query/solver semantics collapse motifs).")

    @staticmethod
    def _require_fields(obj: Dict, *, required: List[Tuple[str, type]]) -> None:
        for name, typ in required:
            if name not in obj:
                raise RevisionRejected(f"missing required field: '{name}'")
            if not isinstance(obj[name], typ):
                raise RevisionRejected(f"field '{name}' must be of type {typ.__name__}")
