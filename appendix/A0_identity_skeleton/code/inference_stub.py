# Copyright (c) 2026 Vladislav Bliznyukov
# Licensed under the MIT License.

"""
inference_stub.py

Inference (Execution Role) in the prototype.

This module represents "doing work" on tasks WITHOUT mutating persistence.

Key constraints:
- Inference reads the latest motif (structure) as context.
- Inference produces outputs (answers, decisions, actions) for the task.
- Inference may emit observations that the proposer can use.
- Inference has ZERO write access to persistence.

This is intentionally a stub:
- It does not solve real tasks.
- It exists to demonstrate separation: execution -> observations -> proposals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .persistent_store import MotifVersion


@dataclass(frozen=True)
class TaskInput:
    task_id: str
    prompt: str


@dataclass(frozen=True)
class InferenceOutput:
    task_id: str
    answer: str
    observations: str
    used_tensions: List[str]


class InferenceStub:
    """
    Minimal inference "engine" that consumes structure as a shaping context.

    It does NOT:
    - query the structure for satisfaction
    - evaluate constraints
    - compute optimality
    """

    def run(self, motif: MotifVersion, task: TaskInput) -> InferenceOutput:
        tensions = list(motif.payload.get("tensions", []))
        # Use the motif as an influence on posture (just a toy echo).
        used = tensions[: min(2, len(tensions))]

        # Produce an "answer" that is explicitly non-authoritative.
        answer = self._make_answer(task.prompt, used)

        # Produce observations that would plausibly trigger a proposal.
        observations = self._make_observations(task.prompt, used)

        return InferenceOutput(
            task_id=task.task_id,
            answer=answer,
            observations=observations,
            used_tensions=used,
        )

    # -----------------------------
    # Internal helpers
    # -----------------------------

    def _make_answer(self, prompt: str, used_tensions: List[str]) -> str:
        if not used_tensions:
            return f"[inference] Response to: {prompt}\n(no tensions applied)"
        return (
            f"[inference] Response to: {prompt}\n"
            f"(posture shaped by: {', '.join(used_tensions)})\n"
            f"Note: this is a stub, not a solver."
        )

    def _make_observations(self, prompt: str, used_tensions: List[str]) -> str:
        """
        Emit lightweight signals that can be used by the Proposal Engine.
        In real systems, these could come from logs, evaluations or user feedback.
        """
        text = prompt.lower()
        signals = []

        if "fast" in text or "latency" in text:
            signals.append("latency pressure observed")
        if "cheap" in text or "cost" in text or "budget" in text:
            signals.append("cost pressure observed")
        if "safe" in text or "risk" in text:
            signals.append("risk pressure observed")
        if "accurate" in text or "correct" in text:
            signals.append("accuracy pressure observed")
        if "user" in text or "trust" in text:
            signals.append("user trust pressure observed")

        if not signals:
            # default signal to keep the loop alive
            signals.append("generic trade-off pressure observed")

        if used_tensions:
            signals.append(f"current posture invoked: {', '.join(used_tensions)}")

        return "; ".join(signals)
