# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.
# persistent-reasoning-architecture/appendix/A0_identity_skeleton/code/proposal_engine.py

"""
Appendix A0 — Identity Skeleton (code)

Proposal Engine (Role):
- Generates candidate revisions to a persistent structure.
- Has NO commit authority.
- Must remain stateless with respect to persistence.
- May use heuristics, LLMs or human input in real systems,
  but in this prototype it is intentionally simple.

Important framing:
- Proposal Engine is a ROLE, not necessarily a standalone component.
- Here we implement it as a small class for clarity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List
import random

from .persistent_store import MotifVersion


@dataclass(frozen=True)
class ProposalContext:
    """
    Inputs available to the proposer.

    In the prototype we keep this intentionally small:
    - task_id: a label for the current episode (no semantics enforced)
    - observation: any text describing what happened in inference
    """
    task_id: str
    observation: str


@dataclass(frozen=True)
class CandidateProposal:
    """
    Candidate payload for revision.

    This is NOT a commit request.
    It is merely a candidate structure.
    """
    proposed_payload: Dict
    rationale: str


class ProposalEngine:
    """
    Minimal proposer used to demonstrate:
    inference -> proposal -> barrier -> (commit/reject)

    The proposer mutates NOTHING.
    It only returns candidate payloads.
    """

    def __init__(self, *, seed: int = 7) -> None:
        self._rng = random.Random(seed)

    def propose_revision(self, current: MotifVersion, ctx: ProposalContext) -> CandidateProposal:
        """
        Generate a candidate revision of the motif payload.

        This intentionally avoids "smartness":
        - sometimes propose no change
        - sometimes propose a small structural extension (add tension or relation)
        """
        payload = _deepcopy_json(current.payload)
        tensions: List[str] = list(payload.get("tensions", []))
        relations: List[Dict] = list(payload.get("relations", []))
        notes: str = str(payload.get("notes", ""))

        # Decide proposal type.
        roll = self._rng.random()

        # 35%: propose no change (tests that system can refuse to churn)
        if roll < 0.35:
            return CandidateProposal(
                proposed_payload=payload,
                rationale=f"No change proposed for task={ctx.task_id}: preserve current tensions.",
            )

        # 35%: propose adding a tension (simulates new decision pressure)
        if roll < 0.70:
            new_tension = self._suggest_tension(ctx)
            if new_tension and new_tension not in tensions:
                tensions.append(new_tension)
                payload["tensions"] = tensions
                payload["notes"] = _merge_notes(notes, f"[{ctx.task_id}] +tension: {new_tension}")
                return CandidateProposal(
                    proposed_payload=payload,
                    rationale=f"Observed new pressure; propose adding tension '{new_tension}'.",
                )
            # fallback: if tension duplicates, propose no change
            return CandidateProposal(
                proposed_payload=payload,
                rationale=f"Proposed tension already present; keep structure unchanged.",
            )

        # 30%: propose adding a relation (purely structural, non-executable)
        if tensions:
            a = self._rng.choice(tensions)
            b = self._rng.choice(tensions)
            if a != b:
                rel = {"from": a, "to": b, "type": "coexists-with"}
                relations.append(rel)
                payload["relations"] = relations
                payload["notes"] = _merge_notes(notes, f"[{ctx.task_id}] +relation: {a} -> {b} (coexists-with)")
                return CandidateProposal(
                    proposed_payload=payload,
                    rationale=f"Propose linking tensions to preserve topology under task={ctx.task_id}.",
                )

        return CandidateProposal(
            proposed_payload=payload,
            rationale="Fallback: no structural change.",
        )

    # -----------------------------
    # Internal helpers
    # -----------------------------

    def _suggest_tension(self, ctx: ProposalContext) -> Optional[str]:
        """
        Suggest a new tension label based on observation text.
        This is intentionally heuristic and shallow.

        In real systems, this could be:
        - LLM summarization into tensions
        - human proposal
        - extracted patterns from trajectories
        """
        obs = (ctx.observation or "").lower()

        candidates = []
        if "speed" in obs or "latency" in obs:
            candidates.append("speed ↔ stability")
        if "cost" in obs or "budget" in obs:
            candidates.append("cost ↔ thoroughness")
        if "risk" in obs or "safety" in obs:
            candidates.append("exploration ↔ safety")
        if "accuracy" in obs or "correct" in obs:
            candidates.append("accuracy ↔ continuity")
        if "user" in obs or "trust" in obs:
            candidates.append("helpfulness ↔ identity")

        if not candidates:
            # generic tension to keep prototype moving
            candidates = [
                "flexibility ↔ discipline",
                "local success ↔ long-term coherence",
                "adaptation ↔ preservation",
            ]

        return self._rng.choice(candidates)


def _merge_notes(existing: str, addition: str) -> str:
    existing = existing.strip()
    if not existing:
        return addition
    return existing + "\n" + addition


def _deepcopy_json(obj):
    import json
    return json.loads(json.dumps(obj, ensure_ascii=False))
