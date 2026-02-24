# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A0_identity_skeleton/code/commit_gate.py

"""
Appendix A0 — Identity Skeleton (code)

Commit Gate (Governance Role):
- Decides whether a validated proposal should become persistent.
- Uses the write barrier to enforce that all mutations are explicit.
- Can implement policy: rarity of commits, stability thresholds, human-in-the-loop.

Key distinction:
- The write barrier enforces *what is allowed*.
- The commit gate decides *what survives* (when to commit).

This prototype gate is intentionally simple and conservative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .persistent_store import PersistentStore, MotifVersion
from .write_barrier import WriteBarrier, RevisionProposal, WriteBarrierResult


@dataclass(frozen=True)
class CommitPolicy:
    """
    Minimal commit policy.

    commit_probability:
      even if valid, commits are not automatic; persistence must be earned.

    min_iterations_between_commits:
      helps prevent churn and "commit spam".
    """
    commit_probability: float = 0.25
    min_iterations_between_commits: int = 2


class CommitGate:
    """
    A minimal governance gate that:
    - calls barrier.validate()
    - then decides commit/reject based on policy
    - commits via barrier.commit() only if allowed

    This is where "deliberate revision" lives in the prototype.
    """

    def __init__(self, store: PersistentStore, barrier: WriteBarrier, *, policy: Optional[CommitPolicy] = None, seed: int = 11) -> None:
        self._store = store
        self._barrier = barrier
        self._policy = policy or CommitPolicy()
        self._seed = seed
        self._rng = __import__("random").Random(seed)
        self._last_commit_iter: dict[str, int] = {}  # motif_id -> iteration index

    def consider(
        self,
        *,
        motif_id: str,
        proposal_payload: dict,
        rationale: str,
        iteration: int,
        actor: str = "commit-gate",
    ) -> WriteBarrierResult:
        """
        Consider committing a proposed payload for motif_id at a given iteration.

        Returns a WriteBarrierResult:
        - accepted=False for rejected/invalid proposals
        - accepted=True with new_version if committed
        """
        latest = self._store.latest_version(motif_id)

        proposal = RevisionProposal(
            motif_id=motif_id,
            base_version_id=latest.version_id,
            proposed_payload=proposal_payload,
            rationale=rationale,
        )

        # 1) Validate through write barrier (structural admissibility)
        validation = self._barrier.validate(proposal)
        if not validation.accepted:
            return validation

        # 2) Decide whether to commit (policy)
        if not self._policy_allows_commit(motif_id=motif_id, iteration=iteration):
            return WriteBarrierResult(accepted=False, reason="rejected_by_policy", new_version=None)

        # 3) Commit through write barrier (only write path)
        res = self._barrier.commit(
            proposal,
            actor=actor,
            commit_message=f"Deliberate revision at iter={iteration}",
        )
        if res.accepted and res.new_version is not None:
            self._last_commit_iter[motif_id] = iteration
        return res

    # -----------------------------
    # Policy logic (intentionally minimal)
    # -----------------------------

    def _policy_allows_commit(self, *, motif_id: str, iteration: int) -> bool:
        last = self._last_commit_iter.get(motif_id, None)
        if last is not None:
            if (iteration - last) < self._policy.min_iterations_between_commits:
                return False

        # Require that committing is rare enough to preserve stability.
        return self._rng.random() < self._policy.commit_probability
