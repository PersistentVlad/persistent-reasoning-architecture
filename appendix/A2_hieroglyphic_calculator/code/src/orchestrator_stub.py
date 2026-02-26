# persistent-reasoning-architecture/appendix/A2_hieroglyphic_calculator/code/src/orchestrator_stub.py
"""
Orchestrator stub for Appendix A2 — Hieroglyphic Calculator.

Purpose:
- Demonstrate the *right* integration boundary:
  the calculator is NOT a solver and NOT an LLM prompt trick.
- The orchestrator coordinates:
  1) retrieve latest committed state
  2) propose a next transform (human / heuristic / LLM proposer)
  3) run invariant checker on the candidate
  4) commit through append-only lineage store (or reject)

This is a minimal educational skeleton.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, Tuple

from .checker import CheckResult, check_candidate
from .state import PRState
from .transforms import (
    CombineConstantsAdd,
    CombineConstantsMul,
    FlattenAssociative,
    NormalizeOrdering,
    Transform,
    apply_transform_to_candidate,
)


class LineageStore(Protocol):
    """
    Minimal store protocol expected by the orchestrator.

    A real implementation:
    - persists append-only
    - assigns state_id
    - never overwrites old states
    """
    def get(self, state_id: str) -> PRState:
        ...

    def head(self, namespace: str) -> PRState:
        ...

    def commit(self, namespace: str, candidate: Mapping[str, Any]) -> PRState:
        ...


class Proposer(Protocol):
    """
    Proposer role (LLM/human/heuristic). Has NO write authority.

    Must return a transform instance from the approved whitelist (by id),
    not arbitrary code.
    """
    def propose_next_transform(self, state: PRState) -> Transform:
        ...


@dataclass
class SimpleHeuristicProposer:
    """
    A tiny deterministic proposer for the demo.

    Priority:
    - flatten add/mul
    - normalize ordering
    - combine constants (add then mul)
    """
    def propose_next_transform(self, state: PRState) -> Transform:
        payload = state.payload
        kind = payload.get("kind")

        # Flatten first
        if kind == "add":
            return FlattenAssociative("add")
        if kind == "mul":
            return FlattenAssociative("mul")

        # Default normalization step
        return NormalizeOrdering()


class A2Orchestrator:
    """
    Orchestrator coordinating proposer -> checker -> commit.
    """
    def __init__(self, *, store: LineageStore, namespace: str, proposer: Proposer):
        self._store = store
        self._ns = namespace
        self._proposer = proposer

    def step(self) -> Tuple[bool, str, Optional[PRState]]:
        """
        Execute one controlled step.

        Returns:
          (committed?, message, new_state_if_committed)
        """
        head = self._store.head(self._ns)

        # 1) Propose
        transform = self._proposer.propose_next_transform(head)

        # 2) Apply transform to produce candidate (no state_id yet)
        candidate = apply_transform_to_candidate(
            transform=transform,
            scope=head.scope,
            payload=head.payload,
            parent_id=head.state_id,
        )

        # 3) Check invariants
        result: CheckResult = check_candidate(candidate)
        if not result.ok:
            msg = f"REJECT: invariants_failed: {', '.join(result.reasons)}"
            return False, msg, None

        # 4) Commit (append-only) via store
        new_state = self._store.commit(self._ns, candidate)
        msg = f"COMMIT: {new_state.state_id} via {candidate['meta']['transform_id']}"
        return True, msg, new_state

    def run(self, *, max_steps: int = 10) -> None:
        """
        Run several steps (demo mode).
        """
        for i in range(max_steps):
            committed, msg, _ = self.step()
            print(f"[step {i+1}] {msg}")
            if not committed:
                break


# Optional: a stricter proposer that tries combine-constants, showing different trajectories.
@dataclass
class CombineFirstProposer:
    """
    Deterministic proposer that attempts constant combination when applicable.
    """
    def propose_next_transform(self, state: PRState) -> Transform:
        kind = state.payload.get("kind")
        if kind == "add":
            return CombineConstantsAdd()
        if kind == "mul":
            return CombineConstantsMul()
        return NormalizeOrdering()